# ADR 0001 — Classificação vs. Detecção vs. Segmentação

## Status
Aceito (2026-07-13)

## Contexto
O CABRUCA precisa identificar doenças e pragas em folhas/frutos de cacau (*Theobroma cacao*) a partir de fotos de campo, geralmente tiradas por não especialistas com celular, com iluminação e enquadramento variáveis.

Decisão do time (2026-07-13): o produto deve **localizar e contar as lesões desde o MVP**, não apenas classificar a imagem como um todo.

## Opções consideradas

- **(a) Classificação de imagem inteira** — um rótulo por foto (ex.: "vassoura-de-bruxa", "saudável"). Mais barato de anotar e treinar, mas não localiza nem conta lesões — descartado, não atende ao requisito.
- **(b) Detecção de objetos (bounding boxes)** — localiza cada lesão/inseto na imagem com uma caixa delimitadora. Permite contar ocorrências e mostrar ao agricultor onde está o problema. Custo de anotação bem maior que classificação (desenhar caixas por lesão), modelos (ex. YOLO, Faster R-CNN) mais pesados e mais complexos de treinar/ajustar.
- **(c) Segmentação semântica/instância** — contorno exato de cada lesão, pixel a pixel. Permite medir área afetada (severidade), mas tem o maior custo de anotação e o maior custo computacional das três opções.

## Decisão
Adotar **detecção de objetos (bounding boxes)** desde o MVP.

Segmentação fica em backlog — só entra em pauta se "percentual de área afetada" virar requisito de produto validado com usuários reais, dado seu custo de anotação e de treino/inferência.

## Consequências
- O dataset inicial precisa ser anotado com bounding boxes (não apenas rótulo por imagem) — formato COCO ou YOLO.
- A anotação é mais cara e demorada que classificação simples; planejar tempo/orçamento de rotulagem já na primeira fase.
- Modelos de detecção são mais pesados computacionalmente, o que reforça a decisão de inferência cloud-first no MVP (ver [ADR 0002](0002-inferencia-on-device-vs-nuvem.md)) — rodar detecção on-device fica ainda mais distante como opção de curto prazo.
- O versionamento de dataset (ver [ADR 0003](0003-versionamento-de-modelo.md)) precisa versionar anotações de bounding box junto com as imagens, não só as imagens.
- A API deve retornar uma lista de detecções (classe + caixa + confiança por lesão), não apenas uma classe única — isso molda o contrato da API desde já.

## # REVISAR:
Nenhum ponto pendente nesta ADR — decisão confirmada explicitamente pelo usuário.
