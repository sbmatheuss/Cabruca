"""Entrada para rodar a API localmente (ver CLAUDE.md).

Uso: poetry run python run.py
"""

import asyncio
import sys

# psycopg (modo async) exige SelectorEventLoop (ver app/db/session.py). Ao
# rodar via `uvicorn app.main:app` na CLI, o uvicorn cria o event loop antes
# de importar a app, então definir a policy dentro do código da app chega
# tarde demais — precisa acontecer aqui, antes de uvicorn.run() criar o loop.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
