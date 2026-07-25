# ADR 0010 — Implementação do DVC (bucket e ferramenta de instalação)

## Status
Aceito (2026-07-24)

## Contexto
A [ADR 0003](0003-versionamento-de-modelo.md) decidiu adotar DVC, com o remote apontando "para o mesmo storage de imagens definido na ADR 0004 (...) ou infraestrutura própria", deixando explícito que "o storage de artefatos de modelo pode ser o mesmo bucket de imagens (...) ou um bucket dedicado — decisão de implementação, não arquitetural". Esta ADR resolve esse ponto de implementação e registra como o CLI do DVC foi instalado, já que ainda não existe nenhum projeto Python na raiz do repositório (só `backend/`, gerenciado via Poetry).

## Opções consideradas

### Bucket do remote S3
- **Mesmo bucket de imagens** (`cabruca-images-dev`), com prefixo separado (ex. `dvc-store/`) — reaproveita o bucket já usado pelo backend (ADR 0004), sem criar recurso AWS novo, mas mistura no mesmo bucket dados de duas naturezas diferentes (imagens de produção enviadas por agricultores vs. dataset/modelo versionado para treino), com lifecycle policies e necessidades de acesso potencialmente distintas.
- **Bucket dedicado** (`cabruca-dvc-dev`) — isola dataset/modelo do bucket de imagens de produção, permitindo lifecycle policy e política de acesso próprias. Custo: mais um recurso AWS a monitorar dentro do limite de 5 GB do free tier (ADR 0004).

### Ferramenta de instalação do DVC
- **pipx global** — instala o CLI do DVC isolado do sistema, sem amarrar a nenhum projeto Python específico. Faz sentido porque ainda não existe um projeto de treino/ML no repositório para o DVC ser dependência dele.
- **Novo projeto Poetry na raiz** (ex. `training/`) — mais estruturado, mas seria overhead antes de existir qualquer script de treino real para acompanhar o DVC.
- **pip install global sem isolamento** — mais simples, mas polui o Python do sistema/ambiente ativo.

## Decisão
Bucket **dedicado** (`cabruca-dvc-dev`) para o remote do DVC, separado do bucket de imagens de produção.

Instalação do CLI via **pipx** (`pipx install "dvc[s3]"`), sem criar projeto Python na raiz — decisão revisitável quando existir de fato um pipeline de treino com dependências Python próprias.

## Consequências
- `.dvc/config` aponta para `s3://cabruca-dvc-dev` — bucket que **ainda não existe** na AWS no momento desta ADR (placeholder combinado com o usuário). `dvc push` só funcionará depois que o bucket for criado.
- Mais um bucket a monitorar contra os limites do free tier da AWS (ADR 0004), além do bucket de imagens.
- Quando um pipeline de treino real for criado, reavaliar se o DVC deve migrar para ser dependência declarada desse projeto (Poetry) em vez de instalação via pipx.

## # REVISAR:
Confirmar a criação efetiva do bucket `cabruca-dvc-dev` na AWS antes de rodar `dvc push` pela primeira vez — enquanto isso, o remote configurado é um placeholder (ver comentário em `.dvc/config`).
