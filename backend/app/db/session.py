import asyncio
import sys

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings

# Garante que todos os models sejam registrados no Base.metadata antes de
# qualquer flush/commit — sem isso, o SQLAlchemy não conhece tabelas que
# nenhum outro módulo importou diretamente (ex.: 'users'), e falha ao
# resolver foreign keys. Mesmo motivo pelo qual migrations/env.py já
# importa todos os models explicitamente para o autogenerate.
import app.models  # noqa: E402, F401

# psycopg (modo async) não suporta o ProactorEventLoop, padrão do asyncio no
# Windows — precisa do SelectorEventLoop. Sem isso, toda query real falha com
# psycopg.InterfaceError assim que o event loop é criado (asyncio.run() nos
# scripts, ou o próprio uvicorn ao servir). Precisa rodar antes da criação do
# loop, por isso fica aqui, no import deste módulo.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

engine = create_async_engine(settings.database_url)
async_session = async_sessionmaker(engine, expire_on_commit=False)
