"""Esporta i dati di SchoolHRM in tre CSV (studenti, docenti, progetti).
Utile per analisi offline o backup, complementare alla dashboard Streamlit.

Uso (dalla radice del progetto):
    python dashboard/export_csv.py

I file vengono scritti nella cartella exports/ (creata se non esiste).
"""
import sqlite3
import csv
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORT_DIR   = os.path.join(PROJECT_ROOT, 'exports')
DB_PATH      = os.path.join(PROJECT_ROOT, 'instance', 'schoolhrm.sqlite')

os.makedirs(EXPORT_DIR, exist_ok=True)

if not os.path.exists(DB_PATH):
    print("Database non trovato. Esegui prima: python setup_db.py")
    sys.exit(1)


QUERIES = {
    'studenti_export.csv': '''
        SELECT
            u.id, u.nome, u.email,
            COUNT(DISTINCT i.progetto_id)                  AS iscrizioni,
            COUNT(CASE WHEN i.progresso = 100 THEN 1 END)  AS completati,
            ROUND(COALESCE(AVG(i.progresso), 0), 1)        AS progresso_medio
        FROM utente u
        LEFT JOIN iscrizione i ON i.studente_id = u.id
        WHERE u.ruolo = 'studente'
        GROUP BY u.id ORDER BY u.id
    ''',
    'docenti_export.csv': '''
        SELECT
            u.id, u.nome, u.email,
            COUNT(DISTINCT p.id)                            AS progetti_creati,
            COUNT(DISTINCT f.id)                            AS feedback_ricevuti,
            ROUND(COALESCE(AVG(f.stelle_docente), 0), 2)    AS media_docente,
            ROUND(COALESCE(AVG(f.stelle_progetto), 0), 2)   AS media_progetto
        FROM utente u
        LEFT JOIN progetto p ON p.docente_id = u.id
        LEFT JOIN feedback f ON f.docente_id = u.id
        WHERE u.ruolo = 'docente'
        GROUP BY u.id ORDER BY u.id
    ''',
    'progetti_export.csv': '''
        SELECT
            p.id, p.titolo, p.stato, u.nome AS docente,
            COUNT(DISTINCT i.studente_id)                   AS studenti_iscritti,
            ROUND(COALESCE(AVG(i.progresso), 0), 1)         AS progresso_medio,
            COUNT(DISTINCT f.id)                            AS feedback_ricevuti,
            ROUND(COALESCE(AVG(f.stelle_progetto), 0), 2)   AS valutazione_progetto
        FROM progetto p
        JOIN utente u ON u.id = p.docente_id
        LEFT JOIN iscrizione i ON i.progetto_id = p.id
        LEFT JOIN feedback f ON f.progetto_id = p.id
        GROUP BY p.id ORDER BY p.id
    ''',
}

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

for filename, query in QUERIES.items():
    rows = conn.execute(query).fetchall()
    if not rows:
        print(f"Nessun dato per {filename}, salto.")
        continue
    fieldnames = list(rows[0].keys())
    out_path   = os.path.join(EXPORT_DIR, filename)
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(dict(r) for r in rows)
    print(f"exports/{filename}: {len(rows)} righe esportate")

conn.close()
print("\nEsportazione completata.")
