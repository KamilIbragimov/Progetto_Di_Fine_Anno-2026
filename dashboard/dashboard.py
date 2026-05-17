"""Dashboard Streamlit di SchoolHRM: legge il database in sola lettura e mostra
KPI, grafici e un modello di regressione logistica per predire la sufficienza.

Dual-mode come il resto del progetto: se la variabile d'ambiente `DATABASE_URL`
è valorizzata legge da PostgreSQL (Supabase — stesso DB della web app in
produzione), altrimenti dal file SQLite locale `instance/schoolhrm.sqlite`.

Uso (dalla radice del progetto):
    streamlit run dashboard/dashboard.py
"""
import os
import sqlite3
import time

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH      = os.path.join(PROJECT_ROOT, 'instance', 'schoolhrm.sqlite')

load_dotenv(os.path.join(PROJECT_ROOT, '.env'))


def _database_url():
    """DATABASE_URL da env (.env locale / Render) o da st.secrets (Streamlit Cloud)."""
    url = os.environ.get('DATABASE_URL')
    if url:
        return url
    try:
        return st.secrets.get('DATABASE_URL')
    except Exception:
        return None


DATABASE_URL = _database_url()

# ── Palette colori coerente ───────────────────────────────────────────────────
COLORS       = ['#4361ee', '#f72585', '#4cc9f0', '#7209b7', '#06d6a0']
STATE_COLORS = {'disponibile': '#4cc9f0', 'in_corso': '#f8961e', 'completato': '#06d6a0'}
ESITO_COLORS = {'Sufficiente': '#06d6a0', 'Non sufficiente': '#f72585',
                'Eccellente': '#06d6a0', 'Da migliorare': '#f72585'}
BINARY_COLORS = {1: '#06d6a0', 0: '#f72585'}   # verde=positivo, rosso=negativo

# ── Label colonne → nomi leggibili (definiti una volta sola) ──────────────────
LABELS_S = {
    'nome': 'Nome', 'iscrizioni': 'Iscrizioni',
    'completati': 'Completati', 'progresso_medio': 'Progresso medio (%)',
    'sufficiente': 'Sufficiente',
}
LABELS_D = {
    'nome': 'Nome', 'n_progetti': 'Progetti creati',
    'n_feedback': 'Feedback ricevuti',
    'valutazione_media': 'Valutazione media (★)', 'eccellente': 'Eccellente',
}
LABELS_P = {
    'titolo': 'Titolo', 'stato': 'Stato', 'docente': 'Docente',
    'n_studenti': 'Studenti iscritti',
    'progresso_medio': 'Progresso medio (%)', 'n_feedback': 'Feedback ricevuti',
    'valutazione_progetto': 'Valutazione progetto (★)',
}

