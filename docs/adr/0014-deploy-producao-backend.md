# ADR 0014 — Deploy de Produção do Backend (API + Postgres)

## Status
Aceito (2026-08-15)

## Contexto
O backend (`backend/`, [ADR 0005](0005-stack-de-backend.md)) roda hoje só localmente, via `docker compose up -d` para o Postgres de desenvolvimento. Não existe nenhum ambiente de produção provisionado.

A [ADR 0004](0004-armazenamento-de-imagens.md) já fixou uma filosofia de custo para o storage de imagens — **AWS enquanto couber no free tier, migrar para infraestrutura própria quando estourar** — e consolidou toda a infra AWS existente (bucket S3, User Pool do Cognito da [ADR 0007](0007-autenticacao.md), remote do DVC da [ADR 0010](0010-implementacao-dvc.md)) na região **sa-east-1**. O usuário decidiu (2026-08-15) aplicar a mesma filosofia ao deploy do backend, em vez de adotar um fornecedor novo (ex. Railway/Render) ou pular direto para self-hosted.

A [ADR 0005](0005-stack-de-backend.md) já decidiu que a API e o serviço de inferência do modelo são sistemas separados. Como ainda não existe modelo treinado (`models/` vazio — ver [ADR 0013](0013-framework-deteccao.md)), esta ADR cobre **só o deploy da API e do Postgres de metadados**; onde e como o serviço de inferência roda em produção fica para quando houver um modelo treinado de fato, para não especular sobre requisitos (memória, CPU vs. GPU) sem base real.

## Opções consideradas

### Onde a API roda
- **EC2, instância única, Docker** — mesma imagem/composição usada em dev (`backend/docker-compose.yml`), só trocando o Postgres local pelo RDS (ver abaixo). Cabe nas ~750h/mês de free tier de instâncias `t2.micro`/`t3.micro` (válidas nos primeiros 12 meses da conta) rodando uma única instância 24/7. Custo de manter: patch de SO e do runtime Docker ficam por nossa conta; sem auto-restart/health-check além do que o Docker Compose oferece (`restart: unless-stopped`) a menos que se adicione algo a mais.
- **ECS Fargate** — containers gerenciados, sem servidor para atualizar. Descartado para o MVP: ao contrário do EC2, não tem uma cota de uso sempre-grátis equivalente — o custo de vCPU/memória começa a contar desde a primeira execução, o que quebra a premissa "dentro do free tier" que motivou a escolha nesta ADR.
- **AWS App Runner** — deploy mais simples (aponta pra uma imagem e sobe), mas também sem free tier — cobrança por requisição/computação desde o primeiro dia, mesmo problema do Fargate.

### Onde o Postgres roda
- **RDS free tier, instância separada da API** — decisão do usuário (2026-08-15). RDS tem uma cota de free tier própria (instância `db.t3.micro`/`db.t4g.micro`, ~20 GB de storage, ~750h/mês, primeiros 12 meses), **separada** da cota de EC2 — rodar API em EC2 e banco em RDS ao mesmo tempo cabe nos dois free tiers simultaneamente, diferente de rodar duas instâncias EC2 (uma só para o banco), que estouraria as 750h/mês de EC2 (cota compartilhada entre todas as instâncias EC2 da conta). Ganha backup automático e patching gerenciados pela AWS — relevante porque o banco guarda dado de propriedade/geolocalização de agricultor real (mesma preocupação de LGPD já registrada na ADR 0004).
- **Postgres no mesmo EC2 da API, via Docker** — mesmo padrão do `docker-compose.yml` de dev, uma instância só. Mais simples de operar agora, mas sem backup automático (exigiria `pg_dump` manual/agendado) e acopla o failure domain do banco ao da API — se a instância cai, cai os dois juntos. Rejeitado porque o volume de dado sensível de agricultor pesa mais que a simplicidade operacional aqui.

## Decisão
- **API**: uma instância **EC2** (`t2.micro` ou `t3.micro`, o que estiver coberto pelo free tier no momento do provisionamento) na região **sa-east-1**, rodando a imagem da API via Docker — mesmo padrão de `backend/docker-compose.yml`, adaptado para apontar o `DATABASE_URL` para o RDS em vez de um Postgres local.
- **Postgres**: instância **RDS free tier** (`db.t3.micro`/`db.t4g.micro` conforme disponibilidade), também em **sa-east-1**, separada da instância EC2. Acesso de rede restrito ao security group da instância EC2 da API — sem exposição pública do banco.
- Gatilhos de migração para self-hosted (mesmo espírito da ADR 0004): uso se aproximando dos limites de horas/storage do free tier, ou a conta completando 12 meses. Quando isso acontecer, migrar para um servidor próprio (VPS) rodando o mesmo `docker-compose.yml` já usado em dev, com Postgres também em container — decisão de implementação a ser detalhada nesse momento, não agora.

## Consequências
- A imagem Docker da API passa a ser o artefato de deploy — precisa existir um `Dockerfile` em `backend/` (não existe ainda) antes do primeiro deploy real.
- `backend/.env`/configuração precisa diferenciar `DATABASE_URL` de dev (Postgres local) e produção (RDS) — hoje só há um `.env.example` pensado para dev.
- Cria uma segunda credencial/segredo AWS para gerenciar (endpoint e credenciais do RDS), além do que já existe para S3/Cognito/DVC.
- Não cobre ainda: automação de deploy (hoje `.github/workflows/ci.yml` só roda testes, não publica nem atualiza a instância EC2 — deploy seria manual via SSH até isso ser decidido), domínio e certificado TLS para a API (hoje só existe IP da instância), e onde/como o serviço de inferência do modelo roda quando houver modelo treinado.

## # REVISAR:
- Automação de deploy (CI/CD para publicar a imagem e atualizar a instância EC2) — deploy manual até virar uma decisão própria, quando o ritmo de mudanças justificar automatizar.
- Domínio e TLS para a API exposta publicamente — decisão de implementação pendente, precisa existir antes de ir ao ar com dado real de agricultor (LGPD).
- Deploy do serviço de inferência (ADR 0005) — fora de escopo aqui, decidir quando houver modelo treinado.
