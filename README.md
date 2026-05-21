# SchoolHRM

SchoolHRM è un'applicazione web per la **gestione di progetti scolastici** con un sistema di feedback fra studenti e docenti, affiancata da una **dashboard analitica** con un modello di Machine Learning.

L'ho realizzata come **due applicazioni distinte che condividono un unico database**:

- una **web app Flask** per la parte transazionale (registrazione, login, CRUD progetti, iscrizioni, valutazioni);
- una **dashboard Streamlit** per la parte analitica (KPI, grafici, predizione AI, export CSV).

**Provala online:**

| Componente   | Indirizzo                                                                                   |
| ------------ | ------------------------------------------------------------------------------------------- |
| 🌐 Web app   | [https://schoolhrm.onrender.com](https://schoolhrm.onrender.com)                               |
| 📊 Dashboard | [https://progettodifineanno-2026.streamlit.app](https://progettodifineanno-2026.streamlit.app) |

---

## Cosa si vede nell'applicazione

L'app gestisce tre ruoli: **visitatore**, **studente**, **docente**.

- **Visitatore** — home, elenco e dettaglio di tutti i progetti, registrazione e login.
- **Studente** — una dashboard personale con i propri progetti e progresso; può iscriversi a un progetto, aggiornare la percentuale di avanzamento, e **valutare** sia il progetto sia il docente (1–5 ★ + commento). Da qui apre anche la dashboard analitica.
- **Docente** — la propria area personale con i progetti creati, le statistiche e i contributori; gestione completa dei progetti (crea / modifica / elimina) e vista dei feedback ricevuti con le medie.

Il modello dati ha 4 entità: **utente** (studente o docente), **progetto**, **iscrizione** (lega studente e progetto, con progresso e note) e **feedback** (valutazione del progetto e del docente). Lo schema completo è in `app/bomba.sql`; i diagrammi ER, UML e dei casi d'uso sono in `assets/`.

### La dashboard analitica

Una dashboard Streamlit (adattata da un repository esterno HRanalytics) che legge in sola lettura lo stesso database della web app. Ha 5 tab:

- **Riepilogo** — KPI e grafici principali
- **Studenti** — analisi per studente
- **Docenti** — analisi per docente
- **Predizione AI** — Regressione Logistica che stima la sufficienza di uno studente (progresso medio ≥ 60%)
- **Esporta** — download CSV generati al volo

### Cos'è Streamlit?

Streamlit è una libreria Python che permette di creare applicazioni web interattive senza scrivere HTML, CSS o JavaScript. Trasforma uno script Python in un'app web con bottoni, slider, grafici e tabelle. Perfetto per dashboard, analisi dati e prototipazione veloce. Nel nostro caso, la dashboard analitica è un singolo file `dashboard.py` che Streamlit converte automaticamente in un'interfaccia interattiva.

---

## Tecnologie usate

- **Python 3.10+**
- **Flask** (web app), **Streamlit** (dashboard)
- **PostgreSQL** (Supabase in produzione), **SQLite** (locale)
- **pandas**, **plotly**, **scikit-learn** (analitica e modello AI)
- **pytest** (44 test automatici)

---

## SQLite vs PostgreSQL — qual è la differenza?

**SQLite**: un database **semplice**, memorizzato in un file locale (`instance/schoolhrm.sqlite`). Perfetto per lo sviluppo, ma **non è multiutente** — se due persone accedono contemporaneamente, ci sono conflitti.

**PostgreSQL**: un database **professionale** che gira su un server (Supabase nel nostro caso). Supporta **migliaia di utenti** simultanei e garantisce che i dati non vadano mai persi.

---

## Come funziona il dual-mode: lo stesso codice, due database diversi

L'app è scritta in modo che **il codice Python non cambia mai**, ma il database sì:

| Situazione | Cosa succede |
|-----------|-------------|
| **Sviluppo locale** (senza `DATABASE_URL`) | Usa SQLite (file locale) |
| **Produzione** (con `DATABASE_URL` settata) | Usa PostgreSQL (server remoto) |

### Il trucco: il file `app/db.py`

Questo file controlla quale database usare:

```python
def get_db():
    if 'db' not in g:
        url = _database_url()
        if url:                           # Se DATABASE_URL è settata
            g.db = _PgConnection(url)    # Usa PostgreSQL
        else:                            # Altrimenti
            g.db = sqlite3.connect(...)  # Usa SQLite
            g.db.row_factory = sqlite3.Row
            g.db.execute('PRAGMA foreign_keys = ON')
    return g.db
```

**Cosa succede**: ogni volta che l'app fa una query, chiama `get_db()` che decide automaticamente qual è il database giusto.

### Come rende PostgreSQL compatibile con SQLite

PostgreSQL e SQLite usano sintassi leggermente diversa. L'app ha un **wrapper** (`_PgConnection`) che traduce automaticamente:

```python
class _PgConnection:
    def execute(self, sql, params=()):
        cur = self._conn.cursor()
        cur.execute(sql.replace('?', '%s'), params)  # Converte ? in %s
        return cur
```

**Esempio concreto**:
- SQLite: `SELECT * FROM progetto WHERE id = ?`
- PostgreSQL: `SELECT * FROM progetto WHERE id = %s`

Il wrapper converte il `?` in `%s` al volo, così la stessa query funziona su entrambi i database.

### Gestione delle date

SQLite restituisce le date come **testo** (`"2026-05-21"`), PostgreSQL le restituisce come **oggetti datetime**. L'app ha un filtro che le formatta correttamente in entrambi i casi:

```python
def _fmt_data(value, fmt='%d/%m/%Y'):
    """Accetta sia testo che datetime, restituisce sempre formato '21/05/2026'."""
    if isinstance(value, str):
        value = datetime.fromisoformat(value)  # Converte testo → datetime
    return value.strftime(fmt)
```

Nei template: `{{ data_creazione | data }}` — funziona sempre, indipendentemente dal database.

---

## Dove è deployato

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

- **Web app** → Render (Flask + gunicorn)
- **Database** → Supabase (PostgreSQL gestito, *single source of truth*)
- **Dashboard** → Streamlit Community Cloud (legge lo stesso DB)

I segreti (`SECRET_KEY`, stringa di connessione) stanno solo nelle variabili d'ambiente, mai nel codice.

---

## Struttura del progetto

```
.
├── app/                       # Web app Flask
│   ├── __init__.py            # application factory, config dual-mode
│   ├── auth.py                # registrazione, login, autenticazione
│   ├── main.py                # home, lista e dettaglio progetti
│   ├── studenti.py            # area studente, valutazioni, launcher dashboard
│   ├── docenti.py             # area docente, CRUD progetti, feedback
│   ├── db.py                  # CUORE DEL DUAL-MODE: get_db(), _PgConnection wrapper
│   ├── bomba.sql              # schema e dati di esempio
│   ├── repositories/          # pattern repository: tutte le query SQL
│   ├── templates/             # template Jinja2 (con filtro |data)
│   └── static/                # CSS
│
├── dashboard/
│   ├── dashboard.py           # app Streamlit (5 tab)
│   └── export_csv.py          # export CSV (opzionale)
│
├── assets/                    # diagrammi (PlantUML + PNG)
├── run.py                     # entry point Flask
├── setup_db.py                # crea il database SQLite locale
├── requirements.txt           # dipendenze
├── Procfile                   # comando di avvio per Render
├── Documento_dei_requisiti.md # analisi: requisiti, ER, UML, casi d'uso
├── report.md                  # resoconto: difficoltà, lezioni, sviluppi futuri
└── README.md
```

---

## Come runnnare il progetto

### Setup iniziale (una sola volta)

```bash
git clone <repo-url>
cd Progetto_Di_Fine_Anno-2026

python -m venv .venv
.venv\Scripts\activate          # Windows

pip install -r requirements.txt
python setup_db.py              # crea il database SQLite locale
```

### Run in sviluppo (modo rapido)

**Terminale 1** — Web app (modo Flask debug, reload automatico):
```bash
python run.py
```
Vai su: `http://127.0.0.1:5000`

**Terminale 2** — Dashboard Streamlit:
```bash
streamlit run dashboard/dashboard.py
```
Vai su: `http://localhost:8501`

**Terminale 3** — Test:
```bash
python -m pytest -q
```

### Run in "produzione locale" (server simile a Render)

Se vuoi testare come gira il codice **esattamente** come in produzione (con Gunicorn in Linux o Waitress in Windows):

**Windows** (Waitress — equivalente locale di Gunicorn):
```bash
python -m waitress --listen=127.0.0.1:8000 run:app
```
Vai su: `http://127.0.0.1:8000`

**Linux/macOS** (Gunicorn — server di produzione):
```bash
gunicorn run:app
```
Vai su: `http://127.0.0.1:8000`

---

**Nota**: `python run.py` è **più veloce** per sviluppare (reload automatico). Waitress/Gunicorn sono per testare che il codice giri bene in produzione.

### ⚠️ ATTENZIONE: setup_db.py solo in locale

**IMPORTANTE**: `python setup_db.py` **NON** deve mai essere eseguito in produzione. Questo script fa `DROP TABLE` su tutti i dati — se eseguito con `DATABASE_URL` puntato a Supabase, **cancella completamente il database di produzione**. Va eseguito una sola volta in locale, al primo clone del progetto. In produzione, il database è già creato e non cambia mai via script; gli aggiornamenti avvengono tramite `git push` e redeploy.

---

## Moduli della dashboard — cosa fanno gli import

Il file `dashboard.py` importa:

- **`os`** — accede alle variabili d'ambiente (es. `DATABASE_URL`) e al filesystem
- **`sqlite3`** — driver per connessione al database SQLite (modalità locale)
- **`pandas`** — carica e manipola i dati in tabelle (DataFrame)
- **`plotly.express`** — crea grafici interattivi (linee, barre, scatter, ecc.)
- **`streamlit`** — libreria che trasforma lo script Python in un'app web interattiva
- **`dotenv.load_dotenv()`** — carica le variabili d'ambiente dal file `.env`
- **`LogisticRegression`** (scikit-learn) — modello di Machine Learning che predice se uno studente avrà successo (sufficienza sì/no)
- **`accuracy_score`** (scikit-learn) — calcola la precisione del modello sui dati di test
- **`train_test_split`** (scikit-learn) — divide i dati in set di training (insegna al modello) e test (verifica la precisione)

---

## Note operative

- I servizi gratuiti si sospendono dopo inattività: il primo accesso può richiedere ~30 secondi.
- Aggiornare il progetto online significa solo fare `git push` su `main`.

---

## Documentazione

- **`Documento_dei_requisiti.md`** — analisi completa: requisiti, schema ER, diagramma delle classi, casi d'uso
- **`report.md`** — resoconto dettagliato del lavoro svolto, difficoltà risolte, lezioni apprese
- **`assets/`** — sorgenti PlantUML e immagini dei diagrammi
- Licenza: **MIT**
