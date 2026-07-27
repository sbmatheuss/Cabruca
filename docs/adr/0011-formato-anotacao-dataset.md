# ADR 0011 — Formato de Anotação do Dataset e Taxonomia de Classes

## Status
Aceito (2026-07-26)

## Contexto
A [ADR 0001](0001-classificacao-vs-deteccao.md) decidiu que o dataset precisa ser anotado com bounding boxes, mas deixou em aberto a escolha entre "formato COCO ou YOLO". A pasta `dataset/` (imagens e anotações) existe apenas como estrutura vazia (`.gitkeep`) — sem uma decisão concreta de schema, não há como escrever um script de validação de dataset nem orientar quem for anotar.

Também não havia, até agora, uma lista fechada de classes (doenças/pragas) que o dataset deve cobrir.

## Opções consideradas (formato de anotação)
- **YOLO** — um arquivo `.txt` por imagem, cada linha `classe x_center y_center largura altura` normalizado (0-1). Simples, permite validar cada imagem isoladamente sem parsear um arquivo único grande, é o formato nativo de frameworks da família YOLO (Ultralytics).
- **COCO** — um único JSON (por split) com arrays `images`, `annotations`, `categories`, bbox em pixels absolutos `[x, y, largura, altura]`. Ecossistema mais rico para avaliação padrão (`pycocotools`, mAP COCO-style) e compatibilidade com torchvision/Detectron2, ao custo de um schema mais verboso e validação que exige o JSON inteiro.

## Decisão
Adotar **COCO** para `dataset/annotations/` — decisão explícita do usuário (2026-07-26).

Taxonomia de classes fechada para o MVP (`categories` do schema COCO):

| id | name |
|---|---|
| 0 | vassoura-de-bruxa |
| 1 | podridao-parda |
| 2 | moniliase |

Mal-do-facão (*Ceratocystis cacaofunesta*) e as pragas levantadas (tripes, ácaros, cochonilha, mosca-branca, monalônio, besouros) ficaram fora do MVP: são sintomas sistêmicos (mal-do-facão) ou alvos pequenos demais para bounding box confiável a partir de foto de celular com iluminação/enquadramento variáveis (premissa da ADR 0001).

## Consequências
- `dataset/annotations/` passa a conter JSON(s) no schema COCO (`images`, `annotations`, `categories`), não arquivos `.txt` por imagem.
- O bbox em COCO é pixels absolutos — diferente da convenção normalizada 0-1 já adotada pela [ADR 0009](0009-formato-bounding-box.md) para o schema da API/banco (`backend/app/models/detection.py`). Não é um conflito: são etapas distintas do pipeline (anotação de treino vs. resultado de inferência armazenado). Qualquer pipeline de treino/inferência que grave detecções via API precisa converter pixels absolutos (COCO) → normalizado 0-1 antes de persistir.
- Se a arquitetura de detecção adotada futuramente for da família YOLO (candidata citada na ADR 0001), o treino provavelmente vai exigir uma conversão COCO → YOLO como pré-processamento — ferramentas como o Ultralytics já têm conversores prontos; custo aceito em troca do ecossistema de avaliação padrão do COCO.
- O script de validação de dataset (próximo passo) deve validar contra este schema e contra esta lista fechada de `categories`.

## # REVISAR:
Nenhum ponto pendente nesta ADR — decisão confirmada explicitamente pelo usuário.
