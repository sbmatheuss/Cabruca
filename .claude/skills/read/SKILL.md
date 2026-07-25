---
name: read
description: Atualiza o README.md do projeto CABRUCA para refletir o estado real do repositório e sobe direto para o GitHub (origin/main), sem pedir confirmação a cada execução. Use quando o usuário pedir "/read", "atualiza o readme", "sobe o readme".
---

# /read

Skill de manutenção do README: a cada invocação, reverifica o estado real do repositório (não confie em memória de conversas anteriores) e reescreve `README.md` pra refletir o que existe de fato — depois commita e dá push pra `origin/main` automaticamente.

**Autorização de push já dada pelo usuário para este comando especificamente** (2026-07-24) — não perguntar de novo a cada execução. Isso vale só para o commit/push do `README.md` feito por este comando; não estende autorização automática pra outras mudanças ou branches.

## Passos ao executar

1. Rode buscas rápidas no repo (Glob/Grep/Bash) pra checar o estado atual — mesmo espírito do `/check`: rotas em `backend/app/api/routes/`, ADRs em `docs/adr/`, testes em `backend/tests/`, workflows em `.github/workflows/`, DVC (`.dvc/config`), etc. Não copie o texto antigo do README sem confirmar contra o repo.
2. Reescreva `README.md` mantendo a mesma estrutura/seções da versão atual (visão geral, estado atual do projeto, decisões arquiteturais, como rodar localmente, protocolo de trabalho) — atualize só o que mudou de fato.
3. **Nunca invente dado, número ou funcionalidade que não exista no repo.** Se uma área não mudou desde a última vez, não reescreva a frase à toa.
4. Se `git diff -- README.md` não mostrar nenhuma mudança depois do passo 2 (README já está atualizado), diga isso em uma frase e pare — não crie commit vazio nem dê push à toa.
5. Se houver mudança real:
   - `git add README.md` (só este arquivo — nunca `git add -A`/`git add .`, pra não arrastar mudanças não relacionadas que possam estar em andamento no working tree).
   - `git commit` com mensagem curta descrevendo o que mudou no README.
   - `git push origin main` — direto, sem perguntar.
6. Se o push falhar (ex.: branch divergiu do remoto), pare e reporte o erro ao usuário — não force push.
7. Reporte em 1-2 frases o que mudou no README e confirme que subiu (com o hash do commit).
