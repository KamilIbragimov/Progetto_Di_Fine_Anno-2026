"""Blueprint /auth — registrazione, login, logout e decorator di accesso per ruolo."""
import functools
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g
from app.repositories import utente_repository as ur

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    g.user = ur.get_utente_by_id(user_id) if user_id else None


@bp.route('/registra', methods=['GET', 'POST'])
def registra():
    if request.method == 'POST':
        nome     = request.form['nome'].strip()
        email    = request.form['email'].strip()
        password = request.form['password']
        ruolo    = request.form['ruolo']

        errore = None
        if not nome:
            errore = 'Il nome è obbligatorio.'
        elif not email:
            errore = "L'email è obbligatoria."
        elif not password:
            errore = 'La password è obbligatoria.'
        elif ruolo not in ('studente', 'docente'):
            errore = 'Ruolo non valido.'
        elif ur.get_utente_by_email(email):
            errore = 'Email già registrata.'

        if errore is None:
            ur.crea_utente(nome, email, password, ruolo)
            flash('Registrazione completata. Effettua il login.', 'success')
            return redirect(url_for('auth.login'))

        flash(errore, 'danger')

    return render_template('auth/register.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form['email'].strip()
        password = request.form['password']
        utente   = ur.get_utente_by_email(email)

        if utente is None or not ur.verifica_password(utente['password_hash'], password):
            flash('Email o password non corretti.', 'danger')
        else:
            session.clear()
            session['user_id'] = utente['id']
            if utente['ruolo'] == 'studente':
                return redirect(url_for('studenti.dashboard'))
            return redirect(url_for('docenti.area_personale'))

    return render_template('auth/login.html')


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))


def ruolo_required(ruolo):
    def decorator(view):
        @functools.wraps(view)
        def wrapped(**kwargs):
            if g.user is None:
                flash('Devi effettuare il login.', 'warning')
                return redirect(url_for('auth.login'))
            if g.user['ruolo'] != ruolo:
                flash('Accesso non autorizzato.', 'danger')
                return redirect(url_for('main.index'))
            return view(**kwargs)
        return wrapped
    return decorator
