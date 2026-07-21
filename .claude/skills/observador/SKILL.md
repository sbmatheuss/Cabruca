---
name: observador
description: Observa o repositório CABRUCA em busca de bugs introduzidos ou preexistentes e relata os achados — não corrige nada sozinho. Use quando o usuário pedir "/observador", "observa o projeto", "tem bug novo?".
---

# /observador

Skill de observação passiva: a cada invocação, escaneia o estado atual do repositório em busca de bugs (novos ou preexistentes) e produz um relatório. **Nunca edita código.** Corrigir é decisão do usuário, conforme o protocolo colaborativo do `CLAUDE.md` (aprovação explícita antes de qualquer código).

Este comando é tipicamente disparado em loop (`/loop 4m /observador`) enquanto a IA principal trabalha no projeto em outra conversa/sessão — funciona como um segundo par de olhos rodando em paralelo.

## Passos ao executar

1. Rode `git status` e `git diff` (staged e unstaged) para ver o que mudou desde a última verificação. Se nada mudou desde o último `/observador` desta conversa, diga isso em uma frase e pare — não repita um relatório idêntico.
2. Nos arquivos alterados (ou, se não houver diff, nos arquivos-chave do backend tocados mais recentemente via `git log -n 5 --stat`), procure por:
   - erros de lógica óbvios (off-by-one, condição invertida, comparação errada de tipo)
   - bugs de concorrência/async mal tratado (esquecimento de `await`, sessão SQLAlchemy não fechada)
   - inconsistência com os ADRs em `docs/adr/` (ex.: retorno de classificação única onde a ADR 0001 exige lista de detecções; chamada síncrona onde a ADR 0002 exige fila assíncrona)
   - marcações `# REVISAR:` deixadas no código sem decisão tomada
   - erros que só apareceriam em runtime (import faltando, nome de variável errado, chamada de função com assinatura incompatível)
3. Não invente bugs: se nada relevante for encontrado, diga explicitamente "nenhum bug identificado nesta varredura" — não force achados fracos só para preencher o relatório.
4. Para cada achado real, reporte: arquivo:linha, o que está errado, e o cenário concreto que quebra (input/estado que causa o problema) — no mesmo espírito de um finding de code review, mas como texto simples, já que esta skill não é `/code-review`.
5. Nunca proponha nem aplique a correção diretamente — no máximo, sugira em uma frase qual seria a correção, deixando a decisão para o usuário aprovar depois.
6. Não repita, em execuções futuras dentro da mesma sessão, um achado já reportado anteriormente a menos que o código relacionado tenha mudado de novo.
