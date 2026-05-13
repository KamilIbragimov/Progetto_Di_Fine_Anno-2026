DROP TABLE IF EXISTS feedback;
DROP TABLE IF EXISTS iscrizione;
DROP TABLE IF EXISTS progetto;
DROP TABLE IF EXISTS utente;

CREATE TABLE utente (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nome          TEXT NOT NULL,
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    ruolo         TEXT NOT NULL CHECK (ruolo IN ('studente', 'docente')),
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE progetto (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    titolo      TEXT NOT NULL,
    descrizione TEXT,
    stato       TEXT NOT NULL DEFAULT 'disponibile'
                     CHECK (stato IN ('disponibile', 'in_corso', 'completato')),
    docente_id  INTEGER NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (docente_id) REFERENCES utente(id) ON DELETE CASCADE
);

CREATE TABLE iscrizione (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    studente_id INTEGER NOT NULL,
    progetto_id INTEGER NOT NULL,
    progresso   INTEGER NOT NULL DEFAULT 0 CHECK (progresso BETWEEN 0 AND 100),
    note        TEXT,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (studente_id, progetto_id),
    FOREIGN KEY (studente_id) REFERENCES utente(id) ON DELETE CASCADE,
    FOREIGN KEY (progetto_id) REFERENCES progetto(id) ON DELETE CASCADE
);

CREATE TABLE feedback (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    studente_id    INTEGER NOT NULL,
    docente_id     INTEGER NOT NULL,
    progetto_id    INTEGER NOT NULL,
    stelle_docente INTEGER NOT NULL CHECK (stelle_docente BETWEEN 1 AND 5),
    stelle_progetto INTEGER NOT NULL CHECK (stelle_progetto BETWEEN 1 AND 5),
    commento       TEXT,
    created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (studente_id, progetto_id),
    FOREIGN KEY (studente_id) REFERENCES utente(id) ON DELETE CASCADE,
    FOREIGN KEY (docente_id)  REFERENCES utente(id) ON DELETE CASCADE,
    FOREIGN KEY (progetto_id) REFERENCES progetto(id) ON DELETE CASCADE
);

/* ── SEED DATA ──
   Tutti i docenti hanno password "rossi"
   Tutti gli studenti hanno password "luca"
*/

/* ── DOCENTI (id 1..5) ── */
INSERT INTO utente (nome, email, password_hash, ruolo) VALUES
('Prof. Marco Rossi',     'rossi@school.it',    'scrypt:32768:8:1$K7AF6IMoTkq83YJR$0c44a5f4507174668c6d3851e3ec105690ef878a70c265c08f7a3faafa43183b81702af3c407695d966d00058523f99bfb590e1b087a66b21fae02b7ffd3e87c', 'docente'),
('Prof.ssa Anna Bianchi', 'bianchi@school.it',  'scrypt:32768:8:1$K7AF6IMoTkq83YJR$0c44a5f4507174668c6d3851e3ec105690ef878a70c265c08f7a3faafa43183b81702af3c407695d966d00058523f99bfb590e1b087a66b21fae02b7ffd3e87c', 'docente'),
('Prof. Luigi Verdi',     'verdi@school.it',    'scrypt:32768:8:1$K7AF6IMoTkq83YJR$0c44a5f4507174668c6d3851e3ec105690ef878a70c265c08f7a3faafa43183b81702af3c407695d966d00058523f99bfb590e1b087a66b21fae02b7ffd3e87c', 'docente'),
('Prof.ssa Giulia Romano','romano@school.it',   'scrypt:32768:8:1$K7AF6IMoTkq83YJR$0c44a5f4507174668c6d3851e3ec105690ef878a70c265c08f7a3faafa43183b81702af3c407695d966d00058523f99bfb590e1b087a66b21fae02b7ffd3e87c', 'docente'),
('Prof. Andrea Galli',    'galli@school.it',    'scrypt:32768:8:1$K7AF6IMoTkq83YJR$0c44a5f4507174668c6d3851e3ec105690ef878a70c265c08f7a3faafa43183b81702af3c407695d966d00058523f99bfb590e1b087a66b21fae02b7ffd3e87c', 'docente');

/* ── STUDENTI (id 6..20) ── */
INSERT INTO utente (nome, email, password_hash, ruolo) VALUES
('Luca Ferrari',        'luca@student.it',      'scrypt:32768:8:1$7mpX6yIfyNeYjU56$e228d025a286d68c9379a3c819f6317e3963257d0eaf064ab25e291f675d14d6594255ee5122b064411a5687f4dae985b4d1551f0c3166c400e53698d378ef09', 'studente'),
('Sofia Esposito',      'sofia@student.it',     'scrypt:32768:8:1$7mpX6yIfyNeYjU56$e228d025a286d68c9379a3c819f6317e3963257d0eaf064ab25e291f675d14d6594255ee5122b064411a5687f4dae985b4d1551f0c3166c400e53698d378ef09', 'studente'),
('Marco Ricci',         'marco@student.it',     'scrypt:32768:8:1$7mpX6yIfyNeYjU56$e228d025a286d68c9379a3c819f6317e3963257d0eaf064ab25e291f675d14d6594255ee5122b064411a5687f4dae985b4d1551f0c3166c400e53698d378ef09', 'studente'),
('Elena Conti',         'elena@student.it',     'scrypt:32768:8:1$7mpX6yIfyNeYjU56$e228d025a286d68c9379a3c819f6317e3963257d0eaf064ab25e291f675d14d6594255ee5122b064411a5687f4dae985b4d1551f0c3166c400e53698d378ef09', 'studente'),
('Giovanni Marino',     'giovanni@student.it',  'scrypt:32768:8:1$7mpX6yIfyNeYjU56$e228d025a286d68c9379a3c819f6317e3963257d0eaf064ab25e291f675d14d6594255ee5122b064411a5687f4dae985b4d1551f0c3166c400e53698d378ef09', 'studente'),
('Chiara Galli',        'chiara@student.it',    'scrypt:32768:8:1$7mpX6yIfyNeYjU56$e228d025a286d68c9379a3c819f6317e3963257d0eaf064ab25e291f675d14d6594255ee5122b064411a5687f4dae985b4d1551f0c3166c400e53698d378ef09', 'studente'),
('Francesco Lombardi',  'francesco@student.it', 'scrypt:32768:8:1$7mpX6yIfyNeYjU56$e228d025a286d68c9379a3c819f6317e3963257d0eaf064ab25e291f675d14d6594255ee5122b064411a5687f4dae985b4d1551f0c3166c400e53698d378ef09', 'studente'),
('Martina De Luca',     'martina@student.it',   'scrypt:32768:8:1$7mpX6yIfyNeYjU56$e228d025a286d68c9379a3c819f6317e3963257d0eaf064ab25e291f675d14d6594255ee5122b064411a5687f4dae985b4d1551f0c3166c400e53698d378ef09', 'studente'),
('Alessandro Greco',    'alessandro@student.it','scrypt:32768:8:1$7mpX6yIfyNeYjU56$e228d025a286d68c9379a3c819f6317e3963257d0eaf064ab25e291f675d14d6594255ee5122b064411a5687f4dae985b4d1551f0c3166c400e53698d378ef09', 'studente'),
('Valentina Costa',     'valentina@student.it', 'scrypt:32768:8:1$7mpX6yIfyNeYjU56$e228d025a286d68c9379a3c819f6317e3963257d0eaf064ab25e291f675d14d6594255ee5122b064411a5687f4dae985b4d1551f0c3166c400e53698d378ef09', 'studente'),
('Davide Russo',        'davide@student.it',    'scrypt:32768:8:1$7mpX6yIfyNeYjU56$e228d025a286d68c9379a3c819f6317e3963257d0eaf064ab25e291f675d14d6594255ee5122b064411a5687f4dae985b4d1551f0c3166c400e53698d378ef09', 'studente'),
('Federica Marino',     'federica@student.it',  'scrypt:32768:8:1$7mpX6yIfyNeYjU56$e228d025a286d68c9379a3c819f6317e3963257d0eaf064ab25e291f675d14d6594255ee5122b064411a5687f4dae985b4d1551f0c3166c400e53698d378ef09', 'studente'),
('Matteo Barbieri',     'matteo@student.it',    'scrypt:32768:8:1$7mpX6yIfyNeYjU56$e228d025a286d68c9379a3c819f6317e3963257d0eaf064ab25e291f675d14d6594255ee5122b064411a5687f4dae985b4d1551f0c3166c400e53698d378ef09', 'studente'),
('Giulia Fontana',      'giuliaf@student.it',   'scrypt:32768:8:1$7mpX6yIfyNeYjU56$e228d025a286d68c9379a3c819f6317e3963257d0eaf064ab25e291f675d14d6594255ee5122b064411a5687f4dae985b4d1551f0c3166c400e53698d378ef09', 'studente'),
('Riccardo Bruno',      'riccardo@student.it',  'scrypt:32768:8:1$7mpX6yIfyNeYjU56$e228d025a286d68c9379a3c819f6317e3963257d0eaf064ab25e291f675d14d6594255ee5122b064411a5687f4dae985b4d1551f0c3166c400e53698d378ef09', 'studente');

/* ── PROGETTI (id 1..15) ── */
INSERT INTO progetto (titolo, descrizione, stato, docente_id) VALUES
('Introduzione agli Algoritmi',
 'Fondamenti di algoritmi e strutture dati: ordinamento, ricerca e complessità computazionale.',
 'disponibile', 1),
('Calcolo Integrale',
 'Teoria e applicazioni del calcolo integrale: integrali definiti e indefiniti, teorema fondamentale.',
 'in_corso', 1),
('Sviluppo Web con Flask',
 'Realizzazione di una web app con Python/Flask, template Jinja2 e database SQLite.',
 'in_corso', 2),
('Database Relazionali',
 'Progettazione ER, normalizzazione fino alla 3FN e query SQL avanzate.',
 'in_corso', 2),
('Algebra Lineare',
 'Vettori, matrici, sistemi lineari e trasformazioni geometriche.',
 'completato', 1),
('Python per Principianti',
 'Basi del linguaggio Python: variabili, funzioni, strutture dati e introduzione alla OOP.',
 'completato', 2),
('Machine Learning Basics',
 'Introduzione al machine learning: regressione lineare, classificazione, validazione.',
 'in_corso', 4),
('Reti Neurali',
 'Reti neurali artificiali: percettrone, backpropagation, deep learning.',
 'disponibile', 4),
('Meccanica Quantistica',
 'Principi della meccanica quantistica: equazione di Schrödinger e operatori.',
 'in_corso', 5),
('Termodinamica',
 'Leggi della termodinamica, entropia e cicli termodinamici.',
 'completato', 5),
('Geometria Analitica',
 'Coniche, rette e piani nello spazio cartesiano.',
 'completato', 3),
('Probabilità e Statistica',
 'Variabili aleatorie, distribuzioni, test di ipotesi e regressione.',
 'in_corso', 3),
('Sviluppo Mobile con React Native',
 'Creazione di app mobile cross-platform con React Native.',
 'disponibile', 4),
('Sicurezza Informatica',
 'Crittografia, autenticazione, OWASP top 10, penetration testing.',
 'in_corso', 2),
('Strutture Dati Avanzate',
 'Alberi bilanciati, grafi, hash table e algoritmi su grafi.',
 'completato', 1);

/* ── ISCRIZIONI ──
   Sfrutto vari progressi per avere distribuzioni interessanti.
   Studenti id: 6..20 — Progetti id: 1..15 */
INSERT INTO iscrizione (studente_id, progetto_id, progresso, note) VALUES
/* Calcolo Integrale (in_corso, prog 2) */
(6,  2, 70, 'Sto studiando i metodi di integrazione per parti.'),
(7,  2, 55, 'Buon avanzamento, ho completato gli integrali definiti.'),
(11, 2, 30, 'Sto recuperando il programma.'),

/* Sviluppo Web Flask (in_corso, prog 3) */
(6,  3, 65, 'Ho completato le route di autenticazione e i Blueprint.'),
(7,  3, 40, 'Ho impostato la struttura del progetto.'),
(8,  3, 85, 'Quasi finito, sto rifinendo i template Jinja2.'),
(12, 3, 50, 'A metà del corso, mi piace molto Flask.'),

/* Database Relazionali (in_corso, prog 4) */
(8,  4, 80, 'Schema ER completato e normalizzato.'),
(9,  4, 25, 'Iniziata fase di analisi requisiti.'),
(13, 4, 60, 'Ho completato la modellazione concettuale.'),
(14, 4, 45, 'Sto lavorando alle query con JOIN.'),

/* Algebra Lineare (completato, prog 5) */
(6,  5, 100, 'Progetto completato! Trasformazioni molto interessanti.'),
(8,  5, 100, 'Completato con successo.'),
(10, 5, 100, 'Finito, parte sui sistemi lineari ottima.'),
(15, 5, 100, 'Concluso brillantemente.'),
(16, 5, 90,  'Quasi finito, mi manca solo l’ultima parte.'),

/* Python per Principianti (completato, prog 6) */
(7,  6, 100, 'Terminato! Imparato Python da zero.'),
(9,  6, 100, 'Completato, corso ottimo.'),
(11, 6, 100, 'Finito con piacere.'),
(17, 6, 100, 'Concluso, ora mi sento pronto per progetti più complessi.'),
(18, 6, 75,  'Quasi alla fine.'),

/* Machine Learning Basics (in_corso, prog 7) */
(6,  7, 50, 'Sto seguendo le lezioni sulla regressione lineare.'),
(10, 7, 70, 'Ho completato la parte di classificazione.'),
(15, 7, 35, 'Sto studiando le metriche di valutazione.'),
(19, 7, 20, 'Appena iniziato.'),

/* Meccanica Quantistica (in_corso, prog 9) */
(11, 9, 60, 'Equazione di Schrödinger compresa.'),
(12, 9, 40, 'Sto studiando gli operatori.'),
(20, 9, 15, 'Argomento difficile, vado piano.'),

/* Termodinamica (completato, prog 10) */
(13, 10, 100, 'Concluso, cicli termodinamici molto chiari.'),
(14, 10, 100, 'Completato.'),
(16, 10, 100, 'Finito con ottimi risultati.'),

/* Geometria Analitica (completato, prog 11) */
(15, 11, 100, 'Coniche studiate a fondo.'),
(17, 11, 100, 'Completato con successo.'),
(19, 11, 80,  'Quasi finito.'),

/* Probabilità e Statistica (in_corso, prog 12) */
(7,  12, 55, 'Sto facendo i test di ipotesi.'),
(13, 12, 70, 'Regressione completata.'),
(18, 12, 40, 'A metà del programma.'),

/* Sicurezza Informatica (in_corso, prog 14) */
(9,  14, 65, 'Ho completato la parte di crittografia.'),
(14, 14, 35, 'Sto studiando OWASP top 10.'),
(20, 14, 50, 'Buon avanzamento sui temi di autenticazione.'),

/* Strutture Dati Avanzate (completato, prog 15) */
(6,  15, 100, 'Alberi bilanciati e grafi compresi a fondo.'),
(10, 15, 100, 'Concluso, hash table molto utili.'),
(11, 15, 100, 'Finito con ottimi risultati.'),
(15, 15, 100, 'Algoritmi su grafi appresi.');

/* ── FEEDBACK ──
   Gli studenti danno feedback ai docenti dei progetti completati o ben avviati.
   docente_id deriva dal docente del progetto. */
INSERT INTO feedback (studente_id, docente_id, progetto_id, stelle_docente, stelle_progetto, commento) VALUES
/* Algebra Lineare (docente 1) */
(6,  1, 5, 4, 4, 'Spiegazioni chiare, avrei gradito qualche esempio in più.'),
(8,  1, 5, 5, 5, 'Ottimo progetto! Il prof. Rossi spiega molto bene.'),
(10, 1, 5, 5, 4, 'Lezioni eccellenti.'),
(15, 1, 5, 4, 4, 'Buon corso, molto solido.'),

/* Python per Principianti (docente 2) */
(7,  2, 6, 5, 5, 'Fantastico! Ho imparato Python da zero.'),
(9,  2, 6, 5, 5, 'La prof.ssa Bianchi è bravissima.'),
(11, 2, 6, 4, 4, 'Molto buono, qualche esempio in più sarebbe stato utile.'),
(17, 2, 6, 5, 5, 'Insegnamento eccellente.'),

/* Termodinamica (docente 5) */
(13, 5, 10, 5, 4, 'Cicli termodinamici spiegati con grande chiarezza.'),
(14, 5, 10, 4, 4, 'Ottimo corso, materiale ben strutturato.'),
(16, 5, 10, 5, 5, 'Il prof. Galli rende la materia accessibile.'),

/* Geometria Analitica (docente 3) */
(15, 3, 11, 4, 4, 'Buon corso, esercizi ben calibrati.'),
(17, 3, 11, 5, 4, 'Spiegazioni cristalline.'),
(19, 3, 11, 3, 3, 'Discreto, alcuni argomenti meritavano più tempo.'),

/* Strutture Dati Avanzate (docente 1) */
(6,  1, 15, 5, 5, 'Argomenti complessi resi semplici.'),
(10, 1, 15, 5, 4, 'Ottimo come sempre il prof. Rossi.'),
(11, 1, 15, 4, 5, 'Molto interessante.'),
(15, 1, 15, 4, 4, 'Buon livello di approfondimento.'),

/* Feedback su progetti in_corso (gli studenti possono valutare anche prima del completamento) */
/* Sviluppo Web Flask (docente 2) */
(8,  2, 3, 5, 5, 'Stage molto pratico, sto imparando tantissimo.'),
(12, 2, 3, 4, 5, 'Buona organizzazione delle lezioni.'),

/* Database Relazionali (docente 2) */
(13, 2, 4, 4, 4, 'Materia ostica resa chiara.'),

/* Machine Learning Basics (docente 4) */
(10, 4, 7, 5, 5, 'Argomento appassionante, prof preparata.'),
(15, 4, 7, 4, 4, 'Molto interessante.'),

/* Probabilità e Statistica (docente 3) */
(13, 3, 12, 4, 3, 'Buona spiegazione della regressione.'),

/* Sicurezza Informatica (docente 2) */
(9,  2, 14, 5, 5, 'Argomenti attualissimi.');
