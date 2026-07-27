# ADR 0012 — Ferramenta de Anotação do Dataset (CVAT self-hosted)

## Status
Aceito (2026-07-26)

## Contexto
A [ADR 0011](0011-formato-anotacao-dataset.md) fechou o formato de anotação (COCO) e a taxonomia de classes do MVP (vassoura-de-bruxa, podridão-parda, monilíase), mas não a ferramenta usada para de fato desenhar as bounding boxes nas fotos de campo — decisão de implementação, não coberta por nenhuma ADR anterior.

## Opções consideradas
- **CVAT self-hosted** — open-source, feito especificamente para anotação de visão computacional (não genérico). Export COCO JSON nativo, além de YOLO e Pascal VOC. Roda de graça via Docker Compose, mesmo padrão já usado em `backend/docker-compose.yml` para o Postgres de desenvolvimento. As fotos de campo (potencialmente com geolocalização) ficam na conta/infra que o próprio projeto gerencia — sem depender do silo de dados de um SaaS de terceiro.
- **Label Studio self-hosted** — também open-source, gratuito e self-hosted, exporta COCO. Ferramenta genérica (cobre texto, áudio, além de imagem), com superfície de recursos maior do que o necessário para este projeto.
- **Roboflow (cloud)** — onboarding mais rápido e pipeline integrado (anotação + versionamento + augmentação + treino), mas é SaaS de terceiros com custo por uso; as fotos de campo passariam a existir também na infra do fornecedor (além do bucket S3/MinIO da [ADR 0004](0004-armazenamento-de-imagens.md)), e o versionamento de dataset embutido no Roboflow duplicaria o que o DVC (ADR 0003/0010) já resolve.

## Decisão
Adotar **CVAT self-hosted**, rodando via Docker Compose — decisão do usuário (2026-07-26).

## Consequências
- Quando houver fotos reais para anotar, será necessário um Docker Compose próprio para subir o CVAT (serviço separado do `backend/docker-compose.yml`, que sobe apenas o Postgres de desenvolvimento do backend).
- Exports do CVAT em COCO JSON devem ser conferidos contra o schema e a lista de `categories` definidos na ADR 0011 antes de entrar em `dataset/annotations/`.
- Nenhuma imagem real existe ainda — esta ADR registra a escolha da ferramenta; a instalação/configuração de fato só é necessária quando houver fotos de campo prontas para rotular.

## # REVISAR:
- Onde o CVAT vai rodar de fato (mesma máquina de desenvolvimento, servidor próprio, etc.) — decisão de infraestrutura de implantação ainda em aberto, fora do escopo desta ADR.
- Local do Docker Compose do CVAT no repositório (ex. pasta própria fora de `backend/`, já que não é parte do serviço de API) — decidir quando a instalação for de fato feita.
