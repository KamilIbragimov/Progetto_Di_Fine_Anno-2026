"""Entry point della web app Flask in modalità sviluppo (`python run.py`)."""
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app import create_app

app = create_app()

if __name__ == '__main__':
    # In produzione (Render) si usa `gunicorn run:app` e questo blocco non gira.
    # Il check sul file serve solo allo sviluppo locale con SQLite.
    usa_sqlite = not os.environ.get('DATABASE_URL')

    # Stampa quale database sta usando
    print("\n" + "="*60)
    if usa_sqlite:
        print("DATABASE: SQLite (sviluppo locale)")
        print("File: instance/schoolhrm.sqlite")
    else:
        db_host = os.environ.get('DATABASE_URL', '').split('@')[1].split(':')[0] if '@' in os.environ.get('DATABASE_URL', '') else 'sconosciuto'
        print("DATABASE: PostgreSQL (Supabase)")
        print(f"Host: {db_host}")
    print("="*60 + "\n")

    if usa_sqlite and not os.path.exists(os.path.join('instance', 'schoolhrm.sqlite')):
        print("Database non trovato! Esegui prima: python setup_db.py")
        exit(1)
    print("Avvio server su http://127.0.0.1:5000...")
    app.run(debug=True)
