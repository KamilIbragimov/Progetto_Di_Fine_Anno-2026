"""Blueprint /docenti — area personale, CRUD progetti, visualizzazione feedback ricevuti."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from app.auth import ruolo_required
from app.repositories import (
    progetto_repository as pr,
    feedback_repository as fr,
    iscrizione_repository as ir,
)

bp = Blueprint('docenti', __name__, url_prefix='/docenti')

STATI_VALIDI        = ('disponibile', 'in_corso', 'completato')
STATI_CREAZIONE     = ('disponibile', 'in_corso')   # non si crea già completato


@bp.route('/area')
@ruolo_required('docente')
def area_personale():
    progetti = pr.get_progetti_con_stats(g.user['id'])
    feedback_map = {p['id']: fr.get_feedback_by_progetto(p['id']) for p in progetti}
    studenti_map = {p['id']: ir.get_studenti_iscritti(p['id'])    for p in progetti}
    return render_template(
        'docenti/area_personale.html',
        progetti=progetti,
        feedback_map=feedback_map,
        studenti_map=studenti_map,
    )


@bp.route('/feedback')
@ruolo_required('docente')
def feedback_ricevuti():
    feedbacks = fr.get_feedback_docente(g.user['id'])
    stats     = fr.get_media_stelle_docente(g.user['id'])
    return render_template('docenti/feedback_ricevuti.html', feedbacks=feedbacks, stats=stats)


@bp.route('/crea', methods=['GET', 'POST'])
@ruolo_required('docente')
def crea_progetto():
    if request.method == 'POST':
        titolo      = request.form['titolo'].strip()
        descrizione = request.form.get('descrizione', '').strip()
        stato       = request.form.get('stato', 'disponibile')

        if not titolo:
            flash('Il titolo è obbligatorio.', 'danger')
        elif stato not in STATI_CREAZIONE:
            flash('Stato non valido.', 'danger')
        else:
            pr.crea_progetto(titolo, descrizione, stato, g.user['id'])
            flash('Progetto creato.', 'success')
            return redirect(url_for('main.lista_progetti'))

    return render_template('progetti/crea.html', stati=STATI_CREAZIONE)


@bp.route('/<int:id>/modifica', methods=['GET', 'POST'])
@ruolo_required('docente')
def modifica_progetto(id):
    progetto = pr.get_progetto_by_id(id)
    if progetto is None or progetto['docente_id'] != g.user['id']:
        flash('Progetto non trovato o accesso non autorizzato.', 'danger')
        return redirect(url_for('main.lista_progetti'))

    if request.method == 'POST':
        titolo      = request.form['titolo'].strip()
        descrizione = request.form.get('descrizione', '').strip()
        stato       = request.form.get('stato', progetto['stato'])

        if not titolo:
            flash('Il titolo è obbligatorio.', 'danger')
        elif stato not in STATI_VALIDI:
            flash('Stato non valido.', 'danger')
        else:
            pr.aggiorna_progetto(id, titolo, descrizione, stato)
            flash('Progetto aggiornato.', 'success')
            return redirect(url_for('main.dettaglio_progetto', id=id))

    return render_template('progetti/modifica.html', progetto=progetto, stati=STATI_VALIDI)


@bp.route('/<int:id>/elimina', methods=['POST'])
@ruolo_required('docente')
def elimina_progetto(id):
    progetto = pr.get_progetto_by_id(id)
    if progetto is None or progetto['docente_id'] != g.user['id']:
        flash('Progetto non trovato o accesso non autorizzato.', 'danger')
    elif progetto['stato'] != 'disponibile':
        flash('Non puoi eliminare un progetto già avviato o completato.', 'danger')
    else:
        pr.elimina_progetto(id)
        flash('Progetto eliminato.', 'success')
    return redirect(url_for('main.lista_progetti'))
