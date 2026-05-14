"""Accesso ai dati della tabella `progetto` (creati dai docenti, visibili a tutti)."""
from app.db import get_db


def get_tutti_i_progetti():
    """Lista di tutti i progetti, con il nome del docente, dal più recente."""
    return get_db().execute(
        '''SELECT p.*, u.nome AS nome_docente
           FROM progetto p
           JOIN utente u ON p.docente_id = u.id
           ORDER BY p.created_at DESC'''
    ).fetchall()


def count_progetti():
    """Numero totale di progetti nel sistema (efficiente: usa COUNT)."""
    return get_db().execute('SELECT COUNT(*) AS n FROM progetto').fetchone()['n']


def get_progetto_by_id(id):
    """Singolo progetto con il nome del docente, oppure None."""
    return get_db().execute(
        '''SELECT p.*, u.nome AS nome_docente
           FROM progetto p
           JOIN utente u ON p.docente_id = u.id
           WHERE p.id = ?''',
        (id,)
    ).fetchone()


def crea_progetto(titolo, descrizione, stato, docente_id):
    """Crea un nuovo progetto per il docente specificato."""
    db = get_db()
    db.execute(
        'INSERT INTO progetto (titolo, descrizione, stato, docente_id) VALUES (?, ?, ?, ?)',
        (titolo, descrizione, stato, docente_id)
    )
    db.commit()


def aggiorna_progetto(id, titolo, descrizione, stato):
    """Aggiorna titolo, descrizione e stato di un progetto esistente."""
    db = get_db()
    db.execute(
        'UPDATE progetto SET titolo = ?, descrizione = ?, stato = ? WHERE id = ?',
        (titolo, descrizione, stato, id)
    )
    db.commit()


def get_progetti_con_stats(docente_id):
    """Progetti del docente arricchiti con conteggi e medie (per area personale)."""
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
    """Cambia solo lo stato di un progetto (es. 'disponibile' → 'in_corso')."""
    db = get_db()
    db.execute('UPDATE progetto SET stato = ? WHERE id = ?', (stato, id))
    db.commit()


def elimina_progetto(id):
    """Elimina un progetto. Le FK con ON DELETE CASCADE rimuovono iscrizioni e feedback."""
    db = get_db()
    db.execute('DELETE FROM progetto WHERE id = ?', (id,))
    db.commit()
