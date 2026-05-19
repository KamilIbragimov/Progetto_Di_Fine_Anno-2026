# Report di avanzamento — SchoolHRM

Resoconto del lavoro svolto sul progetto: cosa è stato realizzato, le scelte
prese, le difficoltà incontrate e come sono state risolte.

---

## 1. Stato del progetto

**Completato e in produzione.** L'applicazione è online, funzionante e
verificata end-to-end:

- Web app Flask: <https://schoolhrm.onrender.com>
- Dashboard Streamlit: <https://progettodifineanno-2026.streamlit.app>
- Database PostgreSQL persistente su Supabase, condiviso dalle due app
- 44 test automatici, tutti verdi

L'obiettivo iniziale (gestione progetti scolastici + analitica) è stato
raggiunto, e il progetto è stato portato fino al deploy reale in produzione.

---

## 2. Fasi svolte

1. **Analisi e progettazione.** Documento dei requisiti, schema ER, diagramma
   delle classi e casi d'uso (PlantUML). Più iterazioni sui casi d'uso per
   modellare correttamente le relazioni *extend* / *include* (es. "Valuta
   progetto").
2. **Web app Flask.** Application factory, blueprint per ruolo (auth, main,
   studenti, docenti), pattern repository per isolare l'SQL, autenticazione con
   hashing delle password e controllo dei ruoli.
3. **Funzionalità di dominio.** CRUD progetti, iscrizioni con progresso,
   sistema di feedback con valutazione separata di **progetto** e **docente**.
4. **Dashboard analitica.** Integrazione e riadattamento del repository esterno
   HRanalytics dal dominio HR a quello scolastico, con un modello di
   Regressione Logistica per predire la "sufficienza" degli studenti.
5. **Qualità del codice.** Lavoro mirato su coerenza, semplicità e ordine:
   pulizia di codice morto, commenti utili, struttura ordinata, separazione
   netta della dashboard dalla web app.
6. **Testing.** Suite pytest (44 test) sulla logica della web app.
7. **Messa in produzione.** Trasformazione da progetto di solo sviluppo a
   progetto deployato: database cloud, server WSGI, hosting.

---

## 3. Cosa siamo riusciti a fare

- Un'applicazione **completa e usabile** con tre ruoli (visitatore, studente,
  docente) e tutte le funzionalità previste.
- Una **dashboard analitica integrata** con grafici e un modello di Machine
  Learning, che legge gli stessi dati reali della web app.
- Un **codice dual-mode** unico: gira identico in locale (SQLite) e in
  produzione (PostgreSQL), senza alcuna modifica al sorgente — controllato solo
  da una variabile d'ambiente.
- Un **deploy reale e distribuito**: due applicazioni separate (Render e
  Streamlit Cloud) unite da un unico database cloud (Supabase), con persistenza
  dei dati verificata (un utente registrato dal sito sopravvive a riavvii e
  redeploy).
- **Gestione corretta dei segreti**: chiavi e stringa di connessione solo in
  variabili d'ambiente, mai nel codice o su GitHub.
- Documentazione coerente: README descrittivo + Documento dei requisiti +
  diagrammi.

---

## 4. Cosa è stato difficile (e come è stato risolto)

