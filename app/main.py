from flask import Blueprint, render_template, g
from app.repositories import progetto_repository as pr
from app.repositories import iscrizione_repository as ir

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/progetti/')
def lista_progetti():
    progetti = pr.get_tutti_i_progetti()
    return render_template('progetti/lista.html', progetti=progetti)


@bp.route('/progetti/<int:id>')
def dettaglio_progetto(id):
    progetto = pr.get_progetto_by_id(id)
    if progetto is None:
        return render_template('404.html'), 404
    studenti   = ir.get_studenti_iscritti(id)
    is_iscritto = (
        g.user is not None
        and g.user['ruolo'] == 'studente'
        and ir.is_iscritto(g.user['id'], id)
    )
    return render_template(
        'progetti/dettaglio.html',
        progetto=progetto,
        studenti=studenti,
        is_iscritto=is_iscritto,
    )
