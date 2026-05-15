"""Connessione al DB: PostgreSQL in produzione (DATABASE_URL), SQLite in locale.

Se la config `DATABASE_URL` è valorizzata (Render + Supabase) si usa psycopg2,
altrimenti si ricade su SQLite (sviluppo locale e suite di test). I repository
restano invariati: il wrapper PostgreSQL espone la stessa API di sqlite3.
"""
import sqlite3
from flask import g, current_app


def _database_url():
    return current_app.config.get('DATABASE_URL')


class _PgConnection:
    """Adatta psycopg2 all'interfaccia usata dai repository (come sqlite3.Connection).

    - converte i placeholder `?` in `%s`
    - RealDictCursor → le righe si accedono con row['colonna'] come sqlite3.Row
    """

    def __init__(self, url):
        import psycopg2
        from psycopg2.extras import RealDictCursor
        self._conn = psycopg2.connect(url, cursor_factory=RealDictCursor)

    def execute(self, sql, params=()):
        cur = self._conn.cursor()
        cur.execute(sql.replace('?', '%s'), params)
        return cur

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


def get_db():
    if 'db' not in g:
        url = _database_url()
        if url:
            g.db = _PgConnection(url)
        else:
            g.db = sqlite3.connect(current_app.config['DATABASE'])
            g.db.row_factory = sqlite3.Row
            g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)
