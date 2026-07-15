# Contrato de Endpoints — API CABRUCA

Este documento descreve o contrato de endpoints da API de backend, derivado das decisões registradas em:
- [ADR 0001](../adr/0001-classificacao-vs-deteccao.md) — resposta em lista de detecções (classe + caixa + confiança)
- [ADR 0002](../adr/0002-inferencia-on-device-vs-nuvem.md) — fluxo assíncrono (upload → fila → consulta de resultado)
- [ADR 0004](../adr/0004-armazenamento-de-imagens.md) — storage S3-compatível, metadados em Postgres
- [ADR 0005](../adr/0005-stack-de-backend.md) — FastAPI, fila via tabela no Postgres
- [ADR 0006](../adr/0006-estrategia-de-upload.md) — upload via pré-signed URL
- [ADR 0007](../adr/0007-autenticacao.md) — autenticação via AWS Cognito (email + senha), identidade do chamador vem do JWT
- [ADR 0008](../adr/0008-modelo-usuario-propriedade-imagem.md) — modelo usuário↔propriedade (N:N) ↔ imagem; acesso a propriedade existente via código

Este é um documento de especificação, não uma ADR — não registra trade-offs de decisão, só o formato concreto derivado das ADRs acima. Ainda não implementado em código.

## Autenticação

Todas as rotas abaixo exigem o header `Authorization: Bearer <JWT>`, com um token emitido pelo AWS Cognito ([ADR 0007](../adr/0007-autenticacao.md)). A API valida a assinatura e a expiração do token e extrai o identificador do usuário do claim `sub` — esse valor substitui o placeholder `owner_id` usado numa versão anterior deste documento, antes da ADR 0007 ser decidida.

**Erro comum a todas as rotas:** `401` — token ausente, inválido ou expirado.

O ponto deixado em aberto na ADR 0007 (modelo de associação usuário↔propriedade↔imagem) foi resolvido na [ADR 0008](../adr/0008-modelo-usuario-propriedade-imagem.md): uma imagem pertence a uma **propriedade**, e o acesso do usuário autenticado depende de ele estar associado a essa propriedade — não de ter enviado a imagem diretamente. Os endpoints de propriedade e a regra de autorização atualizada estão na seção seguinte.

## Autorização por propriedade

Um usuário só acessa (lê ou apaga) uma imagem se estiver associado à propriedade dela (tabela `user_properties` da ADR 0008). Isso vale para `GET`/`DELETE /images/{image_id}` abaixo — o erro `404` nesses endpoints cobre tanto "não existe" quanto "existe, mas o usuário não está associado à propriedade", para não vazar a existência de uma propriedade/imagem para quem não tem acesso.

### `POST /properties` — criar propriedade

Cria a propriedade, associa automaticamente o usuário autenticado como criador, e gera o `property_code` para compartilhar com outros técnicos.

**Request body:**
```json
{
  "name": "Fazenda Boa Esperança",
  "location": { "lat": -14.235, "lng": -39.021 }
}
```

**Response `201 Created`:**
```json
{
  "property_id": "uuid",
  "name": "Fazenda Boa Esperança",
  "property_code": "AB12CD34",
  "created_at": "2026-07-14T18:00:00Z"
}
```

### `POST /properties/join` — entrar em propriedade existente via código

Associa o usuário autenticado a uma propriedade já existente, usando o `property_code` (ADR 0008).

**Request body:**
```json
{
  "property_code": "AB12CD34"
}
```

**Response `200 OK`:**
```json
{
  "property_id": "uuid",
  "name": "Fazenda Boa Esperança"
}
```

**Erros:**
- `404` — código não corresponde a nenhuma propriedade.

### `GET /properties` — listar propriedades acessíveis

Lista as propriedades às quais o usuário autenticado está associado.

**Response `200 OK`:**
```json
{
  "items": [
    { "property_id": "uuid", "name": "Fazenda Boa Esperança", "is_creator": true }
  ]
}
```

