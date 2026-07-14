# ADR 0003 — Versionamento de Modelo (e Dataset)

## Status
Aceito (2026-07-13)

## Contexto
Time pequeno/médio, sem infraestrutura de MLOps madura ainda. A [ADR 0001](0001-classificacao-vs-deteccao.md) exige versionar não só imagens, mas também anotações de bounding box junto com os modelos treinados sobre elas.

## Opções consideradas

- **MLflow** (self-hosted ou managed) — tracking de experimentos e model registry maduro. Exige hospedar (ou pagar) um servidor de tracking + storage de artefatos; curva de aprendizado e manutenção operacional considerável para um time pequeno.
- **DVC (Data Version Control)** — versiona datasets e modelos junto com o git, sem exigir servidor próprio (usa um remote storage simples). Menos recursos de dashboard/comparação de experimentos que o MLflow, exige disciplina de uso.
- **Convenção manual** (nome de arquivo + planilha/banco) — zero infraestrutura nova, mas não escala e é propensa a erro humano; sem rastreabilidade real.
- **Model registry de provedor de nuvem** (ex. SageMaker, Vertex AI) — integrado ao provedor, mas gera lock-in e é decisão prematura antes de qualquer necessidade real de treino em escala.

## Decisão
Adotar **DVC**, com o remote apontando para o mesmo storage de imagens definido na [ADR 0004](0004-armazenamento-de-imagens.md) (AWS S3 dentro do free tier, ou infraestrutura própria conforme o gatilho descrito naquele ADR).

Evoluir para MLflow apenas se houver múltiplos experimentos/modelos em paralelo que justifiquem tracking mais robusto que o oferecido pelo DVC.

## Consequências
- Adotar Git + DVC desde o início do pipeline de treino, incluindo as anotações de bounding box (não só as imagens brutas).
- O storage de artefatos de modelo pode ser o mesmo bucket de imagens (com prefixo/pasta separada) ou um bucket dedicado — decisão de implementação, não architetural.
- Adia a decisão de um provedor de MLOps mais completo (MLflow ou equivalente de nuvem) para quando houver evidência de necessidade real.

## # REVISAR:
Nenhum ponto pendente nesta ADR.
