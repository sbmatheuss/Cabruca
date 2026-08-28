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
- Exports do CVAT em COCO JSON devem ser conferidos contra o schema e a lista de `categories` definidos na ADR 0011 antes de entrar em `dataset/annotations/`.
- Nenhuma imagem real existe ainda — a infra de anotação (bloco abaixo) fica pronta antes dos dados, para não haver atrito quando as fotos de campo chegarem.

## Decisão (infraestrutura de implantação, fechada em 2026-08-27)
- **Onde roda**: máquina de desenvolvimento local, via Docker — não há demanda ou orçamento hoje para servidor dedicado. Reavaliar se/quando anotação precisar ser feita por mais de uma pessoa ao mesmo tempo.
- **Onde fica o Docker Compose do CVAT**: em nenhum lugar deste repositório. A config do CVAT em si (`docker-compose.yml` do projeto CVAT) não é vendorizada aqui — mesma razão já registrada acima (evitar manter cópia de terceiro desatualizada). O que entra no repo é só um script fino de bootstrap em `infra/cvat/`, que automatiza os comandos já documentados em `dataset/README.md` (clone da tag fixada, `docker compose up`, instrução de `createsuperuser`) sem copiar a config do CVAT.

## # REVISAR:
Nenhum ponto pendente — as duas decisões de infraestrutura acima foram fechadas com o usuário.