`is_creator` indica se o usuário autenticado é quem criou a propriedade — usado pelo cliente para decidir se mostra a opção de revogar acesso de outros técnicos.

### `GET /properties/{property_id}/members` — listar técnicos associados

Necessário para o criador decidir quem revogar. Acessível a qualquer técnico associado à propriedade (mesma regra de "Autorização por propriedade" acima).

**Response `200 OK`:**
```json
{
  "items": [
    { "user_id": "uuid", "is_creator": true, "associated_at": "2026-07-10T09:00:00Z" },
    { "user_id": "uuid", "is_creator": false, "associated_at": "2026-07-12T14:00:00Z" }
  ]
}
```

### `POST /properties/{property_id}/transfer` — transferir posse da propriedade

Só o criador atual pode chamar. Transfere `created_by` para outro técnico já associado à propriedade (ADR 0008) — necessário antes do criador sair, se houver outros membros.

**Request body:**
```json
{
  "new_owner_user_id": "uuid"
}
```

**Response `200 OK`:**
```json
{
  "property_id": "uuid",
  "created_by": "uuid"
}
```

**Erros:**
- `403` — usuário autenticado não é o criador atual da propriedade.
- `404` — propriedade não existe, ou `new_owner_user_id` não está associado a ela.

### `DELETE /properties/{property_id}/members/{user_id}` — revogar acesso / sair da propriedade

Remove a associação entre `user_id` e a propriedade (ADR 0008). Regras de permissão:
- Qualquer técnico associado pode remover a **própria** associação (`user_id` = usuário autenticado) — sair da propriedade.
- Só o criador da propriedade (`created_by`) pode remover a associação de **outro** técnico.
- **Exceção**: o criador não pode remover a própria associação enquanto existirem outros técnicos associados — precisa usar `POST /properties/{property_id}/transfer` primeiro. Se o criador for o único associado, pode sair normalmente.

**Response `204 No Content`**

**Erros:**
- `403` — usuário autenticado não é nem o criador da propriedade, nem o próprio `user_id` sendo removido.
- `404` — propriedade não existe, ou `user_id` não está associado a ela.
- `409` — o criador está tentando sair (`user_id` = criador) e ainda existem outros técnicos associados; transferir a posse primeiro.

## Ciclo de status de uma imagem

```
pending_upload → queued → processing → done
                                       ↘ failed
```

- `pending_upload`: registro criado, URL pré-assinada emitida, upload ainda não confirmado.
- `queued`: upload confirmado, na fila de detecção (ADR 0005).
- `processing`: worker de inferência pegou o item da fila.
- `done`: detecção concluída, lista de detecções disponível.
- `failed`: falha na inferência (ex.: imagem corrompida, erro do modelo).

## Endpoints

### `POST /images` — solicitar upload

Cria o registro da imagem e retorna a URL pré-assinada para upload direto ao bucket (ADR 0006). A imagem pertence à propriedade informada (ADR 0008) — o usuário precisa estar associado a essa propriedade.

**Request body:**
```json
{
  "property_id": "uuid",
  "content_type": "image/jpeg"
}
```

**Erros:**
- `403` — usuário não está associado à propriedade informada.
- `404` — `property_id` não existe.

**Response `201 Created`:**
```json
{
  "image_id": "uuid",
  "upload_url": "https://...",
  "expires_at": "2026-07-14T18:30:00Z",
  "status": "pending_upload"
}
```

### `POST /images/{image_id}/confirm` — confirmar upload

Cliente avisa que terminou o upload direto ao bucket. A API verifica a existência do objeto no S3 e muda o status para `queued`.

**Response `200 OK`:**
```json
{
  "image_id": "uuid",
  "status": "queued"
}
```

