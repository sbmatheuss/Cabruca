# ADR 0005 — Stack de Backend

## Status
Aceito (2026-07-14)

## Contexto
O repositório ainda não tem código de aplicação. As decisões já tomadas moldam requisitos concretos para o backend:

- [ADR 0001](0001-classificacao-vs-deteccao.md) exige que a API retorne uma lista de detecções (classe + caixa + confiança) por imagem, não uma classe única.
- [ADR 0002](0002-inferencia-on-device-vs-nuvem.md) exige upload assíncrono: o app envia a imagem quando há rede, e o resultado é consultado depois — não é um request/response síncrono simples.
- [ADR 0004](0004-armazenamento-de-imagens.md) exige integração com object storage compatível com S3 (imagens) e um banco relacional separado (metadados, incluindo a lista de detecções).
- O modelo de detecção de objetos será treinado e servido no ecossistema Python (YOLO/PyTorch são a escolha dominante nessa área), o que pesa a favor de manter a API na mesma linguagem para evitar duplicar lógica de pré/pós-processamento em duas linguagens.

Por decisão explícita do usuário, o serviço de API (upload, fila, consulta de resultado) e o serviço de inferência do modelo serão **sistemas separados**, não um monolito.

## Opções consideradas

### Linguagem/framework da API
- **Python + FastAPI** — async nativo (compatível com o fluxo assíncrono da ADR 0002), gera contrato OpenAPI automaticamente, validação de payload via Pydantic, mesma linguagem do serviço de inferência.
- **Python + Django** — traz ORM/admin/auth prontos, mas é mais peso do que a API precisa (majoritariamente upload → fila → consulta de resultado), sem async nativo no núcleo do framework.
- **Node.js/TypeScript** — descartado por decisão explícita do usuário: manter a mesma linguagem do serviço de inferência (Python) evita duplicar lógica de validação/formatos de detecção em duas linguagens.

### Banco relacional de metadados
- **PostgreSQL** — já é o exigido pela ADR 0004 (metadados em banco relacional separado do storage); bom suporte a JSON para armazenar a lista de detecções por imagem, extensão PostGIS disponível caso geolocalização precise de queries espaciais no futuro.
- Nenhuma alternativa foi seriamente considerada aqui: a ADR 0004 já decidiu "banco relacional separado", e Postgres é o padrão de facto no ecossistema Python/FastAPI.

### Comunicação entre API e serviço de inferência (fila assíncrona)
- **Fila simples via tabela no Postgres** (coluna de status `pending`/`processing`/`done`, um worker faz polling) — zero infraestrutura nova, fácil de depurar no início; não escala bem e polling é menos eficiente que um sistema de fila dedicado.
- **Redis + Celery** — portável para self-host (junto com a futura migração para MinIO da ADR 0004), ecossistema Python maduro; exige rodar e manter mais uma peça de infraestrutura (Redis) desde o MVP.
- **AWS SQS** — já estamos no ecossistema AWS pela ADR 0004, free tier cobre bem o volume de um MVP, gerenciado; mas é mais uma dependência específica da AWS, e uma eventual migração para infraestrutura própria (self-host) exigiria trocar também a fila, não só o storage.

## Decisão
- API em **Python + FastAPI**.
- Metadados em **PostgreSQL**.
- Comunicação entre API e serviço de inferência via **fila simples implementada como tabela no Postgres** (status `pending`/`processing`/`done`), com um worker de polling no serviço de inferência.

A escolha da fila via Postgres é deliberadamente a opção mais simples: evita introduzir infraestrutura nova (Redis ou SQS) antes de haver evidência de necessidade real, seguindo o mesmo espírito de adiar complexidade da ADR 0002. O volume esperado no MVP é baixo o suficiente para que polling não seja gargalo.

## Consequências
- API e serviço de inferência são deployáveis e escaláveis de forma independente, mas compartilham o mesmo banco Postgres (a tabela de fila) como ponto de acoplamento — mudanças no schema da fila afetam os dois lados.
- Migrar a fila para Redis/Celery ou SQS no futuro é uma decisão isolada (não exige reescrever a API nem o serviço de inferência do zero), mas deve virar uma nova ADR quando houver evidência de que o polling em Postgres virou gargalo (ex.: latência de detecção de novos itens na fila, contenção de I/O no banco).
- Mantém tudo em Python, simplificando o time e o deploy (uma única linguagem para depurar todo o pipeline de dados até o modelo).
- Ainda não define: schema exato do banco, contrato de endpoints, estratégia de deploy/hosting, nem versão específica de FastAPI/Postgres — decisões de implementação futuras.

## # REVISAR:
Nenhum ponto em aberto no momento desta decisão. Se o volume de imagens/requisições crescer a ponto do polling em Postgres virar gargalo perceptível, revisar para Redis+Celery ou SQS.

### Nota de gatilho futuro (escala) — sem decisão firme, registrado em 2026-07-14
Discussão hipotética sobre um cenário de ~1 milhão de requisições levantou onde o desenho atual realmente quebraria primeiro. Registrado aqui para não perder o raciocínio, **sem que isso mude a decisão tomada acima** — continua valendo até haver evidência real de necessidade:

- **Fila em Postgres (este ADR)**: é o ponto de ruptura mais provável — polling em massa vira contenção de lock e I/O no banco. Gatilho concreto de migração para SQS/Redis+Celery: latência perceptível entre um item entrar na fila e o worker pegá-lo, ou contenção de I/O visível no banco de metadados.
- **`GET /images/{image_id}` (polling do cliente, ver `docs/api/contrato-endpoints.md`)**: em alto volume, cada consulta de status é uma leitura direta no Postgres principal. Antes de qualquer redesenho de endpoint, medidas paliativas: connection pooling e réplica de leitura para separar esse tráfego de leitura do tráfego de escrita da fila. Ver também a nota de considerações futuras no contrato de endpoints sobre substituir parte desse polling por push notification.
- **Rate limiting por usuário/dispositivo**: só é possível de implementar corretamente depois que existir identidade real de chamador — depende da futura ADR 0007 (autenticação). Até lá, qualquer limite de taxa só poderia ser por IP, o que é fraco e não é considerado solução real.
- A API FastAPI em si (camada stateless) e o upload de imagem via S3 (ADR 0006) não foram identificados como pontos de ruptura nesse volume — escalam horizontalmente sem redesenho.
