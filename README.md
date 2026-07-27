# CABRUCA

Sistema de detecção de doenças e pragas em cacau (*Theobroma cacao*) a partir de imagens de campo — fotos tiradas por celular, geralmente por não especialistas, com iluminação/enquadramento variáveis e conectividade rural instável.

O produto faz **detecção de objetos** (bounding boxes, localizar e contar lesões), não classificação de imagem inteira — ver [ADR 0001](docs/adr/0001-classificacao-vs-deteccao.md).

## Estado atual do projeto

Estágio inicial: esqueleto do backend funcionando (upload de imagem via S3 presigned URL), mas ainda sem dataset anotado, sem treino de modelo e sem app mobile.

- **Backend**: FastAPI + SQLAlchemy 2.0 (async) + Alembic + Postgres. Contrato de endpoints (`docs/api/contrato-endpoints.md`) implementado por completo:
  - Imagens: `POST /images`, `POST /images/{id}/confirm`, `GET /images/{id}` (status/detecções), `GET /images` (lista paginada, com filtros), `DELETE /images/{id}` (remove registro e objeto no S3).
  - Propriedades: `POST /properties`, `POST /properties/join`, `GET /properties`, `GET /properties/{id}/members`, `POST /properties/{id}/transfer`, `DELETE /properties/{id}/members/{user_id}`.
- **Autenticação**: stub de desenvolvimento (usuário fixo) enquanto o AWS Cognito não é criado — ver [ADR 0007](docs/adr/0007-autenticacao.md) e `backend/app/core/dev_auth.py`. Pendência conhecida: nada ainda provisiona a linha em `users` para um técnico novo autenticando pela primeira vez.
- **Armazenamento de imagens**: S3 (AWS, dentro do free tier) via presigned URL — ver [ADR 0004](docs/adr/0004-armazenamento-de-imagens.md) e [ADR 0006](docs/adr/0006-estrategia-de-upload.md).
- **Dataset e anotações**: ainda sem imagens/anotações reais, mas pipeline fechado — formato **COCO** e taxonomia de 3 classes (vassoura-de-bruxa, podridão-parda, monilíase) na [ADR 0011](docs/adr/0011-formato-anotacao-dataset.md), ferramenta de anotação **CVAT self-hosted** na [ADR 0012](docs/adr/0012-ferramenta-anotacao-dataset.md), e script de validação (`dataset/scripts/validate_dataset.py`) que confere anotações contra essa taxonomia — ver [`dataset/README.md`](dataset/README.md).
- **Versionamento de dataset/modelo**: DVC inicializado, remote S3 configurado (bucket dedicado `cabruca-dvc-dev` ainda por criar manualmente na AWS). Estrutura de pastas pronta para receber dados reais — [`dataset/`](dataset/README.md) (imagens + anotações) e [`models/`](models/README.md) (pesos treinados) — ambas vazias hoje, versionadas via DVC (não Git) quando houver conteúdo. Ver [ADR 0003](docs/adr/0003-versionamento-de-modelo.md) e [ADR 0010](docs/adr/0010-implementacao-dvc.md).
- **Testes**: suíte pytest cobrindo todas as rotas acima (`backend/tests/`), rodando contra Postgres real (com rollback por teste) e S3 simulado via `moto`.
- **CI**: GitHub Actions (`.github/workflows/ci.yml`) roda lint (ruff), migrations e a suíte de testes a cada push/PR em `main`.
- **Treino de modelo e app mobile**: ainda não iniciados.

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
