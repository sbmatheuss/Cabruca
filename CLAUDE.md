# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Sobre o projeto

CABRUCA é um sistema de detecção de doenças e pragas em cacau (*Theobroma cacao*) a partir de imagens de campo (fotos tiradas por celular, geralmente por não especialistas, com iluminação/enquadramento variáveis e conectividade rural instável).

O repositório está em estágio inicial: ainda não há código de aplicação (backend, app, treino de modelo). O que existe hoje são as decisões arquiteturais fundacionais em `docs/adr/`, que devem ser lidas antes de propor qualquer implementação, pois moldam o contrato de dados e de API desde a primeira linha de código:

- [`docs/adr/0001-classificacao-vs-deteccao.md`](docs/adr/0001-classificacao-vs-deteccao.md) — o produto faz **detecção de objetos** (bounding boxes, localizar e contar lesões), não classificação de imagem inteira. Isso significa: dataset anotado em formato COCO/YOLO, API retorna lista de detecções (classe + caixa + confiança) por lesão, não uma classe única.
- [`docs/adr/0002-inferencia-on-device-vs-nuvem.md`](docs/adr/0002-inferencia-on-device-vs-nuvem.md) — inferência é **cloud-first no MVP**, com fila local de upload assíncrono no app (captura offline, envia quando há rede). A API precisa suportar upload assíncrono com resultado consultado depois, não apenas request/response síncrono. Inferência on-device é fase 2, condicionada a modelo estável e evidência de necessidade real.
- [`docs/adr/0003-versionamento-de-modelo.md`](docs/adr/0003-versionamento-de-modelo.md) — versionamento de dataset (imagens + anotações de bounding box) e modelo via **DVC**, remote apontando para o mesmo storage de imagens da ADR 0004.
- [`docs/adr/0004-armazenamento-de-imagens.md`](docs/adr/0004-armazenamento-de-imagens.md) — armazenamento em **object storage compatível com S3**: AWS S3 enquanto dentro do free tier (5 GB / 12 meses), com migração planejada para MinIO self-hosted quando o free tier deixar de cobrir o uso real. Metadados (geolocalização se autorizada, timestamp, resultado, versão do modelo) ficam em banco relacional separado referenciando a chave do objeto.

Novas decisões arquiteturais relevantes (ex.: escolha de framework de detecção, stack de backend, escolha entre AWS S3/MinIO na prática) devem virar um novo ADR em `docs/adr/`, seguindo o mesmo formato: Contexto → Opções (com trade-offs reais) → Decisão → Consequências.

## Protocolo de trabalho (definido pelo usuário, vale para todo o projeto)

Este projeto é conduzido em modo colaborativo, não "faça tudo e entregue":

1. Antes de escrever qualquer código, apresentar o plano da etapa e esperar aprovação explícita do usuário.
2. Código em blocos pequenos (máx. ~50 linhas por vez). Para cada bloco: explicar antes o que ele faz e por que essa abordagem, apontar trade-offs e o que foi descartado, e marcar com comentário `# REVISAR:` qualquer ponto que exija decisão do usuário.
3. Parar após cada bloco e perguntar antes de seguir para o próximo.
4. Nunca instalar dependência sem avisar o motivo antes.
5. Se um pedido do usuário for tecnicamente ruim, discordar e justificar — não executar silenciosamente.
6. Nunca inventar dados, links, datasets, métricas ou skills. Se não souber, dizer "não sei". Skills/plugins citados em instruções devem ser verificados contra o que de fato está instalado (`~/.claude/skills`, `.claude/skills`, plugins carregados) antes de assumir que existem.

## Comandos

Ainda não há build, lint, testes ou dependências configuradas neste repositório — nenhum framework ou linguagem foi escolhido para implementação ainda. Esta seção deve ser preenchida assim que a primeira stack (backend, treino de modelo, ou app) for decidida e commitada.
