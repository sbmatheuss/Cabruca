# Contrato de Endpoints — API CABRUCA

Este documento descreve o contrato de endpoints da API de backend, derivado das decisões registradas em:
- [ADR 0001](../adr/0001-classificacao-vs-deteccao.md) — resposta em lista de detecções (classe + caixa + confiança)
- [ADR 0002](../adr/0002-inferencia-on-device-vs-nuvem.md) — fluxo assíncrono (upload → fila → consulta de resultado)
- [ADR 0004](../adr/0004-armazenamento-de-imagens.md) — storage S3-compatível, metadados em Postgres
- [ADR 0005](../adr/0005-stack-de-backend.md) — FastAPI, fila via tabela no Postgres
- [ADR 0006](../adr/0006-estrategia-de-upload.md) — upload via pré-signed URL

Este é um documento de especificação, não uma ADR — não registra trade-offs de decisão, só o formato concreto derivado das ADRs acima. Ainda não implementado em código.

## `# REVISAR:` — autenticação/identidade

Nenhuma ADR até agora decidiu como a API identifica o usuário/dispositivo que faz a requisição. Todos os endpoints abaixo assumem implicitamente uma identidade de chamador (para saber de quem é a imagem, e restringir listagem/exclusão ao dono), mas o mecanismo (token, API key, conta de usuário, etc.) **não está definido**. Por acordo explícito, essa decisão fica para o momento em que a implementação em código dos endpoints começar — vai virar a ADR 0007 antes da primeira linha de código.

Até lá, os exemplos abaixo usam um campo genérico `owner_id` como placeholder, sem implicar qual vai ser o mecanismo real.

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

Cria o registro da imagem e retorna a URL pré-assinada para upload direto ao bucket (ADR 0006).

**Request body:**
```json
{
  "content_type": "image/jpeg"
}
```

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
- `404` — `image_id` não existe ou não pertence ao chamador.
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
- `404` — `image_id` não existe ou não pertence ao chamador.

### `GET /images` — listar imagens/detecções

Histórico paginado do chamador.

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
- `404` — `image_id` não existe ou não pertence ao chamador.

## Nota de gatilho futuro — push notification em vez de polling puro (sem decisão firme, registrado em 2026-07-14)

O `GET /images/{image_id}` acima assume que o cliente faz polling periódico até `status == "done"`. Em alto volume (ver nota equivalente na [ADR 0005](../adr/0005-stack-de-backend.md)), esse polling repetido vira carga de leitura relevante no Postgres.

Uma alternativa considerada foi **webhook** (o backend chamar de volta uma URL exposta pelo cliente) — descartada porque o cliente é um app de celular atrás de NAT de operadora, sem endereço público estável (a mesma premissa de conectividade rural instável que já motivou a ADR 0006); um webhook clássico não é implementável nesse cenário.

A alternativa que de fato serviria é **push notification** (Firebase Cloud Messaging / Apple Push Notification): o backend, ao concluir a inferência, dispara uma notificação push; o app, ao recebê-la, faz **uma única** chamada a `GET /images/{image_id}` para buscar o resultado. Isso não elimina o endpoint de consulta (continua necessário para quando o usuário abrir o app depois, ou se a notificação se perder) — reduz o volume de chamadas repetidas, não o substitui.

Isso **não é uma decisão tomada** — é uma nota de gatilho futuro, condicionada a evidência real de que o polling virou gargalo. Se/quando isso for decidido, vira uma ADR própria, cobrindo pelo menos: dependência de FCM/APNs, registro de token de push por dispositivo, e a política de fallback quando a notificação não chega.

## Fora de escopo deste documento

- Autenticação/identidade real (ver `# REVISAR:` acima — vira ADR 0007 antes da implementação).
- Schema exato das tabelas no Postgres.
- Consentimento/privacidade para uso de imagens em retrain (mencionado na ADR 0004, ainda não desenhado como fluxo de API).
- Endpoints administrativos (ex.: gestão de versão de modelo, retrain).
