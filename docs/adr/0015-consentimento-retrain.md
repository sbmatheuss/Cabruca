# ADR 0015 — Consentimento para Uso de Imagens em Retrain (LGPD)

## Status
Aceito (2026-09-06)

## Contexto
A [ADR 0004](0004-armazenamento-de-imagens.md) já sinalizava, na seção de Consequências, que o projeto "exige política de consentimento/privacidade para uso das imagens em retrain, considerando a LGPD (dados de propriedade/geolocalização de agricultores)" — mas nunca chegou a desenhar esse fluxo. O [contrato de endpoints](../api/contrato-endpoints.md) lista isso explicitamente em "Fora de escopo deste documento": "Consentimento/privacidade para uso de imagens em retrain (mencionado na ADR 0004, ainda não desenhado como fluxo de API)".

Ao investigar o código antes desta ADR, ficou confirmado que **hoje não existe nenhum pipeline automático ligando imagens de produção (tabela `images` / bucket S3) ao treino do modelo**: `models/training/dataset.py` lê arquivos COCO locais que alguém exporta manualmente do CVAT ([ADR 0012](0012-ferramenta-anotacao-dataset.md)) para `dataset/annotations/`, sem tocar o Postgres/S3 de produção; e o worker de inferência (`services/inference-worker/worker/inference.py`) tem um `infer()` que é um stub deliberado (sempre retorna lista vazia), sem sequer baixar bytes do S3 ainda. Isso significa que não existe, no código atual, um ponto único de execução automática onde aplicar uma regra de consentimento — a exportação para treino é um processo manual.

## Opções consideradas

### Granularidade do consentimento
- **Por propriedade** — o consentimento vale para todas as imagens de uma `Property`. Consistente com a ADR 0004, que já trata a sensibilidade (geolocalização/propriedade privada) no nível da propriedade, não da foto individual; reaproveita o padrão de permissão já usado em `transfer`/`members` (só `created_by` altera, qualquer técnico associado lê).
- **Por imagem** — mais granular, mas exigiria um campo por imagem e não reflete que a sensibilidade real é da terra, não da foto individual; também multiplicaria decisões de consentimento sem necessidade solicitada pelo usuário.
- **Por usuário (conta)** — um técnico consentiria uma vez para todas as imagens que envia, em qualquer propriedade; descartado porque mistura o consentimento de quem é dono/responsável pela terra com o do técnico que tira a foto, que podem ser pessoas diferentes.

### Comportamento padrão (novas propriedades e propriedades já existentes)
- **Opt-in (padrão `false`)** — nenhuma propriedade pode ter suas imagens usadas em retrain até que o criador consinta explicitamente. Mais conservador do ponto de vista de LGPD (não presume autorização para dado sensível de agricultor).
- **Opt-out (padrão `true`)** — descartado: presumir consentimento por padrão para dado de geolocalização/propriedade de terceiros é uma posição de LGPD mais frágil, sem justificar o ganho de volume de dados de treino.

### Escopo desta feature dado que não há pipeline automático de retrain
- **Só capturar/armazenar o consentimento** (schema + endpoint de leitura/escrita) — implementável agora, sem depender de um pipeline que ainda não existe.
- **Também construir um endpoint de exportação filtrado por consentimento**, pensado para substituir a exportação manual do CVAT — descartado por ora: amplia o escopo para um consumidor que ainda não está definido (a ADR 0012 não especifica esse fluxo), e antecipa uma automação sem evidência de necessidade real.

## Decisão

**Campo:** `retrain_consent: bool` (padrão `false`) na tabela `properties`, junto de `retrain_consent_updated_at` (timestamp, nulo até a primeira alteração explícita) e `retrain_consent_updated_by` (FK para `users.id`, nulo pelo mesmo motivo) — para permitir demonstrar quando e por quem o consentimento foi dado/revogado, que a LGPD trata como responsabilidade do controlador dos dados.

**Retroatividade:** a migration adiciona a coluna com `server_default=false`, então todas as propriedades já existentes ficam automaticamente em "sem consentimento" até confirmação explícita — não é necessário um passo de backfill separado.

**Autorização:** só `created_by` da propriedade pode alterar `retrain_consent` (mesmo padrão de `POST /properties/{id}/transfer`); qualquer técnico associado pode ler o valor (mesmo padrão de `GET /properties/{id}/members`).

**Endpoint:** `PATCH /properties/{property_id}/retrain-consent`, seguindo o padrão de rotas de ação específica já usado no contrato (`/join`, `/transfer`, `/members/{id}`) em vez de um PATCH genérico de propriedade, que não existe hoje. O campo `retrain_consent` também passa a ser retornado em `POST /properties` e `GET /properties`.

**Sem enforcement automático agora:** esta ADR registra como dívida técnica explícita que, enquanto a exportação para treino continuar manual (via CVAT), quem exportar precisa checar `retrain_consent` manualmente — não há, hoje, um ponto de código onde impor essa regra automaticamente. Se/quando um pipeline automático de retrain for construído, ele deve consultar este campo antes de incluir qualquer imagem no dataset de treino; isso é trabalho futuro, não coberto por esta ADR.

## Consequências
- O [contrato de endpoints](../api/contrato-endpoints.md) precisa do novo endpoint `PATCH /properties/{property_id}/retrain-consent` e do campo `retrain_consent` nas respostas de `POST /properties`/`GET /properties` — a linha correspondente em "Fora de escopo" deste documento deixa de se aplicar.
- Nova migration Alembic adicionando 3 colunas a `properties` (`retrain_consent`, `retrain_consent_updated_at`, `retrain_consent_updated_by`).
- Não há mudança em `images`, `detections`, no worker de inferência, nem no pipeline de treino — o campo fica disponível como metadado, mas nenhum consumidor automático o lê ainda.
- Revogar consentimento (`retrain_consent = false` depois de ter sido `true`) não afeta retroativamente um modelo já treinado com dados daquela propriedade — a ADR não cobre "direito ao esquecimento" sobre pesos de modelo já treinado, só sobre inclusão em treinos futuros.

## # REVISAR:
- Nenhum ponto pendente nesta ADR — decisões de granularidade, padrão, retroatividade, escopo e auditoria confirmadas explicitamente pelo usuário.