# ── Configurazione pagina ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="SchoolHRM Analytics",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
[data-testid="stMetric"] {
    background: #f8f9ff;
    border: 1px solid #dde1ff;
    border-radius: 12px;
    padding: 14px 18px;
}
[data-testid="stMetricValue"] { font-size: 2rem; font-weight: 700; color: #2d3561; }
[data-testid="stMetricLabel"] { font-size: 0.78rem; color: #6c757d; letter-spacing: .04em; }
div[data-testid="stSidebar"] { background: #f0f2ff; }
</style>
""", unsafe_allow_html=True)


# ── Lettura live dal database ─────────────────────────────────────────────────
def _connect():
    """Connessione in sola lettura: PostgreSQL se DATABASE_URL è settata, altrimenti SQLite."""
    if DATABASE_URL:
        import psycopg2
        return psycopg2.connect(DATABASE_URL)
    return sqlite3.connect(f'file:{DB_PATH}?mode=ro', uri=True)


def load_data():
    try:
        conn = _connect()
    except Exception:
        return None, None, None

    studenti = pd.read_sql_query('''
        SELECT
            u.nome,
            COUNT(DISTINCT i.progetto_id)                   AS iscrizioni,
            COUNT(CASE WHEN i.progresso = 100 THEN 1 END)   AS completati,
            CAST(ROUND(COALESCE(AVG(i.progresso), 0), 1) AS FLOAT) AS progresso_medio,
            CASE WHEN COALESCE(AVG(i.progresso), 0) >= 60
                 THEN 1 ELSE 0 END                          AS sufficiente
        FROM utente u
        LEFT JOIN iscrizione i ON i.studente_id = u.id
        WHERE u.ruolo = 'studente'
        GROUP BY u.id, u.nome ORDER BY u.id
    ''', conn)

    docenti = pd.read_sql_query('''
        SELECT
            u.nome,
            COUNT(DISTINCT p.id)                            AS n_progetti,
            COUNT(DISTINCT f.id)                            AS n_feedback,
            CAST(ROUND(COALESCE(AVG(f.stelle_docente), 0), 2) AS FLOAT) AS valutazione_media,
            CASE WHEN COALESCE(AVG(f.stelle_docente), 0) >= 4.0
                 THEN 1 ELSE 0 END                          AS eccellente
        FROM utente u
        LEFT JOIN progetto p ON p.docente_id = u.id
        LEFT JOIN feedback f ON f.docente_id = u.id
        WHERE u.ruolo = 'docente'
        GROUP BY u.id, u.nome ORDER BY u.id
    ''', conn)

    progetti = pd.read_sql_query('''
        SELECT
            p.titolo,
            p.stato,
            u.nome AS docente,
            COUNT(DISTINCT i.studente_id)                   AS n_studenti,
            CAST(ROUND(COALESCE(AVG(i.progresso), 0), 1) AS FLOAT) AS progresso_medio,
            COUNT(DISTINCT f.id)                            AS n_feedback,
            CAST(ROUND(COALESCE(AVG(f.stelle_progetto), 0), 2) AS FLOAT) AS valutazione_progetto
        FROM progetto p
        JOIN utente u ON u.id = p.docente_id
        LEFT JOIN iscrizione i ON i.progetto_id = p.id
        LEFT JOIN feedback f ON f.progetto_id = p.id
        GROUP BY p.id, p.titolo, p.stato, u.nome ORDER BY p.id
    ''', conn)

    conn.close()
    return studenti, docenti, progetti


studenti, docenti, progetti = load_data()
if studenti is None:
    if DATABASE_URL:
        st.error("⚠️ Impossibile connettersi al database PostgreSQL (DATABASE_URL). "
                 "Verifica la connection string e che `psycopg2-binary` sia installato.")
    else:
        st.error("⚠️ Database SQLite non trovato. Esegui prima `python setup_db.py`.")
    st.stop()
if studenti.empty and docenti.empty:
    st.error("Nessun utente nel database.")
    st.stop()


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎓 SchoolHRM")
    st.caption(f"{len(studenti)} studenti · {len(docenti)} docenti · {len(progetti)} progetti")

    if st.button("🔄 Aggiorna dati", use_container_width=True, type="primary"):
        st.rerun()

    auto_refresh = st.checkbox("Aggiornamento automatico (10s)", value=False)

    st.divider()
    st.markdown("**ℹ️ Legenda**")
    st.caption(
        "**Sufficiente** — studente con progresso medio ≥ 60%\n\n"
        "**Eccellente** — docente con valutazione media ≥ 4 stelle\n\n"
        "**Completati** — progetti portati al 100%"
    )


# ── Header ────────────────────────────────────────────────────────────────────
st.title("🎓 SchoolHRM Analytics")
st.caption("I dati si aggiornano in tempo reale dal database.")
st.divider()


# ── Helper per opzioni grafici uniformi ──────────────────────────────────────
CHART_LAYOUT = dict(template='simple_white', margin=dict(l=10, r=10, t=40, b=10))


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Riepilogo",
    "🎒 Studenti",
    "👨‍🏫 Docenti",
    "🤖 Predizione AI",
    "📥 Esporta",
])


# ── Tab 1: Riepilogo ──────────────────────────────────────────────────────────
with tab1:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Studenti",            len(studenti))
    c2.metric("Docenti",             len(docenti))
    c3.metric("Progetti totali",     len(progetti))
    c4.metric("Studenti sufficienti", f"{studenti['sufficiente'].mean() * 100:.1f}%")
    c5.metric("Docenti eccellenti",   f"{docenti['eccellente'].mean() * 100:.1f}%")

    st.markdown("")
    c6, c7, c8 = st.columns(3)
    c6.metric("Progresso medio studenti",  f"{studenti['progresso_medio'].mean():.1f}%")
    c7.metric("Valutazione media docenti", f"{docenti['valutazione_media'].mean():.2f} / 5 ★")
    c8.metric("Iscrizioni medie a testa",  f"{studenti['iscrizioni'].mean():.1f}")

    st.divider()
    col_a, col_b = st.columns(2)

    with col_a:
        stati = progetti['stato'].value_counts().reset_index()
        stati.columns = ['stato', 'n']
        fig = px.pie(stati, names='stato', values='n',
                     title="Progetti per stato",
                     color='stato', color_discrete_map=STATE_COLORS, hole=0.4)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(showlegend=False, **CHART_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        top = progetti.sort_values('n_studenti', ascending=False).head(10)
        fig = px.bar(top, x='n_studenti', y='titolo',
                     orientation='h', title="Progetti più seguiti (top 10)",
                     color='stato', color_discrete_map=STATE_COLORS,
                     labels={'n_studenti': 'Studenti iscritti', 'titolo': '', 'stato': 'Stato'})
        fig.update_layout(yaxis=dict(autorange='reversed'), **CHART_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)


# ── Tab 2: Studenti ───────────────────────────────────────────────────────────
with tab2:
    st.caption("**Sufficiente** = progresso medio ≥ 60%  ·  **Completati** = progetti portati al 100%")

    col_a, col_b = st.columns(2)

    with col_a:
        suff = studenti['sufficiente'].value_counts().reset_index()
        suff.columns = ['val', 'n']
        suff['esito'] = suff['val'].map({1: 'Sufficiente', 0: 'Non sufficiente'})
        fig = px.pie(suff, names='esito', values='n',
                     title="Studenti sufficienti",
                     color='esito', color_discrete_map=ESITO_COLORS, hole=0.4)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(showlegend=False, **CHART_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        fig = px.histogram(studenti, x='progresso_medio', nbins=8,
                           title="Distribuzione del progresso medio",
                           color_discrete_sequence=[COLORS[0]],
                           labels={'progresso_medio': 'Progresso medio (%)'})
        fig.add_vline(x=60, line_dash='dash', line_color='red',
                      annotation_text='soglia sufficiente (60%)')
        fig.update_layout(**CHART_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)

    fig = px.bar(studenti.sort_values('progresso_medio', ascending=False),
                 x='nome', y='progresso_medio',
                 color='sufficiente', color_discrete_map=BINARY_COLORS,
                 title="Progresso medio per studente",
                 labels={'nome': '', 'progresso_medio': 'Progresso medio (%)',
                         'sufficiente': 'Sufficiente'})
    fig.add_hline(y=60, line_dash='dash', line_color='gray',
                  annotation_text='soglia 60%')
    fig.update_layout(xaxis_tickangle=-40, height=380, **CHART_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

    col_c, col_d = st.columns(2)
    with col_c:
        fig = px.bar(studenti.sort_values('iscrizioni', ascending=False),
                     x='nome', y='iscrizioni', title="Iscrizioni per studente",
                     color_discrete_sequence=[COLORS[2]],
                     labels={'nome': '', 'iscrizioni': 'Progetti iscritti'})
        fig.update_layout(xaxis_tickangle=-40, **CHART_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)

    with col_d:
        fig = px.bar(studenti.sort_values('completati', ascending=False),
                     x='nome', y='completati', title="Progetti completati al 100%",
                     color_discrete_sequence=[COLORS[4]],
                     labels={'nome': '', 'completati': 'Completati'})
        fig.update_layout(xaxis_tickangle=-40, **CHART_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.markdown("**Dettaglio studenti**")
    st.dataframe(
        studenti[list(LABELS_S)].rename(columns=LABELS_S),
        use_container_width=True, hide_index=True,
    )


# ── Tab 3: Docenti ────────────────────────────────────────────────────────────
with tab3:
    st.caption("**Eccellente** = valutazione media ≥ 4 stelle  ·  i feedback sono lasciati dagli studenti iscritti")

    col_a, col_b = st.columns(2)

    with col_a:
        fig = px.bar(docenti.sort_values('valutazione_media', ascending=False),
                     x='nome', y='valutazione_media',
                     color='eccellente', color_discrete_map=BINARY_COLORS,
                     title="Valutazione media per docente",
                     labels={'nome': '', 'valutazione_media': 'Stelle medie (1-5)',
                             'eccellente': 'Eccellente'})
        fig.add_hline(y=4.0, line_dash='dash', line_color='gray',
                      annotation_text='soglia eccellente (4 ★)')
        fig.update_layout(xaxis_tickangle=-20, **CHART_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        fig = px.bar(docenti.sort_values('n_feedback', ascending=False),
                     x='nome', y='n_feedback',
                     title="Feedback ricevuti per docente",
                     color_discrete_sequence=[COLORS[1]],
                     labels={'nome': '', 'n_feedback': 'Numero feedback'})
        fig.update_layout(xaxis_tickangle=-20, **CHART_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)

    proj_fb = progetti[progetti['n_feedback'] > 0].sort_values('n_feedback', ascending=False)
    if not proj_fb.empty:
        fig = px.bar(proj_fb, x='titolo', y='n_feedback', color='docente',
                     title="Distribuzione feedback per progetto",
                     labels={'titolo': '', 'n_feedback': 'Feedback ricevuti',
                             'docente': 'Docente'})
        fig.update_layout(xaxis_tickangle=-40, legend_title='Docente',
                          height=380, **CHART_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.markdown("**Dettaglio docenti**")
    st.dataframe(
        docenti[list(LABELS_D)].rename(columns=LABELS_D),
        use_container_width=True, hide_index=True,
    )


# ── Tab 4: Predizione AI ──────────────────────────────────────────────────────
with tab4:
    st.subheader("Predizione sufficienza — Regressione Logistica")
    st.caption(
        "Il modello usa il numero di **iscrizioni** e i **progetti completati** "
        "per stimare se uno studente raggiungerà la sufficienza (progresso medio ≥ 60%)."
    )

    features, target = ['iscrizioni', 'completati'], 'sufficiente'

    if studenti[target].nunique() < 2:
        st.warning("Servono studenti sia sufficienti che non sufficienti. Verifica i dati nel database.")
    else:
        X, y = studenti[features], studenti[target]
        # stratify mantiene la stessa proporzione di sufficienti/non sufficienti nel test;
        # con pochi campioni può non essere possibile → fallback senza stratify.
        try:
            X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
        except ValueError:
            X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.3, random_state=42)

        model = LogisticRegression(max_iter=1000)
        model.fit(X_tr, y_tr)
        acc = accuracy_score(y_te, model.predict(X_te)) * 100

        col_acc, col_info = st.columns([1, 3])
        col_acc.metric("Accuratezza modello", f"{acc:.1f}%")
        col_info.info(
            "Con pochi campioni l'accuratezza può variare — è un risultato indicativo, "
            "non una misura assoluta."
        )

        st.divider()
        st.markdown("**Prova il modello su uno studente ipotetico**")

        c1, c2 = st.columns(2)
        n_isc  = c1.number_input("Progetti iscritto (1-10)", 1, 10, 3)
        n_comp = c2.number_input("Progetti completati (0-10)", 0, 10, 1)

        pred = model.predict([[n_isc, n_comp]])[0]
        prob = model.predict_proba([[n_isc, n_comp]])[0][1]

        if pred == 1:
            st.success(f"✅ Lo studente è probabilmente **sufficiente** — confidenza: {prob * 100:.1f}%")
        else:
            st.error(f"❌ Lo studente è probabilmente **insufficiente** — confidenza: {(1 - prob) * 100:.1f}%")


# ── Tab 5: Esporta ────────────────────────────────────────────────────────────
with tab5:
    st.subheader("Esporta i dati")

    exp1, exp2, exp3 = st.tabs(["Studenti", "Docenti", "Progetti"])

    with exp1:
        df_s = studenti[list(LABELS_S)].rename(columns=LABELS_S)
        st.dataframe(df_s, use_container_width=True, hide_index=True)
        st.download_button("📥 Scarica CSV studenti",
                           df_s.to_csv(index=False).encode(),
                           'studenti_export.csv', 'text/csv',
                           use_container_width=True, type="primary")

    with exp2:
        df_d = docenti[list(LABELS_D)].rename(columns=LABELS_D)
        st.dataframe(df_d, use_container_width=True, hide_index=True)
        st.download_button("📥 Scarica CSV docenti",
                           df_d.to_csv(index=False).encode(),
                           'docenti_export.csv', 'text/csv',
                           use_container_width=True, type="primary")

    with exp3:
        df_p = progetti[list(LABELS_P)].rename(columns=LABELS_P)
        st.dataframe(df_p, use_container_width=True, hide_index=True)
        st.download_button("📥 Scarica CSV progetti",
                           df_p.to_csv(index=False).encode(),
                           'progetti_export.csv', 'text/csv',
                           use_container_width=True, type="primary")


# ── Aggiornamento automatico ──────────────────────────────────────────────────
if auto_refresh:
    time.sleep(10)
    st.rerun()
