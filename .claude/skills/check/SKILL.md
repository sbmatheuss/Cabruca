---
name: check
description: Mostra o checklist de progresso do projeto CABRUCA (áreas ponderadas + % de conclusão geral). Use quando o usuário pedir "/check", "status do projeto", "quanto falta", "checklist de progresso".
---

# /check

Recalcula e exibe o checklist de progresso do projeto CABRUCA. Não é uma leitura estática: a cada invocação, reverifique o estado real do repositório (não confie em memória de conversas anteriores) antes de preencher a tabela.

## Áreas e pesos (fixos, decididos com o usuário em 2026-07-19 — não alterar sem confirmação)

| Área | Peso | Como verificar % concluído |
|---|---|---|
| API — contrato de endpoints | 15% | Rotas em `backend/app/api/routes/` além de `/health`; cobrem upload, consulta de resultado, CRUD de properties/images, conforme ADRs 0002 e 0006 |
| Dataset e anotações (COCO/YOLO) | 15% | Existência de imagens anotadas versionadas (DVC) ou pasta de dataset no repo |
| Modelo de detecção (treino/avaliação) | 15% | Scripts/notebooks de treino, pesos de modelo versionados, métricas de avaliação |
| App mobile | 13% | Existência de projeto mobile (pasta `app/`, `mobile/` ou similar) |
| Backend — esqueleto | 8% | `backend/app/main.py`, models em `backend/app/models/`, migrations em `backend/migrations/versions/`, Docker Compose |
| Decisões arquiteturais (ADRs) | 8% | Quantidade de ADRs em `docs/adr/` cobrindo: detecção, inferência, versionamento, storage, stack backend, upload, auth, modelo de dados, bbox — vs. decisões ainda faltantes (framework de detecção, stack mobile, CI/CD, deploy/produção) |
| Autenticação (Cognito + JWT) | 8% | Middleware/dependency de validação de JWT implementado em `backend/app/` |
| Armazenamento de imagens (S3 presigned URL) | 8% | Código de geração de presigned URL / integração S3 no backend |
| Versionamento (DVC) | 5% | Arquivo `.dvc`, `dvc.yaml` ou config de remote DVC no repo |
| Testes automatizados | 3% | Arquivos `test_*.py` ou pasta `tests/` em `backend/` |
| CI/CD | 2% | Workflows em `.github/workflows/` ou config de CI equivalente |

## Passos ao executar

1. Rode buscas rápidas no repo (Glob/Grep/Bash) para checar cada linha da tabela acima — não assuma o estado da última vez.
2. Preencha `% concluído` de cada área com base no que existe de fato agora.
3. Calcule contribuição = peso × % concluído, some tudo para o total geral ponderado.
4. Mostre a tabela completa + total geral em uma frase.
5. Se uma área nova relevante tiver surgido (ex. pasta de mobile criada, testes adicionados) e não estiver na tabela, avise o usuário e pergunte se quer adicionar uma linha — não adicione silenciosamente.
