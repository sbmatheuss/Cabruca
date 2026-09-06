# CABRUCA

Sistema de detecção de doenças e pragas em cacau (*Theobroma cacao*) a partir de imagens de campo — fotos tiradas por celular, geralmente por não especialistas, com iluminação/enquadramento variáveis e conectividade rural instável.

O produto faz **detecção de objetos** (bounding boxes, localizar e contar lesões), não classificação de imagem inteira — ver [ADR 0001](docs/adr/0001-classificacao-vs-deteccao.md).

## Estado atual do projeto

Estágio inicial: esqueleto do backend funcionando (upload de imagem via S3 presigned URL), mas ainda sem dataset anotado, sem treino de modelo e sem app mobile.

- **Backend**: FastAPI + SQLAlchemy 2.0 (async) + Alembic + Postgres. Contrato de endpoints (`docs/api/contrato-endpoints.md`) implementado por completo:
  - Imagens: `POST /images`, `POST /images/{id}/confirm`, `GET /images/{id}` (status/detecções), `GET /images` (lista paginada, com filtros), `DELETE /images/{id}` (remove registro e objeto no S3).
  - Propriedades: `POST /properties`, `POST /properties/join`, `GET /properties`, `GET /properties/{id}/members`, `POST /properties/{id}/transfer`, `DELETE /properties/{id}/members/{user_id}`.
- **Autenticação**: validação real de JWT do AWS Cognito (JWKS, `PyJWKClient`) — ver [ADR 0007](docs/adr/0007-autenticacao.md) e `backend/app/core/cognito_auth.py`. Lazy-create: a primeira request autenticada de um `sub` novo do Cognito já cria a linha em `users`.
- **Armazenamento de imagens**: S3 (AWS, dentro do free tier) via presigned URL — ver [ADR 0004](docs/adr/0004-armazenamento-de-imagens.md) e [ADR 0006](docs/adr/0006-estrategia-de-upload.md).
- **Dataset e anotações**: pipeline fechado — formato **COCO** e taxonomia de 3 classes (vassoura-de-bruxa, podridão-parda, monilíase) na [ADR 0011](docs/adr/0011-formato-anotacao-dataset.md), ferramenta de anotação **CVAT self-hosted** na [ADR 0012](docs/adr/0012-ferramenta-anotacao-dataset.md) (bootstrap automatizado em `infra/cvat/setup.ps1`), scripts de split treino/validação (`dataset/scripts/split_dataset.py`) e de validação de schema/bbox (`dataset/scripts/validate_dataset.py`) — ver [`dataset/README.md`](dataset/README.md). Só existem 5 imagens placeholder CC0 (`dataset/PLACEHOLDER_SOURCES.md`) para testar o pipeline; dataset real de campo ainda não coletado.
- **Versionamento de dataset/modelo**: DVC inicializado, remote S3 real e criado (`s3://cabruca-dvc-dev-klm`, sa-east-1) — ver [ADR 0003](docs/adr/0003-versionamento-de-modelo.md) e [ADR 0010](docs/adr/0010-implementacao-dvc.md). [`models/`](models/README.md) (pesos treinados) segue vazio, versionado via DVC quando houver um treino real.
- **Treino de modelo e inferência**: ainda sem modelo treinado. `models/training/` tem scaffolding de treino com Detectron2 ([ADR 0013](docs/adr/0013-framework-deteccao.md)); `services/inference-worker/` é um serviço separado (ADR 0005) com um runner real (`worker/main.py`) que faz poll da fila e transiciona imagens `QUEUED` → `PROCESSING` → `DONE`/`FAILED`, mas a inferência em si (`worker/inference.py`) ainda é um stub que sempre retorna lista vazia — nenhuma detecção é inventada.
- **Deploy de produção**: decidido e parcialmente executado — API em EC2 + Postgres em RDS, ambos free tier, região sa-east-1 ([ADR 0014](docs/adr/0014-deploy-producao-backend.md)); já existe `Dockerfile` da API (`backend/Dockerfile`), mas falta a automação de deploy (hoje seria manual via SSH).
- **Testes**: suíte pytest cobrindo todas as rotas do backend (`backend/tests/`), rodando contra Postgres real (com rollback por teste) e S3 simulado via `moto`; `services/inference-worker/tests/` tem teste de contrato de schema.
- **CI**: GitHub Actions (`.github/workflows/ci.yml`) roda lint (ruff), migrations e a suíte de testes a cada push/PR em `main`.
- **App mobile**: ainda não iniciado.

## Decisões arquiteturais

Toda decisão de arquitetura relevante vira um ADR em [`docs/adr/`](docs/adr/), seguindo o formato Contexto → Opções → Decisão → Consequências. Leitura recomendada antes de propor código novo, pois moldam o contrato de dados e de API desde a primeira linha.

## Backend — como rodar localmente

Pré-requisitos: Python 3.12+, [Poetry](https://python-poetry.org/), Docker.

```bash
cd backend
poetry install                       # instala dependências
docker compose up -d                 # sobe o Postgres de desenvolvimento
poetry run alembic upgrade head       # roda as migrations
poetry run uvicorn app.main:app --reload   # sobe a API
```

Rodar a suíte de testes:

```bash
poetry run pytest
```

Rodar o linter:

```bash
poetry run ruff check .
```

## Protocolo de trabalho

Este projeto é conduzido em modo colaborativo com o assistente de IA usado no desenvolvimento (não "faça tudo e entregue") — detalhes em [`CLAUDE.md`](CLAUDE.md).
