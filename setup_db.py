"""Crea (o ricrea) il database applicando app/bomba.sql.

- Se DATABASE_URL è settato (es. Supabase) → applica lo schema a PostgreSQL,
  traducendo al volo `INTEGER PRIMARY KEY AUTOINCREMENT` → `SERIAL PRIMARY KEY`.
- Altrimenti → ricrea il file SQLite locale in instance/.

Uso:
    python setup_db.py
"""
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL')

with open('app/bomba.sql', encoding='utf-8') as f:
    schema_sql = f.read()


def setup_postgres(url):
    import psycopg2

    # PROTEZIONE: chiedi conferma prima di cancellare dati su Supabase
    print("\n" + "!"*60)
    print("ATTENZIONE: Stai per cancellare il database PostgreSQL!")
    print("Host:", url.split('@')[1].split(':')[0] if '@' in url else 'sconosciuto')
    print("!"*60)
    conferma = input("\nSei SICURO di voler cancellare TUTTI i dati? Scrivi 'SÌ' per continuare: ")

    if conferma.strip().upper() not in ['SÌ', 'SI']:
        print("Operazione annullata. Database non è stato modificato.")
        sys.exit(0)

    # SQLite usa AUTOINCREMENT, PostgreSQL usa SERIAL: unica differenza di dialetto
    pg_sql = schema_sql.replace(
        'INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY'
    )
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    cur.execute(pg_sql)
    conn.commit()
    conn.close()
    print("\nDatabase PostgreSQL creato con successo (Supabase).")
    print("Ora puoi avviare il server con: gunicorn run:app")


def setup_sqlite():
    import sqlite3
    os.makedirs('instance', exist_ok=True)
    db_path = os.path.join('instance', 'schoolhrm.sqlite')
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print("Database esistente eliminato.")
        except PermissionError:
            print("Impossibile eliminare il database (file in uso).")
            print("Chiudi il server Flask e riprova, oppure elimina manualmente:")
            print(f"  {os.path.abspath(db_path)}")
            sys.exit(1)
    conn = sqlite3.connect(db_path)
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()
    print("Database SQLite creato con successo!")
    print("Ora puoi avviare il server con: python run.py")


if DATABASE_URL:
    setup_postgres(DATABASE_URL)
else:
    setup_sqlite()
