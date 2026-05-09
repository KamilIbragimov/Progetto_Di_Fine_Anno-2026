from app.db import get_db


def iscrivi(studente_id, progetto_id):
    db = get_db()
    db.execute(
        'INSERT OR IGNORE INTO iscrizione (studente_id, progetto_id) VALUES (?, ?)',
        (studente_id, progetto_id)
    )
    db.commit()


def is_iscritto(studente_id, progetto_id):
    row = get_db().execute(
        'SELECT id FROM iscrizione WHERE studente_id = ? AND progetto_id = ?',
        (studente_id, progetto_id)
    ).fetchone()
    return row is not None


def get_progetti_studente(studente_id):
    return get_db().execute(
        '''SELECT p.*, u.nome AS nome_docente,
                  i.progresso, i.note, i.created_at AS iscritto_il
           FROM iscrizione i
           JOIN progetto p ON i.progetto_id = p.id
           JOIN utente u ON p.docente_id = u.id
           WHERE i.studente_id = ?
           ORDER BY i.created_at DESC''',
        (studente_id,)
    ).fetchall()


def get_studenti_iscritti(progetto_id):
    return get_db().execute(
        '''SELECT u.nome, i.progresso, i.created_at AS iscritto_il
           FROM iscrizione i
           JOIN utente u ON i.studente_id = u.id
           WHERE i.progetto_id = ?
           ORDER BY i.progresso DESC''',
        (progetto_id,)
    ).fetchall()


def aggiorna_progresso(studente_id, progetto_id, progresso, note):
    db = get_db()
    db.execute(
        '''UPDATE iscrizione SET progresso = ?, note = ?
           WHERE studente_id = ? AND progetto_id = ?''',
        (progresso, note or None, studente_id, progetto_id)
    )
    db.commit()
