"""Accesso ai dati della tabella `utente` (studenti + docenti)."""
from werkzeug.security import generate_password_hash, check_password_hash
from app.db import get_db


def crea_utente(nome, email, password, ruolo):
    """Inserisce un nuovo utente con password hashata via werkzeug.security."""
    db = get_db()
    db.execute(
        'INSERT INTO utente (nome, email, password_hash, ruolo) VALUES (?, ?, ?, ?)',
        (nome, email, generate_password_hash(password), ruolo)
    )
    db.commit()


def get_utente_by_email(email):
    """Ritorna l'utente con quella email, oppure None se non esiste."""
    return get_db().execute(
        'SELECT * FROM utente WHERE email = ?', (email,)
    ).fetchone()


def get_utente_by_id(id):
    """Ritorna l'utente con quell'id, oppure None se non esiste."""
    return get_db().execute(
        'SELECT * FROM utente WHERE id = ?', (id,)
    ).fetchone()


def verifica_password(password_hash, password):
    """True se la password in chiaro corrisponde all'hash salvato."""
    return check_password_hash(password_hash, password)
