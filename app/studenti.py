import os
import socket
import subprocess
import sys
import time

from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from app.auth import ruolo_required
from app.repositories import (
    iscrizione_repository as ir,
    feedback_repository as fr,
    progetto_repository as pr,
)

bp = Blueprint('studenti', __name__, url_prefix='/studenti')

STREAMLIT_PORT = 8501
HRANALYTICS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _streamlit_is_up():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.3)
    try:
        s.connect(('127.0.0.1', STREAMLIT_PORT))
        return True
    except OSError:
        return False
    finally:
        s.close()


def _launch_streamlit():
    flags = 0
    if os.name == 'nt':
        # CREATE_NEW_PROCESS_GROUP: streamlit non muore se Flask riceve Ctrl+C
        # CREATE_NO_WINDOW: nessuna finestra cmd visibile
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
    subprocess.Popen(
        [
            sys.executable, '-m', 'streamlit', 'run', 'app.py',
            '--server.headless=true',
            '--server.port', str(STREAMLIT_PORT),
            '--browser.gatherUsageStats=false',
        ],
        cwd=HRANALYTICS_DIR,
        creationflags=flags,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


@bp.route('/launch-dashboard')
@ruolo_required('studente')
def launch_dashboard():
    dashboard_url = f'http://localhost:{STREAMLIT_PORT}'
    if _streamlit_is_up():
        return redirect(dashboard_url)
    if not os.path.isdir(HRANALYTICS_DIR):
        flash(f'Cartella dashboard non trovata: {HRANALYTICS_DIR}', 'danger')
        return redirect(url_for('studenti.dashboard'))
    try:
        _launch_streamlit()
    except Exception as e:
        flash(f'Impossibile avviare la dashboard: {e}', 'danger')
        return redirect(url_for('studenti.dashboard'))
    for _ in range(30):
        time.sleep(0.5)
        if _streamlit_is_up():
            return redirect(dashboard_url)
    flash('La dashboard non risponde dopo 15s. Riprova tra qualche secondo.', 'warning')
    return redirect(url_for('studenti.dashboard'))


@bp.route('/dashboard')
@ruolo_required('studente')
def dashboard():
    progetti_iscritto = ir.get_progetti_studente(g.user['id'])
    stats_docenti     = fr.get_statistiche_docenti()
    totale_progetti   = len(pr.get_tutti_i_progetti())
    return render_template(
        'studenti/dashboard.html',
        progetti=progetti_iscritto,
        stats_docenti=stats_docenti,
        totale_progetti=totale_progetti,
    )


@bp.route('/iscrivi/<int:progetto_id>', methods=['POST'])
@ruolo_required('studente')
def iscrivi(progetto_id):
    progetto = pr.get_progetto_by_id(progetto_id)
    if progetto is None:
        return render_template('404.html'), 404
    if progetto['stato'] == 'completato':
        flash('Non puoi iscriverti a un progetto già completato.', 'danger')
    elif ir.is_iscritto(g.user['id'], progetto_id):
        flash('Sei già iscritto a questo progetto.', 'info')
    else:
        ir.iscrivi(g.user['id'], progetto_id)
        if progetto['stato'] == 'disponibile':
            pr.aggiorna_stato(progetto_id, 'in_corso')
        flash('Iscrizione avvenuta con successo!', 'success')
    return redirect(url_for('main.dettaglio_progetto', id=progetto_id))


@bp.route('/progresso/<int:progetto_id>', methods=['POST'])
@ruolo_required('studente')
def aggiorna_progresso(progetto_id):
    if not ir.is_iscritto(g.user['id'], progetto_id):
        flash('Non sei iscritto a questo progetto.', 'danger')
        return redirect(url_for('studenti.dashboard'))

    progresso = request.form.get('progresso', type=int, default=0)
    note      = request.form.get('note', '').strip()

    if progresso not in range(0, 101):
        flash('Valore di avanzamento non valido.', 'danger')
    else:
        ir.aggiorna_progresso(g.user['id'], progetto_id, progresso, note)
        flash('Avanzamento aggiornato.', 'success')

    return redirect(url_for('studenti.dashboard'))


@bp.route('/valuta/<int:progetto_id>', methods=['GET', 'POST'])
@ruolo_required('studente')
def valuta(progetto_id):
    progetto = pr.get_progetto_by_id(progetto_id)
    if progetto is None:
        return render_template('404.html'), 404

    if not ir.is_iscritto(g.user['id'], progetto_id):
        flash('Devi essere iscritto al progetto per valutare il docente.', 'warning')
        return redirect(url_for('main.dettaglio_progetto', id=progetto_id))

    feedback_esistente = fr.get_feedback_studente_progetto(g.user['id'], progetto_id)

    if request.method == 'POST':
        stelle   = request.form.get('stelle', type=int)
        commento = request.form.get('commento', '').strip()

        if stelle not in range(1, 6):
            flash('Seleziona un voto da 1 a 5 stelle.', 'danger')
        else:
            fr.crea_feedback(
                g.user['id'], progetto['docente_id'], progetto_id, stelle, commento
            )
            flash('Valutazione inviata con successo!', 'success')
            return redirect(url_for('studenti.dashboard'))

    return render_template(
        'studenti/valuta.html', progetto=progetto, feedback=feedback_esistente
    )
