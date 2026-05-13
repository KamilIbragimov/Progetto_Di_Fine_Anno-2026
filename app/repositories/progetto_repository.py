from app.db import get_db


def get_tutti_i_progetti():
    return get_db().execute(
        '''SELECT p.*, u.nome AS nome_docente
           FROM progetto p
           JOIN utente u ON p.docente_id = u.id
           ORDER BY p.created_at DESC'''
    ).fetchall()


def get_progetto_by_id(id):
    return get_db().execute(
        '''SELECT p.*, u.nome AS nome_docente
           FROM progetto p
           JOIN utente u ON p.docente_id = u.id
           WHERE p.id = ?''',
        (id,)
    ).fetchone()


def crea_progetto(titolo, descrizione, stato, docente_id):
    db = get_db()
    db.execute(
        'INSERT INTO progetto (titolo, descrizione, stato, docente_id) VALUES (?, ?, ?, ?)',
        (titolo, descrizione, stato, docente_id)
    )
    db.commit()


def aggiorna_progetto(id, titolo, descrizione, stato):
    db = get_db()
    db.execute(
        'UPDATE progetto SET titolo = ?, descrizione = ?, stato = ? WHERE id = ?',
        (titolo, descrizione, stato, id)
    )
    db.commit()


def get_progetti_con_stats(docente_id):
    return get_db().execute(
        '''SELECT p.*,
                  COUNT(DISTINCT i.studente_id) AS num_studenti,
                  AVG(f.stelle_progetto)        AS media_progetto,
                  AVG(f.stelle_docente)         AS media_docente,
                  COUNT(DISTINCT f.id)          AS num_feedback
           FROM progetto p
           LEFT JOIN iscrizione i ON i.progetto_id = p.id
           LEFT JOIN feedback   f ON f.progetto_id = p.id
           WHERE p.docente_id = ?
           GROUP BY p.id
           ORDER BY p.created_at DESC''',
        (docente_id,)
    ).fetchall()


def aggiorna_stato(id, stato):
    db = get_db()
    db.execute('UPDATE progetto SET stato = ? WHERE id = ?', (stato, id))
    db.commit()


def elimina_progetto(id):
    db = get_db()
    db.execute('DELETE FROM progetto WHERE id = ?', (id,))
    db.commit()
