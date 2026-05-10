import sqlite3
import csv
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))

DB_PATH  = os.path.join('instance', 'schoolhrm.sqlite')
CSV_PATH = 'hranalytics_export.csv'

if not os.path.exists(DB_PATH):
    print("Database non trovato. Esegui prima: python setup_db.py")
    sys.exit(1)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# ── Studenti ────────────────────────────────────────────────────────────────
# length_of_service  = numero progetti a cui è iscritto
# salary             = progresso medio (0-100, usato come punteggio produttività)
# no_of_trainings    = progetti completati al 100%
# previous_year_rating / performance_rating = progresso medio / 20  ->  scala 1-5
# promoted           = 1 se almeno un progetto al 100%
studenti = conn.execute('''
    SELECT
        u.id                                               AS employee_id,
        u.nome                                             AS name,
        'Studente'                                         AS department,
        COUNT(DISTINCT i.progetto_id)                      AS length_of_service,
        ROUND(COALESCE(AVG(i.progresso), 0), 1)           AS salary,
        COUNT(CASE WHEN i.progresso = 100 THEN 1 END)     AS no_of_trainings,
        ROUND(COALESCE(AVG(i.progresso) / 20.0, 0), 2)   AS previous_year_rating,
        ROUND(COALESCE(AVG(i.progresso) / 20.0, 0), 2)   AS performance_rating,
        CASE WHEN MAX(COALESCE(i.progresso, 0)) = 100
             THEN 1 ELSE 0 END                             AS promoted
    FROM utente u
    LEFT JOIN iscrizione i ON i.studente_id = u.id
    WHERE u.ruolo = 'studente'
    GROUP BY u.id
    ORDER BY u.id
''').fetchall()

# ── Docenti ─────────────────────────────────────────────────────────────────
# length_of_service  = numero progetti creati
# salary             = media stelle ricevute × 20  ->  scala 0-100
# no_of_trainings    = numero feedback ricevuti
# previous_year_rating / performance_rating = media stelle (1-5)
# promoted           = 1 se media stelle >= 4
docenti = conn.execute('''
    SELECT
        u.id                                               AS employee_id,
        u.nome                                             AS name,
        'Docente'                                          AS department,
        COUNT(DISTINCT p.id)                               AS length_of_service,
        ROUND(COALESCE(AVG(f.stelle) * 20.0, 0), 1)      AS salary,
        COUNT(DISTINCT f.id)                               AS no_of_trainings,
        ROUND(COALESCE(AVG(f.stelle), 0), 2)              AS previous_year_rating,
        ROUND(COALESCE(AVG(f.stelle), 0), 2)              AS performance_rating,
        CASE WHEN COALESCE(AVG(f.stelle), 0) >= 4
             THEN 1 ELSE 0 END                             AS promoted
    FROM utente u
    LEFT JOIN progetto p ON p.docente_id = u.id
    LEFT JOIN feedback f ON f.docente_id = u.id
    WHERE u.ruolo = 'docente'
    GROUP BY u.id
    ORDER BY u.id
''').fetchall()

conn.close()

rows = [dict(r) for r in list(studenti) + list(docenti)]

if not rows:
    print("Nessun utente trovato.")
    sys.exit(1)

fieldnames = [
    'employee_id', 'name', 'department',
    'length_of_service', 'salary',
    'no_of_trainings', 'previous_year_rating', 'performance_rating', 'promoted',
]

with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"File creato: {os.path.abspath(CSV_PATH)}")
print(f"Righe esportate: {len(rows)}")
print()
print("Mappatura colonne:")
print("  employee_id         -> ID utente (studente o docente)")
print("  department          -> ruolo (Studente / Docente)")
print("  length_of_service   -> n. progetti iscritti (studenti) / creati (docenti)")
print("  salary              -> progresso medio 0-100 (studenti) / stelle*20 (docenti)")
print("  no_of_trainings     -> progetti completati (studenti) / feedback ricevuti (docenti)")
print("  performance_rating  -> progresso/20 (studenti) / media stelle (docenti)")
print("  promoted            -> 1 se completato al 100% / media stelle >= 4")
print()
print("Come usare in HRanalytics:")
print("  1. cd Downloads\\HRanalytics-main\\HRanalytics-main")
print("  2. pip install streamlit pandas plotly seaborn scikit-learn")
print("  3. streamlit run app.py")
print("  4. Seleziona 'Upload Your Own Data' e carica:", CSV_PATH)
