import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app import create_app

app = create_app()

if __name__ == '__main__':
    if not os.path.exists(os.path.join('instance', 'schoolhrm.sqlite')):
        print("Database non trovato! Esegui prima: python setup_db.py")
        exit(1)
    print("Avvio server...")
    app.run(debug=True)