### Modellazione dei casi d'uso
Le relazioni *extend*/*include* fra i casi d'uso hanno richiesto diverse
revisioni, sia logiche sia di leggibilità del diagramma. Risolto iterando sul
file PlantUML e mantenendo allineati diagramma, documento e codice.

### Migrazione dello schema dei voti
Il passaggio da un singolo voto a **due voti distinti** (`stelle_docente` e
`stelle_progetto`) ha toccato database, repository, route e template tutti
insieme. Risolto propagando la modifica in modo coerente su ogni layer e
verificando con i test.

### Rendere il codice compatibile con PostgreSQL senza riscriverlo
Il problema più grosso del deploy. La web app era scritta per SQLite. Invece di
riscrivere tutti i repository, è stato creato un piccolo wrapper che fa parlare
`psycopg2` con la stessa interfaccia di `sqlite3` (conversione automatica dei
placeholder `?` → `%s`, righe accessibili allo stesso modo). Così i repository
sono rimasti **invariati**.

### Differenze di dialetto SQL fra SQLite e PostgreSQL
Diversi punti rompevano su PostgreSQL e sono stati resi portabili:
- `INSERT OR IGNORE` (solo SQLite) → `ON CONFLICT DO NOTHING`
- `GROUP BY` con colonne non aggregate (tollerato da SQLite, rifiutato da
  PostgreSQL) → aggiunte tutte le colonne necessarie
- `ROUND()` che su PostgreSQL restituisce `Decimal` e rompeva i calcoli di
  pandas → `CAST(... AS FLOAT)`
- `INTEGER PRIMARY KEY AUTOINCREMENT` → `SERIAL PRIMARY KEY` (tradotto al volo)
- date come stringa (SQLite) vs oggetto datetime (PostgreSQL) → filtro Jinja
  dedicato

### Gunicorn non funziona su Windows
Gunicorn dipende da un modulo solo-Unix (`fcntl`): impossibile testarlo in
locale su Windows. Risolto usando **waitress** come equivalente per il test
locale, tenendo Gunicorn per la produzione su Render (Linux).

### Il pulsante "Dashboard" non funzionava in produzione
In locale la web app lanciava Streamlit come processo figlio e rimandava a
`localhost:8501`. Su Render questo è impossibile: un solo servizio, una sola
porta, e `localhost` punta al PC dell'utente. Risolto **deployando la dashboard
separatamente** su Streamlit Community Cloud e facendo sì che il pulsante, in
produzione, reindirizzi all'URL pubblico (gestito da una variabile
d'ambiente). Il codice resta dual-mode: in locale comportamento invariato.

### Configurazione cloud poco intuitiva
Diversi ostacoli pratici nel deploy:
- **Supabase**: scegliere la connection string giusta — la "Direct connection"
  è IPv6 e Render free non la supporta; serviva la "Session pooler" (IPv4).
- **Streamlit Cloud**: i segreti non sono variabili d'ambiente ma un sistema
  proprio in formato TOML (`chiave = "valore"`), che ha richiesto un piccolo
  adattamento al codice della dashboard.
- Allineare la stessa stringa di connessione in tre posti (locale, Render,
  Streamlit) senza errori.

### Dati di esempio non affidabili come fonte
I conteggi dei dati di seed inizialmente riportati erano sbagliati perché letti
da un database locale "sporcato" dai test. Corretti prendendo i numeri
direttamente dal database appena creato (fonte autoritativa).

### Gestione dei segreti
La stringa di connessione (con password) è stata esposta per errore in uno
screenshot durante la configurazione. È servito come promemoria concreto sul
perché i segreti vanno trattati con attenzione; la procedura di rotazione è
documentata anche se non applicata.

---

## 5. Lezioni apprese

- Progettare per la portabilità **prima** di scrivere il codice costa meno che
  adattarlo dopo: gran parte del lavoro di deploy è stato sistemare differenze
  di dialetto SQL emerse solo a posteriori.
- Un piccolo strato di astrazione (il wrapper della connessione) può evitare di
  riscrivere intere parti di codice.
- "Funziona in locale" non implica "funziona in produzione": ambiente,
  filesystem, porte e rete cambiano le regole (Gunicorn, il pulsante dashboard,
  IPv6 vs IPv4).
- I segreti vanno gestiti con disciplina dal primo minuto.

---

## 6. Possibili sviluppi futuri

- Rotazione della password del database e gestione segreti più rigorosa.
- Migrazioni di schema versionate invece del `DROP/CREATE` di `bomba.sql`.
- Estensione della suite di test anche alla parte analitica.
- Eventuale dominio personalizzato e piano a pagamento per eliminare il
  "risveglio" dei servizi gratuiti.
