# Dataset

Estrutura reservada para o dataset anotado de detecção de doenças/pragas em cacau. Ainda **vazia** — nenhuma imagem ou anotação real foi adicionada até o momento.

- `images/` — fotos de campo (celular, iluminação/enquadramento variáveis).
- `annotations/` — anotações de bounding box em **formato COCO** (decisão de detecção de objetos, não classificação — [ADR 0001](../docs/adr/0001-classificacao-vs-deteccao.md); escolha entre COCO e YOLO fechada na [ADR 0011](../docs/adr/0011-formato-anotacao-dataset.md)): um JSON (por split) com `images`, `annotations`, `categories`, bbox em pixels absolutos `[x, y, largura, altura]`.

## Classes (MVP)

Taxonomia fechada na [ADR 0011](../docs/adr/0011-formato-anotacao-dataset.md) — `categories` do schema COCO:

| id | name |
|---|---|
| 0 | vassoura-de-bruxa |
| 1 | podridao-parda |
| 2 | moniliase |

Mal-do-facão e pragas (tripes, ácaros, cochonilha, mosca-branca, monalônio, besouros) ficaram fora do MVP: sintoma sistêmico (mal-do-facão) ou alvo pequeno demais para bounding box confiável a partir de foto de celular.

## Ferramenta de anotação

[ADR 0012](../docs/adr/0012-ferramenta-anotacao-dataset.md) decidiu **CVAT self-hosted** (Docker Compose) para desenhar as bounding boxes. Ainda não instalado — só necessário quando houver fotos reais para rotular. Export do CVAT deve sair em COCO JSON e ser conferido contra a lista de `categories` acima antes de entrar em `annotations/`.

## Fluxo esperado (quando houver dados reais)

O conteúdo desta pasta é versionado via **DVC**, não pelo Git (`dataset/.gitignore` ignora os arquivos reais, mantendo só a estrutura de pastas) — ver [ADR 0003](../docs/adr/0003-versionamento-de-modelo.md) e [ADR 0010](../docs/adr/0010-implementacao-dvc.md).

```bash
# depois de adicionar imagens/anotações reais em dataset/images e dataset/annotations:
dvc add dataset/images dataset/annotations
git add dataset/images.dvc dataset/annotations.dvc dataset/.gitignore
git commit -m "..."
dvc push   # requer o bucket cabruca-dvc-dev criado na AWS e credenciais configuradas
```

O remote do DVC (`s3://cabruca-dvc-dev`) ainda é um placeholder — o bucket não foi criado na AWS ainda (ver `# REVISAR:` em `.dvc/config` e ADR 0010).
