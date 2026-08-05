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

[ADR 0012](../docs/adr/0012-ferramenta-anotacao-dataset.md) decidiu **CVAT self-hosted** (Docker Compose). Instalação **fora deste repositório** (decisão: documentar comandos fixados numa versão, não vendorizar a config do CVAT aqui — evita manter uma cópia de terceiro que fica desatualizada).

Instalação (versão fixada, [instalação oficial](https://docs.cvat.ai/docs/administration/community/basics/installation/)):

```bash
git clone -b v2.72.0 https://github.com/cvat-ai/cvat
cd cvat
docker compose up -d
docker exec -it cvat_server bash -ic 'python3 ~/manage.py createsuperuser'
```

Acesse http://localhost:8080, crie uma task apontando para as imagens de `dataset/images/`, desenhe as bounding boxes usando a taxonomia da ADR 0011, exporte em formato **COCO 1.0** e salve o JSON em `dataset/annotations/`. Export do CVAT deve ser conferido contra a lista de `categories` acima (rode `dataset/scripts/validate_dataset.py`) antes de entrar em `annotations/`.

Pra encerrar: `docker compose down` (a partir da pasta onde o CVAT foi clonado).

# REVISAR: versão fixada em v2.72.0 (mais recente em 2026-08-05) — atualizar aqui se o projeto decidir subir de versão depois.

## Fluxo esperado (quando houver dados reais)

O conteúdo desta pasta é versionado via **DVC**, não pelo Git (`dataset/.gitignore` ignora os arquivos reais, mantendo só a estrutura de pastas) — ver [ADR 0003](../docs/adr/0003-versionamento-de-modelo.md) e [ADR 0010](../docs/adr/0010-implementacao-dvc.md).

```bash
# depois de adicionar imagens/anotações reais em dataset/images e dataset/annotations:
dvc add dataset/images dataset/annotations
git add dataset/images.dvc dataset/annotations.dvc dataset/.gitignore
git commit -m "..."
dvc push   # requer credenciais AWS configuradas localmente com acesso ao bucket
```

O remote do DVC (`s3://cabruca-dvc-dev-klm`, sa-east-1) já é um bucket real, criado em 2026-08-01 — não é mais um placeholder (ver ADR 0010 e `.dvc/config`).
