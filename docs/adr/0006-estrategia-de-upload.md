# ADR 0006 — Estratégia de Upload de Imagens

## Status
Aceito (2026-07-14)

## Contexto
A [ADR 0004](0004-armazenamento-de-imagens.md) decidiu armazenar imagens em object storage compatível com S3, mas deixou explicitamente em aberto *"upload direto ao backend que repassa ao bucket, ou pré-signed URL — decisão de implementação futura"*. Esta ADR resolve esse ponto.

A premissa central do projeto (ver `CLAUDE.md`) é que as fotos vêm de agricultores em campo, com **conectividade rural instável**. Isso torna o caminho que a imagem percorre até o bucket uma decisão com impacto direto na experiência do usuário, não só um detalhe de implementação.

## Opções consideradas

- **Upload direto ao backend** — o cliente envia a imagem (multipart) para a API (FastAPI), que repassa para o S3. Fluxo de uma chamada só; permite o backend validar/redimensionar a imagem antes de armazenar. Porém a imagem trafega **duas vezes** (cliente → backend → S3), o que dobra o tempo de exposição a uma conexão instável e aumenta a carga de banda/memória no backend.
- **Pré-signed URL** — o backend gera uma URL temporária de upload direto ao bucket S3; o cliente sobe a imagem direto para o storage, sem passar pelo backend. A imagem trafega **uma vez só**, minimizando o risco de falha em conexão ruim, e reduz carga no backend. O custo é um fluxo em duas chamadas (pedir a URL, depois confirmar que o upload terminou) e a impossibilidade de validar/transformar a imagem antes dela estar no bucket (validação vira pós-upload).

## Decisão
Usar **pré-signed URL**. A conectividade rural instável é uma premissa central do projeto, e o upload direto ao backend duplicaria justamente o tráfego no cenário mais frágil (conexão ruim). O custo de um fluxo em duas chamadas é aceitável frente a esse ganho.

Fluxo decidido:
1. Cliente pede uma URL de upload à API.
2. API cria o registro da imagem no Postgres com status `pending_upload` e retorna a URL pré-assinada do S3.
3. Cliente sobe a imagem diretamente ao bucket usando essa URL.
4. Cliente confirma à API que o upload terminou; a API verifica a existência do objeto no bucket e muda o status para `queued`, entrando na fila de detecção definida na [ADR 0005](0005-stack-de-backend.md).

## Consequências
- Validação de conteúdo da imagem (formato, tamanho, dimensões mínimas) só pode ocorrer **depois** que o objeto já está no bucket — não antes, como aconteceria com upload direto ao backend. Uma imagem inválida gera custo de storage e exige lógica de limpeza/rejeição pós-upload.
- O passo de confirmação (etapa 4) depende do cliente de fato chamar a API depois do upload. Se o cliente falhar em confirmar (app fechado, sem rede na hora certa), a imagem fica órfã no bucket sem nunca entrar na fila — decisão de implementação futura: expirar/limpar registros presos em `pending_upload` após um tempo, ou usar notificação de evento do S3 como alternativa/reforço à confirmação do cliente.
- Define parte do contrato de endpoints (documentado em `docs/api/contrato-endpoints.md`): existe uma etapa explícita de "pedir upload" separada de "confirmar upload".
- URLs pré-assinadas têm expiração; isso precisa ser curto o bastante para segurança, mas longo o bastante para tolerar uma conexão rural lenta — valor exato de expiração é decisão de implementação futura.

## # REVISAR:
Nenhum ponto pendente de decisão do usuário nesta ADR. A estratégia de limpeza de uploads órfãos (registros presos em `pending_upload`) fica registrada como decisão de implementação futura, não como bloqueio desta ADR.
