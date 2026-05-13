# SchoolHRM — Layer Analytics

Questo README documenta la parte **analitica** del progetto SchoolHRM:
da dove arriva, come si avvia la dashboard, e quali dati produce.

---

## 1. Origine: il repository HRanalytics

Il layer di analytics nasce da un repository esterno chiamato **HRanalytics**,
una dashboard scritta in Streamlit per analizzare dati di risorse umane
(dipendenti, anzianità di servizio, valutazioni, promozioni).

Per integrarlo in SchoolHRM ho fatto due passi:

1. **Refactor del dominio**: i dati HR (employee, salary, promotion…) sono stati
   sostituiti con i dati scolastici del progetto (studente, docente, progetto, feedback).
   Le metriche sono state riformulate nel linguaggio della scuola:
   - "Promosso" → **Sufficiente** (studente con progresso medio ≥ 60%)
   - "Eccellente" (docente con valutazione media ≥ 4 ★) resta concettualmente analogo
2. **Connessione diretta al DB**: la dashboard non legge più CSV esterni —
   si connette in sola lettura al file `instance/schoolhrm.sqlite` condiviso
   con la web app Flask. Niente duplicazione di dati, niente import manuale.

---

## 2. `app.py` — Dashboard Streamlit

Single-page app costruita con Streamlit + Plotly + scikit-learn.
Si avvia da terminale oppure cliccando il pulsante "📊 Dashboard" nella
navbar della webapp (lo studente loggato apre `/studenti/launch-dashboard`,
che la accende in background sulla porta 8501).

### Avvio manuale

```bash
streamlit run app.py
```

La dashboard apre su `http://localhost:8501`.

### Cosa mostra

5 tab, tutti popolati live dal DB SQLite:

| Tab                       | Contenuto                                                                                                                                                                                  |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 📊**Riepilogo**     | KPI principali (n. studenti/docenti/progetti, % sufficienti, % eccellenti, progresso medio, valutazione media), grafico a torta dello stato dei progetti, top 10 dei progetti più seguiti |
| 🎒**Studenti**      | Distribuzione del progresso, % sufficienti, classifica per progresso, iscrizioni e progetti completati per studente, tabella di dettaglio                                                  |
| 👨‍🏫**Docenti**   | Valutazione media per docente (stelle), distribuzione delle valutazioni, n. progetti per docente, tabella di dettaglio                                                                     |
| 🤖**Predizione AI** | Modello di Regressione Logistica che predice se uno studente sarà "sufficiente" sulla base di `iscrizioni` e `completati`. Mostra accuratezza, coefficienti e feature importance      |
| 📥**Esporta**       | Download CSV (studenti, docenti, progetti) direttamente dalla UI                                                                                                                           |

### Pattern tecnici

- **Connessione read-only**: `sqlite3.connect(f'file:{DB_PATH}?mode=ro', uri=True)` per evitare race condition (TOCTOU) tra il check di esistenza e l'apertura del file
- **Refresh manuale + auto**: pulsante "🔄 Aggiorna dati" e checkbox per refresh ogni 10 s
- **No caching**: le query SQL girano a ogni rerun → la dashboard riflette sempre lo stato reale del DB

---

## 3. `export_csv.py` — Esportazione da CLI

Script da terminale che esporta lo stesso set di dati della dashboard,
ma in formato CSV su disco. Utile per:

- backup periodici
- analisi offline (Excel, R, Tableau…)
- condivisione dei dati senza esporre il DB

### Avvio

```bash
python export_csv.py
```

Genera **tre file** nella radice del progetto:

```
studenti_export.csv
docenti_export.csv
progetti_export.csv
```

Lo script:

1. apre `instance/schoolhrm.sqlite` (errore se il DB non esiste)
2. esegue 3 query aggregate (una per entità)
3. scrive ogni risultato come CSV UTF-8 con header

I file sono in `.gitignore` (`*_export.csv`) → non vengono pushati su GitHub.

---

## 4. Schema dei CSV esportati

### `studenti_export.csv`

| Colonna             | Tipo   | Significato                                      |
| ------------------- | ------ | ------------------------------------------------ |
| `id`              | int    | ID utente                                        |
| `nome`            | string | Nome completo                                    |
| `email`           | string | Email (univoca)                                  |
| `iscrizioni`      | int    | Numero di progetti a cui lo studente è iscritto |
| `completati`      | int    | Progetti portati al 100% di progresso            |
| `progresso_medio` | float  | Progresso medio su tutti i progetti (0–100)     |

### `docenti_export.csv`

| Colonna               | Tipo   | Significato                                  |
| --------------------- | ------ | -------------------------------------------- |
| `id`                | int    | ID utente                                    |
| `nome`              | string | Nome completo                                |
| `email`             | string | Email (univoca)                              |
| `progetti_creati`   | int    | Numero di progetti gestiti dal docente       |
| `feedback_ricevuti` | int    | Totale feedback degli studenti               |
| `media_docente`     | float  | Media stelle ricevute dal docente (1–5)     |
| `media_progetto`    | float  | Media stelle dei progetti del docente (1–5) |

### `progetti_export.csv`

| Colonna                  | Tipo   | Significato                                   |
| ------------------------ | ------ | --------------------------------------------- |
| `id`                   | int    | ID progetto                                   |
| `titolo`               | string | Titolo                                        |
| `stato`                | string | `disponibile`, `in_corso`, `completato` |
| `docente`              | string | Nome del docente responsabile                 |
| `studenti_iscritti`    | int    | Numero di iscritti al progetto                |
| `progresso_medio`      | float  | Avanzamento medio degli iscritti (0–100)     |
| `feedback_ricevuti`    | int    | Totale valutazioni ricevute                   |
| `valutazione_progetto` | float  | Media stelle del progetto (1–5)              |

---

## 5. Flusso completo

```
              ┌─────────────────────┐
              │  webapp Flask       │  (CRUD progetti, iscrizioni, feedback)
              │  run.py             │
              └──────────┬──────────┘
                         │ scrive
                         ▼
              ┌─────────────────────┐
              │ schoolhrm.sqlite    │  ← unica fonte di verità
              └──────────┬──────────┘
                         │ legge (read-only)
            ┌────────────┴────────────┐
            ▼                         ▼
   ┌──────────────────┐     ┌──────────────────┐
   │ app.py           │     │ export_csv.py    │
   │ (Streamlit)      │     │ (CLI)            │
   └──────────────────┘     └────────┬─────────┘
                                     ▼
                            *_export.csv (3 file)
```

Tre componenti, **una sola sorgente di dati**: il DB SQLite scritto dalla webapp.
Niente sincronizzazioni manuali, niente snapshot da rinfrescare.
