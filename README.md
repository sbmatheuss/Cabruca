# CABRUCA

Sistema de detecção de doenças e pragas em cacau (*Theobroma cacao*) a partir de imagens de campo — fotos tiradas por celular, geralmente por não especialistas, com iluminação/enquadramento variáveis e conectividade rural instável.

O produto faz **detecção de objetos** (bounding boxes, localizar e contar lesões), não classificação de imagem inteira — ver [ADR 0001](docs/adr/0001-classificacao-vs-deteccao.md).

## Estado atual do projeto

Estágio inicial: esqueleto do backend funcionando (upload de imagem via S3 presigned URL), mas ainda sem dataset anotado, sem treino de modelo e sem app mobile.

- **Backend**: FastAPI + SQLAlchemy 2.0 (async) + Alembic + Postgres. Duas rotas implementadas: `POST /images` (solicita upload) e `POST /images/{id}/confirm` (confirma upload). O restante do contrato (`docs/api/contrato-endpoints.md`) — CRUD de propriedades, consulta de resultado, listagem, exclusão — ainda não existe.
- **Autenticação**: stub de desenvolvimento (usuário fixo) enquanto o AWS Cognito não é criado — ver [ADR 0007](docs/adr/0007-autenticacao.md) e `backend/app/core/dev_auth.py`.
- **Armazenamento de imagens**: S3 (AWS, dentro do free tier) via presigned URL — ver [ADR 0004](docs/adr/0004-armazenamento-de-imagens.md) e [ADR 0006](docs/adr/0006-estrategia-de-upload.md).
- **Versionamento de dataset/modelo**: DVC inicializado, remote S3 configurado (bucket dedicado ainda por criar manualmente) — ver [ADR 0003](docs/adr/0003-versionamento-de-modelo.md) e [ADR 0010](docs/adr/0010-implementacao-dvc.md).
- **Testes**: suíte pytest cobrindo as duas rotas existentes (`backend/tests/`), rodando contra Postgres real (com rollback por teste) e S3 simulado via `moto`.
- **CI**: GitHub Actions (`.github/workflows/ci.yml`) roda lint (ruff), migrations e a suíte de testes a cada push/PR em `main`.
- **Dataset, treino de modelo e app mobile**: ainda não iniciados.

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
