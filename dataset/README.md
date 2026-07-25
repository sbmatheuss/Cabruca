# Dataset

Estrutura reservada para o dataset anotado de detecção de doenças/pragas em cacau. Ainda **vazia** — nenhuma imagem ou anotação real foi adicionada até o momento.

- `images/` — fotos de campo (celular, iluminação/enquadramento variáveis).
- `annotations/` — anotações de bounding box em formato COCO ou YOLO (decisão de detecção de objetos, não classificação — [ADR 0001](../docs/adr/0001-classificacao-vs-deteccao.md)).

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
