# Modelos

Estrutura reservada para pesos do modelo de detecção treinado. Ainda **vazia** — nenhum treino foi executado até o momento.

## Fluxo esperado (quando houver um modelo treinado)

Versionado via **DVC**, não pelo Git (`models/.gitignore` ignora os arquivos reais de peso) — ver [ADR 0003](../docs/adr/0003-versionamento-de-modelo.md) e [ADR 0010](../docs/adr/0010-implementacao-dvc.md). A versão usada em produção é registrada no campo `model_version` de cada imagem processada (`docs/api/contrato-endpoints.md`).

```bash
# depois de gerar os pesos de um treino real em models/:
dvc add models/<nome-do-arquivo-de-pesos>
git add models/<nome-do-arquivo-de-pesos>.dvc models/.gitignore
git commit -m "..."
dvc push   # requer o bucket cabruca-dvc-dev criado na AWS e credenciais configuradas
```
