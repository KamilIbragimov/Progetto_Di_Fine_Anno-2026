# SchoolHRM

Applicazione web per la gestione di progetti scolastici con sistema di feedback
fra studenti e docenti, completata da una **dashboard analitica** integrata.

Il progetto è composto da due tronconi:

1. **Web app Flask** — la parte transazionale (registrazione, login, CRUD progetti, iscrizioni, valutazioni)
2. **Dashboard Streamlit** — la parte analitica (KPI, grafici, predizione AI, export CSV)

Entrambi leggono dallo **stesso database SQLit** — nessuna sincronizzazione manuale.

---

## 1. Struttura del progetto

```
.
├── app/                          # Pacchetto Flask (web app)
│   ├── __init__.py               # application factory: create_app()
│   ├── auth.py                   # blueprint /auth — registra, login, logout, ruoli
│   ├── main.py                   # blueprint / — home, lista e dettaglio progetti
│   ├── studenti.py               # blueprint /studenti — iscrizione, progresso, valuta
│   ├── docenti.py                # blueprint /docenti — area personale, CRUD, feedback
│   ├── db.py                     # gestione connessione SQLite (get_db, close_db)
│   ├── bomba.sql                 # schema + seed iniziale del DB
│   ├── repositories/             # layer di accesso ai dati (pattern repository)
│   │   ├── utente_repository.py
│   │   ├── progetto_repository.py
│   │   ├── iscrizione_repository.py
│   │   └── feedback_repository.py
│   ├── templates/                # template Jinja2 organizzati per blueprint
│   │   ├── base.html
│   │   ├── index.html, 404.html
│   │   ├── auth/                 # login.html, register.html
│   │   ├── progetti/             # lista, dettaglio, crea, modifica
│   │   ├── studenti/             # dashboard, valuta
│   │   └── docenti/              # area_personale, feedback_ricevuti
│   └── static/                   # CSS
│
├── dashboard/                    # Dashboard analitica (separata dalla web app)
│   ├── dashboard.py              # app Streamlit (5 tab: KPI, studenti, docenti, AI, esporta)
│   └── export_csv.py             # script CLI per esportare gli stessi dati in CSV
│
├── assets/                       # Diagrammi UML (sorgenti .puml + immagini .png)
│   ├── usecase.puml / .png       # diagramma dei casi d'uso
│   ├── er.puml / .png            # schema ER
│   └── uml.puml / .png           # diagramma delle classi
│
├── exports/                      # cartella creata a runtime (gitignored)
│   ├── studenti_export.csv       # generati da python dashboard/export_csv.py
│   ├── docenti_export.csv
│   └── progetti_export.csv
│
├── instance/                     # cartella creata a runtime (gitignored)
│   └── schoolhrm.sqlite          # database SQLite — single source of truth
│
├── run.py                        # entry point Flask (python run.py)
├── setup_db.py                   # crea/ricrea il DB applicando bomba.sql
├── requirements.txt              # dipendenze Python
├── Procfile                      # configurazione Gunicorn per il deploy
├── usecase.puml                  # sorgente diagramma casi d'uso
├── Documento_dei_requisiti.md    # documento di analisi
└── README.md                     # questo file
```

### Cosa fa ciascun file

| File / cartella             | Ruolo                                                                                                                                                                    |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `app/__init__.py`         | Application factory: configura Flask, registra blueprint, gestisce 404/403                                                                                               |
| `app/auth.py`             | Registrazione, login, logout, hashing password (`werkzeug.security`), decorator `ruolo_required`                                                                     |
| `app/main.py`             | Route pubbliche: home, lista progetti, dettaglio progetto                                                                                                                |
| `app/studenti.py`         | Route protette per ruolo `studente`: dashboard personale, iscrizione, aggiornamento progresso, valutazione progetto + docente; lancia la dashboard Streamlit on-demand |
| `app/docenti.py`          | Route protette per ruolo `docente`: area personale, CRUD progetti, vista feedback ricevuti                                                                             |
| `app/db.py`               | Gestione del ciclo di vita della connessione SQLite per request                                                                                                          |
| `app/bomba.sql`           | DDL delle 4 tabelle (`utente`, `progetto`, `iscrizione`, `feedback`) + ~50 righe di seed                                                                         |
| `app/repositories/*.py`   | Funzioni che incapsulano tutte le query SQL — i blueprint non scrivono mai SQL direttamente                                                                             |
| `dashboard/dashboard.py`  | Streamlit app: legge il DB in sola lettura e mostra grafici, tabelle, modello AI                                                                                         |
| `dashboard/export_csv.py` | Versione CLI dell'export: genera 3 CSV nella cartella `exports/`                                                                                                       |
| `run.py`                  | Avvia il server di sviluppo Flask (`flask run` equivalente)                                                                                                            |
| `setup_db.py`             | Cancella `instance/schoolhrm.sqlite` se esiste e lo ricrea applicando `bomba.sql`                                                                                    |

---

## 2. La dashboard analitica

### Origine

