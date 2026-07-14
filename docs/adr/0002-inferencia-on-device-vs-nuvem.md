# ADR 0002 — Inferência: On-device vs. Nuvem

## Status
Aceito (2026-07-13)

## Contexto
O uso é em campo, tipicamente em áreas rurais com conectividade instável ou inexistente. A [ADR 0001](0001-classificacao-vs-deteccao.md) definiu detecção de objetos (não classificação simples) desde o MVP, o que implica modelos mais pesados.

## Opções consideradas

- **(a) On-device** (ex. TensorFlow Lite, ONNX Runtime Mobile) — funciona offline, baixa latência, sem custo de infraestrutura por requisição, preserva privacidade. Exige modelo leve/quantizado (perda de acurácia), atualização de modelo requer atualizar o app ou baixar novo artefato, e testar em aparelhos Android de entrada (comuns no público-alvo) é trabalho extra. Modelos de detecção (ADR 0001) são mais difíceis de comprimir sem perda relevante de acurácia.
- **(b) Nuvem** — modelo maior e sempre atualizado, mais fácil de monitorar e melhorar centralmente, simplifica versionamento. Depende de internet no momento do uso (problema real dado o cenário rural), tem custo de infraestrutura por chamada, e a foto da propriedade sai do dispositivo.
- **(c) Híbrido** — modelo leve on-device para resposta imediata offline + reprocessamento/confirmação na nuvem quando há conexão. Cobre o caso offline mas dobra a complexidade de engenharia (dois modelos, sincronização, dois versionamentos).

## Decisão
**Cloud-first no MVP**, aceito explicitamente pelo usuário como adequado ao cenário de conectividade rural, com um mecanismo de **fila local de upload assíncrono**: o app captura e guarda a foto localmente quando não há rede, e envia para a API assim que houver conexão disponível. O resultado da detecção não precisa ser síncrono — pode chegar depois do envio.

Inferência on-device (TFLite ou similar) fica para uma fase 2, condicionada a: (1) o modelo de detecção estar validado e estável, e (2) haver evidência de que a falta de resposta offline é um bloqueador real para os usuários.

## Consequências
- O app mobile precisa de armazenamento local temporário + fila de sincronização (não é um simples "enviar e esperar resposta").
- A API deve aceitar uploads assíncronos e permitir consultar o resultado depois (ex. polling ou notificação), não apenas request/response síncrono.
- Adia a escolha de framework de inferência mobile (TFLite, ONNX Runtime, Core ML) até existir um modelo estável para exportar — não decidir isso agora.
- Reforça a necessidade de a API/backend suportar picos de upload quando o usuário volta a ter conexão (vários envios em lote).

## # REVISAR:
Nenhum ponto pendente — decisão confirmada explicitamente pelo usuário.
