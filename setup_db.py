import sqlite3
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

if not os.path.exists('instance'):
    os.makedirs('instance')

db_path = os.path.join('instance', 'schoolhrm.sqlite')

if os.path.exists(db_path):
    try:
        os.remove(db_path)
        print("Database esistente eliminato.")
    except PermissionError:
        print("Impossibile eliminare il database (file in uso).")
        print("Chiudi il server Flask e riprova, oppure elimina manualmente il file:")
        print(f"  {os.path.abspath(db_path)}")
        exit(1)

connection = sqlite3.connect(db_path)

with open('app/bomba.sql', encoding='utf-8') as f:
    connection.executescript(f.read())

connection.commit()
connection.close()

print("Database creato con successo!")
print("Ora puoi avviare il server con: python run.py")