Il layer analitico nasce da un repository esterno, **HRanalytics**, una dashboard
Streamlit pensata per dati di risorse umane (dipendenti, valutazioni, promozioni).
Per integrarlo in SchoolHRM ho fatto due adattamenti:

1. **Refactor del dominio**: i concetti HR sono stati rimappati in linguaggio scolastico:
   - "Promosso" → **Sufficiente** (studente con progresso medio ≥ 60%)
   - "Eccellente" (docente con valutazione media ≥ 4 ★) resta concettualmente analogo
2. **Connessione diretta al DB**: niente più CSV esterni — la dashboard apre
   `instance/schoolhrm.sqlite` in modalità read-only (`file:...?mode=ro`) e
   condivide la stessa fonte di dati della web app.

### Cosa mostra (`dashboard/dashboard.py`)

5 tab, tutti popolati live dal DB SQLite:

| Tab                       | Contenuto                                                                                                                                                                  |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 📊**Riepilogo**     | KPI principali, grafico a torta degli stati progetti, top 10 dei progetti più seguiti                                                                                     |
| 🎒**Studenti**      | Distribuzione del progresso, % sufficienti, classifica, tabella di dettaglio                                                                                               |
| 👨‍🏫**Docenti**   | Valutazione media per docente (stelle), distribuzione, tabella di dettaglio                                                                                                |
| 🤖**Predizione AI** | Regressione Logistica che predice se uno studente sarà "sufficiente" sulla base di `iscrizioni` e `completati`. Mostra accuratezza, coefficienti e feature importance |
| 📥**Esporta**       | Download diretto di `studenti_export.csv`, `docenti_export.csv`, `progetti_export.csv`                                                                               |

### Esportazione CLI (`dashboard/export_csv.py`)

Versione headless dell'export: stessi dati della dashboard, ma scritti su disco.
Utile per backup, analisi offline (Excel, R…) e condivisione dati senza esporre il DB.

Genera **3 file** nella cartella `exports/` (gitignored):

| File                    | Colonne                                                                                                 |
| ----------------------- | ------------------------------------------------------------------------------------------------------- |
| `studenti_export.csv` | id, nome, email, iscrizioni, completati, progresso_medio                                                |
| `docenti_export.csv`  | id, nome, email, progetti_creati, feedback_ricevuti, media_docente, media_progetto                      |
| `progetti_export.csv` | id, titolo, stato, docente, studenti_iscritti, progresso_medio, feedback_ricevuti, valutazione_progetto |

### Flusso completo

```
              ┌─────────────────────┐
              │  webapp Flask       │   (scrive)
              │  run.py             │
              └──────────┬──────────┘
                         ▼
              ┌─────────────────────┐
              │ schoolhrm.sqlite    │   ← single source of truth
              └──────────┬──────────┘
                         │ read-only
            ┌────────────┴────────────┐
            ▼                         ▼
   ┌──────────────────┐     ┌──────────────────┐
   │ dashboard.py     │     │ export_csv.py    │
   │ (Streamlit UI)   │     │ (CLI)            │
   └──────────────────┘     └────────┬─────────┘
                                     ▼
                            *_export.csv (3 file)
```

---

## 3. Come avviare il progetto (sviluppo locale)

> ⚠️ Questo tutorial è per l'**ambiente di sviluppo locale**.
> Quando il progetto sarà deployato (Gunicorn + Render + SUPABASE/postgresql),
> questa sezione andrà riscritta per riflettere il setup remoto.

### Prerequisiti

- Python 3.10+
- `pip`

### Passo 1 — Cloning e ambiente virtuale

```bash
git clone <repo-url>
cd Progetto_Di_Fine_Anno-2026

python -m venv .venv
.venv\Scripts\activate          # Windows (PowerShell)
# source .venv/bin/activate     # Linux/macOS
```

### Passo 2 — Installa le dipendenze

```bash
pip install -r requirements.txt
```

### Passo 3 — Crea il database

```bash
python setup_db.py
```

Lo script crea `instance/schoolhrm.sqlite` con lo schema e i dati di esempio
(5 docenti, 15 studenti, 15 progetti, 43 iscrizioni, 25 feedback).

Credenziali di default per i dati di seed:

- Tutti i **docenti** hanno password `rossi`
- Tutti gli **studenti** hanno password `luca`

### Passo 4 — Avvia la web app

```bash
python run.py
```

Apri `http://127.0.0.1:5000` e fai login con uno degli account seed,
oppure registra un nuovo utente.

### Passo 5 — Apri la dashboard analitica

**Opzione A — dalla webapp:** Fai login come studente e clicca "📊 Dashboard"
in alto a destra: Flask avvierà Streamlit in background sulla porta 8501 e
ti reindirizzerà.

**Opzione B — manualmente:**

```bash
streamlit run dashboard/dashboard.py
```

Apri `http://localhost:8501`.

### Passo 6 (opzionale) — Esporta i dati in CSV

```bash
python dashboard/export_csv.py
```

Genera 3 file `*_export.csv` nella cartella `exports/` (creata se non esiste).

### Test

```bash
python -m pytest tests/ -v
```

> La cartella `tests/` è gitignored (è una suite locale per verifica funzionale,
> non parte della consegna).
