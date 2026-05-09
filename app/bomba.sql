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
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    studente_id INTEGER NOT NULL,
    docente_id  INTEGER NOT NULL,
    progetto_id INTEGER NOT NULL,
    stelle      INTEGER NOT NULL CHECK (stelle BETWEEN 1 AND 5),
    commento    TEXT,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (studente_id, progetto_id),
    FOREIGN KEY (studente_id) REFERENCES utente(id) ON DELETE CASCADE,
    FOREIGN KEY (docente_id)  REFERENCES utente(id) ON DELETE CASCADE,
    FOREIGN KEY (progetto_id) REFERENCES progetto(id) ON DELETE CASCADE
);

/* ── SEED DATA ── */

INSERT INTO utente (nome, email, password_hash, ruolo) VALUES
('Prof. Marco Rossi',    'rossi@school.it',   'scrypt:32768:8:1$K7AF6IMoTkq83YJR$0c44a5f4507174668c6d3851e3ec105690ef878a70c265c08f7a3faafa43183b81702af3c407695d966d00058523f99bfb590e1b087a66b21fae02b7ffd3e87c', 'docente'),
('Prof.ssa Anna Bianchi','bianchi@school.it',  'scrypt:32768:8:1$K7AF6IMoTkq83YJR$0c44a5f4507174668c6d3851e3ec105690ef878a70c265c08f7a3faafa43183b81702af3c407695d966d00058523f99bfb590e1b087a66b21fae02b7ffd3e87c', 'docente'),
('Luca Ferrari',         'luca@student.it',   'scrypt:32768:8:1$7mpX6yIfyNeYjU56$e228d025a286d68c9379a3c819f6317e3963257d0eaf064ab25e291f675d14d6594255ee5122b064411a5687f4dae985b4d1551f0c3166c400e53698d378ef09', 'studente'),
('Sofia Esposito',       'sofia@student.it',  'scrypt:32768:8:1$7mpX6yIfyNeYjU56$e228d025a286d68c9379a3c819f6317e3963257d0eaf064ab25e291f675d14d6594255ee5122b064411a5687f4dae985b4d1551f0c3166c400e53698d378ef09', 'studente'),
('Marco Ricci',          'marco@student.it',  'scrypt:32768:8:1$7mpX6yIfyNeYjU56$e228d025a286d68c9379a3c819f6317e3963257d0eaf064ab25e291f675d14d6594255ee5122b064411a5687f4dae985b4d1551f0c3166c400e53698d378ef09', 'studente'),
('Elena Conti',          'elena@student.it',  'scrypt:32768:8:1$7mpX6yIfyNeYjU56$e228d025a286d68c9379a3c819f6317e3963257d0eaf064ab25e291f675d14d6594255ee5122b064411a5687f4dae985b4d1551f0c3166c400e53698d378ef09', 'studente');

INSERT INTO progetto (titolo, descrizione, stato, docente_id) VALUES
('Introduzione agli Algoritmi',
 'Fondamenti di algoritmi e strutture dati: ordinamento, ricerca e complessità computazionale. Progetto disponibile per iscriversi.',
 'disponibile', 1),

('Calcolo Integrale',
 'Teoria e applicazioni del calcolo integrale: integrali definiti e indefiniti, teorema fondamentale del calcolo.',
 'disponibile', 1),

('Sviluppo Web con Flask',
 'Realizzazione di una web app con Python/Flask, template Jinja2 e database SQLite. Progetto in corso.',
 'in_corso', 2),

('Database Relazionali',
 'Progettazione ER, normalizzazione fino alla 3FN e query SQL avanzate su database relazionale.',
 'in_corso', 2),

('Algebra Lineare',
 'Vettori, matrici, sistemi lineari e trasformazioni geometriche. Progetto concluso.',
 'completato', 1),

('Python per Principianti',
 'Basi del linguaggio Python: variabili, funzioni, strutture dati e introduzione alla OOP. Progetto concluso.',
 'completato', 2);

INSERT INTO iscrizione (studente_id, progetto_id, progresso, note) VALUES
(3, 3, 65, 'Ho completato le route di autenticazione e sto lavorando sui Blueprint.'),
(4, 3, 40, 'Ho impostato la struttura del progetto e implementato il modulo di registrazione.'),
(5, 4, 80, 'Schema ER completato e normalizzato, ora sto scrivendo le query di aggregazione.'),
(6, 4, 25, 'Ho iniziato la fase di analisi dei requisiti e abbozzato il primo schema ER.'),
(3, 5, 100, 'Progetto completato! I capitoli sulle trasformazioni geometriche erano molto interessanti.'),
(5, 5, 100, 'Completato con successo. Ho apprezzato molto la parte sui sistemi lineari.'),
(4, 6, 100, 'Terminato! Ho imparato Python praticamente da zero, corso molto ben strutturato.');

INSERT INTO feedback (studente_id, docente_id, progetto_id, stelle, commento) VALUES
(3, 1, 5, 4, 'Progetto molto utile, spiegazioni chiare. Avrei gradito qualche esempio pratico in più.'),
(5, 1, 5, 5, 'Ottimo progetto! Il prof. Rossi spiega con molta chiarezza, lo consiglio.'),
(4, 2, 6, 5, 'Fantastico! Ho imparato Python praticamente da zero. La prof.ssa Bianchi è bravissima.');
