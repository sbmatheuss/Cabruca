# ADR 0004 — Armazenamento de Imagens

## Status
Aceito (2026-07-13), com gatilho de revisão explícito

## Contexto
As imagens são de agricultores/propriedades, potencialmente sensíveis (localização, propriedade privada), e precisam alimentar retrain de modelo e auditoria. A [ADR 0002](0002-inferencia-on-device-vs-nuvem.md) define upload assíncrono via fila local, então o storage precisa suportar chegada em lote quando o usuário reconecta.

## Opções consideradas

- **Object storage compatível com S3** (AWS S3, Cloudflare R2, MinIO self-hosted) — desenhado para arquivos binários em volume, custo baixo por GB, lifecycle policies, integra bem com pipelines de ML (DVC, treino) que já esperam API estilo S3.
- **Banco de dados com blobs** — simples para prototipagem, mas bancos relacionais não são otimizados para blobs grandes em volume e custo de storage tende a ser maior.
- **Sistema de arquivos local** — sem custo de serviço externo, mas não escala e não tem redundância/backup nativo.

## Decisão
Usar **object storage compatível com S3**. Como pedido explicitamente pelo usuário: **AWS S3 enquanto estiver dentro do free tier**; caso o uso ultrapasse os limites do free tier (ou o período de 12 meses expire), migrar para **infraestrutura própria (MinIO self-hosted)**.

### Nota importante (`# REVISAR:` resolvido, mas registrado)
O free tier da AWS S3 é limitado — **5 GB de armazenamento e um número limitado de requisições, válido só nos primeiros 12 meses da conta**. Não existe "S3 gratuito para sempre". A decisão acima foi aplicada da forma mais fiel possível à instrução do usuário ("se for gratuito use AWS, senão infra própria"), mas isso significa que **haverá uma migração planejada** para MinIO self-hosted quando o free tier deixar de cobrir o uso real do projeto — não é uma escolha definitiva de longo prazo.

Gatilhos concretos para migrar de AWS S3 para MinIO self-hosted:
- Volume de imagens armazenadas se aproximando de 5 GB, ou
- Conta AWS completando 12 meses, ou
- Volume de requisições se aproximando dos limites do free tier.

Metadados (geolocalização, se autorizada pelo usuário; timestamp; resultado da detecção; versão do modelo usado — ver [ADR 0003](0003-versionamento-de-modelo.md)) ficam em um banco relacional separado, referenciando a chave do objeto no bucket.

## Consequências
- Define o contrato de upload da API (upload direto ao backend que repassa ao bucket, ou pré-signed URL — decisão de implementação futura).
- Exige política de consentimento/privacidade para uso das imagens em retrain, considerando a LGPD (dados de propriedade/geolocalização de agricultores).
- Cria dependência de monitorar uso do free tier da AWS para não haver cobrança surpresa nem interrupção de serviço na migração.
- O bucket (AWS ou MinIO) alimenta tanto o versionamento via DVC (ADR 0003) quanto o pipeline de retrain do modelo.

## Atualização 2026-07-28 — consolidação de região (sa-east-1)
Ao provisionar o User Pool do Cognito (ADR 0007), o usuário criou o recurso em **sa-east-1** (São Paulo), por decisão deliberada de latência para o público técnico no Brasil. Isso ficou divergente do bucket de imagens `cabruca-images-dev`, criado em **us-east-1**. Decidido consolidar toda a infraestrutura AWS do projeto em **sa-east-1** — o bucket ainda estava vazio (nenhuma imagem real armazenada), então não há dado a migrar, só recriar o recurso na região certa.

## Atualização 2026-08-01 — bucket de imagens criado em sa-east-1
Ao tentar excluir o bucket `cabruca-images-dev` em us-east-1 (conforme item pendente abaixo), a AWS retornou `NoSuchBucket` — como nomes de bucket S3 são únicos globalmente, isso confirma que o bucket **não existia de fato** (a nota de 2026-07-28 estava desatualizada; provavelmente nunca chegou a ser criado, ou foi apagado sem atualização do registro aqui).

Criado do zero em **sa-east-1**, com o nome `cabruca-images-dev-4f9` (sufixo adicionado porque `cabruca-images-dev` já estava ocupado por outra conta AWS ao tentar criar). Bucket configurado com:
- Bloqueio total de acesso público (`put-public-access-block`).
- Criptografia padrão SSE-S3 (`put-bucket-encryption`).

`backend/.env` e `backend/.env.example` atualizados com `S3_BUCKET_NAME=cabruca-images-dev-4f9`.

## # REVISAR:
- Confirmar com o usuário, antes da migração de fato, se AWS S3 free tier ou infraestrutura própria (MinIO) deve ser o destino final — esta ADR documenta um plano, não uma decisão irreversível.
