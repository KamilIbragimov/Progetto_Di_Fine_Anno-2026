# SchoolHRM

SchoolHRM è un'applicazione web per la **gestione di progetti scolastici** con
un sistema di feedback fra studenti e docenti, affiancata da una **dashboard
analitica** con un modello di Machine Learning.

L'ho realizzata come **due applicazioni distinte che condividono un unico
database**:

- una **web app Flask** per la parte transazionale (registrazione, login, CRUD
  progetti, iscrizioni, valutazioni);
- una **dashboard Streamlit** per la parte analitica (KPI, grafici, predizione
  AI, export CSV).

Le due app sono deployate separatamente ma leggono e scrivono lo **stesso
database PostgreSQL**, quindi i dati sono sempre coerenti senza alcuna
sincronizzazione manuale.

**Provala online:**

| Componente   | Indirizzo                                                                                   |
| ------------ | ------------------------------------------------------------------------------------------- |
| 🌐 Web app   | [https://schoolhrm.onrender.com](https://schoolhrm.onrender.com)                               |
| 📊 Dashboard | [https://progettodifineanno-2026.streamlit.app](https://progettodifineanno-2026.streamlit.app) |

Account demo già presenti nel database (oppure ci si registra dal sito):

| Ruolo    | Email               | Password  |
| -------- | ------------------- | --------- |
| Docente  | `rossi@school.it` | `rossi` |
| Studente | `luca@student.it` | `luca`  |

---

## Cosa si vede nell'applicazione

L'app gestisce tre ruoli: **visitatore**, **studente**, **docente**.

- **Visitatore** — home, elenco e dettaglio di tutti i progetti, registrazione
  e login.
- **Studente** — una dashboard personale con i propri progetti e progresso; può
  iscriversi a un progetto, aggiornare la percentuale di avanzamento, e
  **valutare** sia il progetto sia il docente (1–5 ★ + commento). Da qui apre
  anche la dashboard analitica.
- **Docente** — la propria area personale con i progetti creati, le statistiche
  e i contributori; gestione completa dei progetti (crea / modifica / elimina)
  e vista dei feedback ricevuti con le medie.

Il modello dati ha 4 entità: **utente** (studente o docente), **progetto**,
**iscrizione** (lega studente e progetto, con progresso e note) e **feedback**
(valutazione del progetto e del docente). Lo schema completo è in
`app/bomba.sql`; i diagrammi ER, UML e dei casi d'uso sono in `assets/`.

### La dashboard analitica

Parte da un repository esterno, **HRanalytics** (una dashboard Streamlit per
dati HR), che ho riadattato al dominio scolastico — ad esempio "promosso" è
diventato **sufficiente** (studente con progresso medio ≥ 60%). Invece di
lavorare su CSV esterni, legge in sola lettura lo stesso database della web app.
Ha 5 tab: **Riepilogo** (KPI e grafici), **Studenti**, **Docenti**,
**Predizione AI** (una Regressione Logistica scikit-learn che stima la
sufficienza di uno studente) ed **Esporta** (download CSV generati al volo).

---

## Tecnologie usate

- **Python 3.10+**
- **Flask** per la web app, **Streamlit** per la dashboard
- **Gunicorn** come server WSGI in produzione
- **PostgreSQL** (su Supabase) in produzione, **SQLite** in locale
- **psycopg2** (driver PostgreSQL), **python-dotenv** per le variabili d'ambiente
- **pandas / plotly / scikit-learn** per analitica e modello AI
- **pytest** per i test

Il codice è **dual-mode**: lo stesso identico sorgente gira in locale (SQLite)
e in produzione (PostgreSQL). A decidere è la variabile d'ambiente
`DATABASE_URL`: se assente usa SQLite, se presente usa PostgreSQL. Nessuna
modifica al codice fra i due ambienti.

L'architettura segue il **pattern repository**: i blueprint Flask non scrivono
mai SQL diretto, tutte le query sono incapsulate in `app/repositories/`.

---

## Dove è deployato

Tre componenti indipendenti, uniti dal database:

```
   ┌──────────────────────────┐     pulsante 📊      ┌────────────────────────────┐
   │  Web app Flask           │ ───────────────────► │  Dashboard Streamlit       │
   │  su RENDER (gunicorn)    │                      │  su STREAMLIT CLOUD        │
   │  schoolhrm.onrender.com  │                      │  ...streamlit.app          │
   └────────────┬─────────────┘                      └─────────────┬──────────────┘
                │  scrive / legge                       legge (sola lettura)
                └───────────────────┬───────────────────────────────┘
                                    ▼
                     ┌──────────────────────────────┐
                     │  PostgreSQL su SUPABASE       │
                     │  (database unico, persistente)│
                     └──────────────────────────────┘
```

- **Web app → Render.** Hosting del servizio Flask, avviato con
  `gunicorn run:app`. Si rideploia da solo a ogni `git push` sul branch `main`.
- **Database → Supabase.** PostgreSQL gestito. È la *single source of truth*: i
  dati vivono qui, non sul filesystem di Render, quindi sopravvivono a riavvii e
  redeploy.
- **Dashboard → Streamlit Community Cloud.** App Streamlit pubblica, collegata
  allo stesso database Supabase. Il pulsante "📊 Dashboard" nella web app
  reindirizza qui.

I segreti (`SECRET_KEY`, stringa di connessione al database) non sono nel
codice: stanno solo nelle variabili d'ambiente dei rispettivi pannelli (Render
e Streamlit) e, in locale, in un file `.env` escluso da Git.

---

## Struttura del progetto

```
.
├── app/                       # Web app Flask
│   ├── __init__.py            # application factory (create_app), config, filtri
│   ├── auth.py                # registrazione, login, logout, ruoli
│   ├── main.py                # home, lista e dettaglio progetti
│   ├── studenti.py            # area studente, valutazioni, launcher dashboard
│   ├── docenti.py             # area docente, CRUD progetti, feedback
│   ├── db.py                  # connessione DB dual-mode (SQLite / PostgreSQL)
│   ├── bomba.sql              # schema delle 4 tabelle + dati di esempio
│   ├── repositories/          # tutte le query SQL (pattern repository)
│   ├── templates/             # template Jinja2 (per blueprint)
│   └── static/                # CSS
│
├── dashboard/
│   ├── dashboard.py           # dashboard Streamlit (5 tab) — legge il DB in sola lettura
│   └── export_csv.py          # export CSV via CLI (complementare, opzionale)
│
├── assets/                    # diagrammi UML / ER / casi d'uso (.puml + .png)
│
├── run.py                     # entry point WSGI (python run.py | gunicorn run:app)
├── setup_db.py                # crea il database applicando bomba.sql
├── requirements.txt           # dipendenze Python
├── Procfile                   # comando di avvio per Render (gunicorn run:app)
├── Documento_dei_requisiti.md # analisi: requisiti, ER, UML, casi d'uso
└── README.md
```

---

## Avviare il progetto in locale

In locale gira con SQLite, senza bisogno di alcun account cloud.

```bash
git clone <repo-url>
cd Progetto_Di_Fine_Anno-2026

python -m venv .venv
.venv\Scripts\activate          # Windows ·  source .venv/bin/activate su Linux/macOS

pip install -r requirements.txt

python setup_db.py              # SOLO la prima volta: crea il database SQLite con i dati di esempio
python run.py                   # avvia la web app su http://127.0.0.1:5000
```

Per la dashboard analitica, in un altro terminale:

```bash
streamlit run dashboard/dashboard.py     # http://localhost:8501
```

In breve:

- Test: `python -m pytest -q`.
- Server di produzione in locale: `gunicorn run:app` (Linux/macOS) oppure
  `python -m waitress --listen=127.0.0.1:8000 run:app` (Windows, dove Gunicorn
  non è supportato).
- Per entrare: gli account demo in cima al README.

---

## Note operative

- I servizi gratuiti (Render, Streamlit Cloud) si sospendono dopo un periodo di
  inattività: il primo accesso può richiedere ~30 secondi per il "risveglio". I
  dati non si perdono mai, restano su Supabase.
- Aggiornare il progetto online significa solo fare `git push` su `main`:
  Render e Streamlit Cloud rideploiano in automatico.

---

## Documentazione e licenza

- **`Documento_dei_requisiti.md`** — analisi completa: requisiti funzionali e
  non funzionali, schema ER, diagramma delle classi, casi d'uso.
- **`assets/`** — sorgenti PlantUML (`.puml`) e immagini dei diagrammi.
- Licenza **MIT** (vedi `LICENSE`).
