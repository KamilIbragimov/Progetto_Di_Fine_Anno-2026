"""Esporta i dati di SchoolHRM in tre CSV (studenti, docenti, progetti).
Utile per analisi offline o backup, complementare alla dashboard Streamlit.

Dual-mode come la dashboard: se `DATABASE_URL` è settata legge da PostgreSQL
(Supabase), altrimenti dal file SQLite locale. Stessa fonte dati della web app.

Uso (dalla radice del progetto):
    python dashboard/export_csv.py

I file vengono scritti nella cartella exports/ (creata se non esiste).
"""
import sqlite3
import csv
import os
import sys

from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORT_DIR   = os.path.join(PROJECT_ROOT, 'exports')
DB_PATH      = os.path.join(PROJECT_ROOT, 'instance', 'schoolhrm.sqlite')

load_dotenv(os.path.join(PROJECT_ROOT, '.env'))
DATABASE_URL = os.environ.get('DATABASE_URL')

os.makedirs(EXPORT_DIR, exist_ok=True)


def fetch_rows(query):
    """Esegue la query e ritorna liste di dict, indipendentemente dal motore."""
    if DATABASE_URL:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        cur.execute(query)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
    if not os.path.exists(DB_PATH):
        print("Database SQLite non trovato. Esegui prima: python setup_db.py")
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute(query).fetchall()]
    conn.close()
    return rows


QUERIES = {
    'studenti_export.csv': '''
        SELECT
            u.id, u.nome, u.email,
            COUNT(DISTINCT i.progetto_id)                  AS iscrizioni,
            COUNT(CASE WHEN i.progresso = 100 THEN 1 END)  AS completati,
            CAST(ROUND(COALESCE(AVG(i.progresso), 0), 1) AS FLOAT) AS progresso_medio
        FROM utente u
        LEFT JOIN iscrizione i ON i.studente_id = u.id
        WHERE u.ruolo = 'studente'
        GROUP BY u.id, u.nome, u.email ORDER BY u.id
    ''',
    'docenti_export.csv': '''
        SELECT
            u.id, u.nome, u.email,
            COUNT(DISTINCT p.id)                            AS progetti_creati,
            COUNT(DISTINCT f.id)                            AS feedback_ricevuti,
            CAST(ROUND(COALESCE(AVG(f.stelle_docente), 0), 2) AS FLOAT)  AS media_docente,
            CAST(ROUND(COALESCE(AVG(f.stelle_progetto), 0), 2) AS FLOAT) AS media_progetto
        FROM utente u
        LEFT JOIN progetto p ON p.docente_id = u.id
        LEFT JOIN feedback f ON f.docente_id = u.id
        WHERE u.ruolo = 'docente'
        GROUP BY u.id, u.nome, u.email ORDER BY u.id
    ''',
    'progetti_export.csv': '''
        SELECT
            p.id, p.titolo, p.stato, u.nome AS docente,
            COUNT(DISTINCT i.studente_id)                   AS studenti_iscritti,
            CAST(ROUND(COALESCE(AVG(i.progresso), 0), 1) AS FLOAT) AS progresso_medio,
            COUNT(DISTINCT f.id)                            AS feedback_ricevuti,
            CAST(ROUND(COALESCE(AVG(f.stelle_progetto), 0), 2) AS FLOAT) AS valutazione_progetto
        FROM progetto p
        JOIN utente u ON u.id = p.docente_id
        LEFT JOIN iscrizione i ON i.progetto_id = p.id
        LEFT JOIN feedback f ON f.progetto_id = p.id
        GROUP BY p.id, p.titolo, p.stato, u.nome ORDER BY p.id
    ''',
}

for filename, query in QUERIES.items():
    rows = fetch_rows(query)
    if not rows:
        print(f"Nessun dato per {filename}, salto.")
        continue
    fieldnames = list(rows[0].keys())
    out_path   = os.path.join(EXPORT_DIR, filename)
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"exports/{filename}: {len(rows)} righe esportate")

print("\nEsportazione completata.")
