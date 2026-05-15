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
    if usa_sqlite and not os.path.exists(os.path.join('instance', 'schoolhrm.sqlite')):
        print("Database non trovato! Esegui prima: python setup_db.py")
        exit(1)
    print("Avvio server...")
    app.run(debug=True)