**Erros:**
- `404` — `image_id` não existe, ou o usuário não está associado à propriedade da imagem (ver "Autorização por propriedade" acima).
- `409` — objeto não encontrado no bucket (upload não aconteceu de fato).
- `410` — URL pré-assinada expirou antes da confirmação.

### `GET /images/{image_id}` — consultar status/resultado

Consulta assíncrona de status (ADR 0002). Enquanto `status != "done"`, o campo `detections` vem vazio/ausente.

**Response `200 OK` (em processamento):**
```json
{
  "image_id": "uuid",
  "status": "processing",
  "created_at": "2026-07-14T18:00:00Z"
}
```

**Response `200 OK` (concluído):**
```json
{
  "image_id": "uuid",
  "status": "done",
  "created_at": "2026-07-14T18:00:00Z",
  "completed_at": "2026-07-14T18:02:15Z",
  "model_version": "v0.1.0",
  "detections": [
    {
      "class": "monilíase",
      "bbox": [x, y, largura, altura],
      "confidence": 0.87
    }
  ]
}
```

**Erros:**
- `404` — `image_id` não existe, ou o usuário não está associado à propriedade da imagem (ver "Autorização por propriedade" acima).

### `GET /images` — listar imagens/detecções

Histórico paginado das imagens de todas as propriedades às quais o usuário autenticado está associado.

**Query params:** `status` (filtro opcional), `since`/`until` (filtro de data opcional), `page`, `page_size`.

**Response `200 OK`:**
```json
{
  "items": [
    { "image_id": "uuid", "status": "done", "created_at": "..." }
  ],
  "page": 1,
  "page_size": 20,
  "total": 134
}
```

### `DELETE /images/{image_id}` — excluir imagem

Exclusão da imagem e seus metadados/detecções associadas — motivada pela obrigação de direito de exclusão sob a LGPD, já sinalizada na ADR 0004 (dados de geolocalização/propriedade de agricultores).

**Response `204 No Content`**

**Erros:**
- `404` — `image_id` não existe, ou o usuário não está associado à propriedade da imagem (ver "Autorização por propriedade" acima).

## Nota de gatilho futuro — push notification em vez de polling puro (sem decisão firme, registrado em 2026-07-14)

O `GET /images/{image_id}` acima assume que o cliente faz polling periódico até `status == "done"`. Em alto volume (ver nota equivalente na [ADR 0005](../adr/0005-stack-de-backend.md)), esse polling repetido vira carga de leitura relevante no Postgres.

Uma alternativa considerada foi **webhook** (o backend chamar de volta uma URL exposta pelo cliente) — descartada porque o cliente é um app de celular atrás de NAT de operadora, sem endereço público estável (a mesma premissa de conectividade rural instável que já motivou a ADR 0006); um webhook clássico não é implementável nesse cenário.

A alternativa que de fato serviria é **push notification** (Firebase Cloud Messaging / Apple Push Notification): o backend, ao concluir a inferência, dispara uma notificação push; o app, ao recebê-la, faz **uma única** chamada a `GET /images/{image_id}` para buscar o resultado. Isso não elimina o endpoint de consulta (continua necessário para quando o usuário abrir o app depois, ou se a notificação se perder) — reduz o volume de chamadas repetidas, não o substitui.

Isso **não é uma decisão tomada** — é uma nota de gatilho futuro, condicionada a evidência real de que o polling virou gargalo. Se/quando isso for decidido, vira uma ADR própria, cobrindo pelo menos: dependência de FCM/APNs, registro de token de push por dispositivo, e a política de fallback quando a notificação não chega.

## Fora de escopo deste documento

- Detalhes de configuração do Cognito (política de senha, expiração/refresh de token) — ver ADR 0007.
- Schema exato das tabelas no Postgres.
- Consentimento/privacidade para uso de imagens em retrain (mencionado na ADR 0004, ainda não desenhado como fluxo de API).
- Endpoints administrativos (ex.: gestão de versão de modelo, retrain).
