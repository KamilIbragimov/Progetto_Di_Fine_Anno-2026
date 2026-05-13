from app.db import get_db


def crea_feedback(studente_id, docente_id, progetto_id, stelle_docente, stelle_progetto, commento):
    db = get_db()
    db.execute(
        '''INSERT INTO feedback (studente_id, docente_id, progetto_id,
                                 stelle_docente, stelle_progetto, commento)
           VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT(studente_id, progetto_id)
           DO UPDATE SET stelle_docente  = excluded.stelle_docente,
                         stelle_progetto = excluded.stelle_progetto,
                         commento        = excluded.commento''',
        (studente_id, docente_id, progetto_id, stelle_docente, stelle_progetto, commento or None)
    )
    db.commit()


def get_feedback_docente(docente_id):
    return get_db().execute(
        '''SELECT f.*, u.nome AS nome_studente, p.titolo AS titolo_progetto
           FROM feedback f
           JOIN utente u ON f.studente_id = u.id
           JOIN progetto p ON f.progetto_id = p.id
           WHERE f.docente_id = ?
           ORDER BY f.created_at DESC''',
        (docente_id,)
    ).fetchall()


def get_media_stelle_docente(docente_id):
    return get_db().execute(
        '''SELECT AVG(stelle_docente)  AS media_docente,
                  AVG(stelle_progetto) AS media_progetto,
                  COUNT(*)             AS totale
           FROM feedback WHERE docente_id = ?''',
        (docente_id,)
    ).fetchone()


def get_feedback_studente_progetto(studente_id, progetto_id):
    return get_db().execute(
        'SELECT * FROM feedback WHERE studente_id = ? AND progetto_id = ?',
        (studente_id, progetto_id)
    ).fetchone()


def get_feedback_by_progetto(progetto_id):
    return get_db().execute(
        '''SELECT f.*, u.nome AS nome_studente
           FROM feedback f
           JOIN utente u ON f.studente_id = u.id
           WHERE f.progetto_id = ?
           ORDER BY f.created_at DESC''',
        (progetto_id,)
    ).fetchall()


def get_statistiche_docenti():
    return get_db().execute(
        '''SELECT u.nome                AS nome_docente,
                  AVG(f.stelle_docente) AS media,
                  COUNT(*)              AS totale
           FROM feedback f
           JOIN utente u ON f.docente_id = u.id
           GROUP BY f.docente_id, u.nome
           ORDER BY media DESC'''
    ).fetchall()
