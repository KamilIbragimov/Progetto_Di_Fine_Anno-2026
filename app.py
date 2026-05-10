import os
import sqlite3
import time

import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'instance', 'schoolhrm.sqlite'
)

COLORS = ['#4361ee', '#f72585', '#4cc9f0', '#7209b7', '#06d6a0']
STATE_COLORS = {'disponibile': '#4cc9f0', 'in_corso': '#f8961e', 'completato': '#06d6a0'}

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


# ── Lettura live dal SQLite ───────────────────────────────────────────────────
def load_data():
    if not os.path.exists(DB_PATH):
        return None, None, None
    conn = sqlite3.connect(DB_PATH)

    # Studenti: iscrizioni, progresso, completamento
    # "sufficiente" = progresso medio >= 60 (soglia scolastica)
    studenti = pd.read_sql_query('''
        SELECT
            u.nome,
            COUNT(DISTINCT i.progetto_id)                   AS iscrizioni,
            COUNT(CASE WHEN i.progresso = 100 THEN 1 END)   AS completati,
            ROUND(COALESCE(AVG(i.progresso), 0), 1)         AS progresso_medio,
            ROUND(COALESCE(AVG(i.progresso) / 20.0, 0), 2)  AS valutazione,
            CASE WHEN COALESCE(AVG(i.progresso), 0) >= 60
                 THEN 1 ELSE 0 END                          AS sufficiente
        FROM utente u
        LEFT JOIN iscrizione i ON i.studente_id = u.id
        WHERE u.ruolo = 'studente'
        GROUP BY u.id ORDER BY u.id
    ''', conn)

    # Docenti: progetti, feedback ricevuti, valutazione media
    # "eccellente" = valutazione media >= 4 stelle
    docenti = pd.read_sql_query('''
        SELECT
            u.nome,
            COUNT(DISTINCT p.id)                            AS n_progetti,
            COUNT(DISTINCT f.id)                            AS n_feedback,
            ROUND(COALESCE(AVG(f.stelle), 0), 2)            AS valutazione_media,
            CASE WHEN COALESCE(AVG(f.stelle), 0) >= 4.0
                 THEN 1 ELSE 0 END                          AS eccellente
        FROM utente u
        LEFT JOIN progetto p ON p.docente_id = u.id
        LEFT JOIN feedback f ON f.docente_id = u.id
        WHERE u.ruolo = 'docente'
        GROUP BY u.id ORDER BY u.id
    ''', conn)

    # Progetti: stato, partecipazione, feedback
    progetti = pd.read_sql_query('''
        SELECT
            p.titolo,
            p.stato,
            u.nome AS docente,
            COUNT(DISTINCT i.studente_id)               AS n_studenti,
            ROUND(COALESCE(AVG(i.progresso), 0), 1)     AS progresso_medio,
            COUNT(DISTINCT f.id)                        AS n_feedback
        FROM progetto p
        JOIN utente u ON u.id = p.docente_id
        LEFT JOIN iscrizione i ON i.progetto_id = p.id
        LEFT JOIN feedback f ON f.progetto_id = p.id
        GROUP BY p.id ORDER BY p.id
    ''', conn)

    conn.close()
    return studenti, docenti, progetti


studenti, docenti, progetti = load_data()
if studenti is None:
    st.error(f"Database non trovato: `{DB_PATH}`")
    st.stop()
if studenti.empty and docenti.empty:
    st.error("Nessun utente nel database.")
    st.stop()


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎓 SchoolHRM")
    st.caption(
        f"**{len(studenti)} studenti** · **{len(docenti)} docenti** · "
        f"**{len(progetti)} progetti**"
    )

    if st.button("🔄 Aggiorna dati", use_container_width=True, type="primary"):
        st.rerun()

    auto_refresh = st.checkbox("Auto-refresh ogni 10s", value=False)

    st.divider()
    st.markdown("**ℹ️ Legenda metriche**")
    st.caption(
        "**Sufficiente** (studenti): progresso medio ≥ 60%\n\n"
        "**Eccellente** (docenti): valutazione media ≥ 4 stelle\n\n"
        "**Valutazione** (studenti): progresso medio / 20 → scala 0-5"
    )


# ── Header ────────────────────────────────────────────────────────────────────
st.title("🎓 SchoolHRM Analytics")
st.caption("Analisi live — dati letti direttamente dal database, senza cache.")
st.divider()


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview",
    "🎒 Studenti",
    "👨‍🏫 Docenti",
    "🤖 Predizioni AI",
    "📥 Export",
])


# ── Tab 1: Overview ───────────────────────────────────────────────────────────
with tab1:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Studenti totali",      len(studenti))
    c2.metric("Docenti totali",       len(docenti))
    c3.metric("Progetti totali",      len(progetti))
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
        fig_stati = px.pie(
            stati, names='stato', values='n',
            title="Progetti per stato",
            color='stato',
            color_discrete_map=STATE_COLORS,
            hole=0.38,
        )
        fig_stati.update_traces(textposition='inside', textinfo='percent+label')
        fig_stati.update_layout(showlegend=False)
        st.plotly_chart(fig_stati, use_container_width=True)

    with col_b:
        top = progetti.sort_values('n_studenti', ascending=False).head(10)
        fig_top = px.bar(
            top, x='n_studenti', y='titolo',
            orientation='h',
            title="Progetti più seguiti (top 10)",
            color='stato',
            color_discrete_map=STATE_COLORS,
            labels={'n_studenti': 'Studenti iscritti', 'titolo': '', 'stato': 'Stato'},
        )
        fig_top.update_layout(yaxis=dict(autorange='reversed'))
        st.plotly_chart(fig_top, use_container_width=True)


# ── Tab 2: Studenti ───────────────────────────────────────────────────────────
with tab2:
    st.caption("**Sufficiente** = progresso medio ≥ 60%  ·  **Completati** = progetti portati al 100%")

    col_a, col_b = st.columns(2)

    with col_a:
        suff = studenti['sufficiente'].value_counts().reset_index()
        suff.columns = ['val', 'n']
        suff['esito'] = suff['val'].map({1: 'Sufficiente', 0: 'Non sufficiente'})
        fig_suff = px.pie(
            suff, names='esito', values='n',
            title="Studenti sufficienti",
            color='esito',
            color_discrete_map={'Sufficiente': '#06d6a0', 'Non sufficiente': '#f72585'},
            hole=0.38,
        )
        fig_suff.update_traces(textposition='inside', textinfo='percent+label')
        fig_suff.update_layout(showlegend=False)
        st.plotly_chart(fig_suff, use_container_width=True)

    with col_b:
        fig_hist = px.histogram(
            studenti, x='progresso_medio', nbins=10,
            title="Distribuzione progresso medio",
            color_discrete_sequence=[COLORS[0]],
            labels={'progresso_medio': 'Progresso medio (%)'},
        )
        fig_hist.add_vline(x=60, line_dash='dash', line_color='red',
                           annotation_text='soglia sufficiente (60%)')
        st.plotly_chart(fig_hist, use_container_width=True)

    fig_bar = px.bar(
        studenti.sort_values('progresso_medio', ascending=False),
        x='nome', y='progresso_medio',
        color='sufficiente',
        title="Progresso medio per studente",
        color_discrete_map={1: '#06d6a0', 0: '#f72585'},
        labels={'nome': '', 'progresso_medio': 'Progresso medio (%)', 'sufficiente': 'Sufficiente'},
    )
    fig_bar.add_hline(y=60, line_dash='dash', line_color='gray',
                      annotation_text='soglia 60%')
    fig_bar.update_layout(xaxis_tickangle=-40)
    st.plotly_chart(fig_bar, use_container_width=True)

    col_c, col_d = st.columns(2)
    with col_c:
        fig_isc = px.bar(
            studenti.sort_values('iscrizioni', ascending=False),
            x='nome', y='iscrizioni',
            title="Iscrizioni per studente",
            color_discrete_sequence=[COLORS[2]],
            labels={'nome': '', 'iscrizioni': 'Progetti iscritti'},
        )
        fig_isc.update_layout(xaxis_tickangle=-40)
        st.plotly_chart(fig_isc, use_container_width=True)

    with col_d:
        fig_comp = px.bar(
            studenti.sort_values('completati', ascending=False),
            x='nome', y='completati',
            title="Progetti completati (100%) per studente",
            color_discrete_sequence=[COLORS[4]],
            labels={'nome': '', 'completati': 'Completati'},
        )
        fig_comp.update_layout(xaxis_tickangle=-40)
        st.plotly_chart(fig_comp, use_container_width=True)

    st.divider()
    st.markdown("**Dettaglio studenti**")
    LABELS_S = {
        'nome': 'Nome', 'iscrizioni': 'Iscrizioni',
        'completati': 'Completati', 'progresso_medio': 'Progresso medio (%)',
        'valutazione': 'Valutazione (0-5)', 'sufficiente': 'Sufficiente',
    }
    st.dataframe(
        studenti[list(LABELS_S)].rename(columns=LABELS_S),
        use_container_width=True, hide_index=True,
    )


# ── Tab 3: Docenti ────────────────────────────────────────────────────────────
with tab3:
    st.caption("**Eccellente** = valutazione media ≥ 4 stelle  ·  i feedback sono lasciati dagli studenti iscritti ai loro progetti")

    col_a, col_b = st.columns(2)

    with col_a:
        fig_val = px.bar(
            docenti.sort_values('valutazione_media', ascending=False),
            x='nome', y='valutazione_media',
            color='eccellente',
            title="Valutazione media per docente",
            color_discrete_map={1: '#06d6a0', 0: '#f72585'},
            labels={'nome': '', 'valutazione_media': 'Stelle medie (1-5)', 'eccellente': 'Eccellente'},
        )
        fig_val.add_hline(y=4.0, line_dash='dash', line_color='gray',
                          annotation_text='soglia eccellente (4.0 ★)')
        fig_val.update_layout(xaxis_tickangle=-20)
        st.plotly_chart(fig_val, use_container_width=True)

    with col_b:
        fig_fb = px.bar(
            docenti.sort_values('n_feedback', ascending=False),
            x='nome', y='n_feedback',
            title="Feedback ricevuti per docente",
            color_discrete_sequence=[COLORS[1]],
            labels={'nome': '', 'n_feedback': 'Numero feedback'},
        )
        fig_fb.update_layout(xaxis_tickangle=-20)
        st.plotly_chart(fig_fb, use_container_width=True)

    # Feedback per progetto (solo quelli con almeno un feedback)
    proj_fb = progetti[progetti['n_feedback'] > 0].sort_values('n_feedback', ascending=False)
    if not proj_fb.empty:
        fig_pfb = px.bar(
            proj_fb, x='titolo', y='n_feedback',
            color='docente',
            title="Distribuzione feedback per progetto",
            labels={'titolo': '', 'n_feedback': 'Feedback ricevuti', 'docente': 'Docente'},
        )
        fig_pfb.update_layout(xaxis_tickangle=-40, legend_title='Docente')
        st.plotly_chart(fig_pfb, use_container_width=True)

    st.divider()
    st.markdown("**Dettaglio docenti**")
    LABELS_D = {
        'nome': 'Nome', 'n_progetti': 'Progetti creati',
        'n_feedback': 'Feedback ricevuti',
        'valutazione_media': 'Valutazione media (1-5)', 'eccellente': 'Eccellente',
    }
    st.dataframe(
        docenti[list(LABELS_D)].rename(columns=LABELS_D),
        use_container_width=True, hide_index=True,
    )


# ── Tab 4: AI ─────────────────────────────────────────────────────────────────
with tab4:
    st.subheader("Predizione sufficienza studente — Regressione Logistica")
    st.caption(
        "Il modello usa il numero di *iscrizioni*, i *completati* e la *valutazione media* "
        "per stimare se uno studente raggiungerà la sufficienza (progresso medio ≥ 60%)."
    )

    features = ['iscrizioni', 'completati', 'valutazione']
    target = 'sufficiente'

    if studenti[target].nunique() < 2:
        st.warning(
            "Non ci sono abbastanza dati: servono studenti sia sufficienti che non sufficienti. "
            "Verifica che il database contenga dati variati."
        )
    else:
        X, y = studenti[features], studenti[target]
        try:
            X_tr, X_te, y_tr, y_te = train_test_split(
                X, y, test_size=0.3, random_state=42, stratify=y
            )
        except ValueError:
            X_tr, X_te, y_tr, y_te = train_test_split(
                X, y, test_size=0.3, random_state=42
            )

        model = LogisticRegression(max_iter=1000)
        model.fit(X_tr, y_tr)
        acc = accuracy_score(y_te, model.predict(X_te)) * 100

        col_acc, col_info = st.columns([1, 3])
        col_acc.metric("Accuratezza modello", f"{acc:.1f}%")
        col_info.info(
            "Con pochi campioni l'accuratezza può variare molto — "
            "usala come indicazione, non come misura assoluta."
        )

        st.divider()
        st.markdown("**Prova il modello su uno studente ipotetico**")

        c1, c2, c3 = st.columns(3)
        n_isc  = c1.number_input("Iscrizioni (1-10)", 1, 10, 3)
        n_comp = c2.number_input("Completati (0-10)", 0, 10, 1)
        val    = c3.slider("Valutazione media (0-5)", 0.0, 5.0, 2.5, 0.1)

        pred = model.predict([[n_isc, n_comp, val]])[0]
        prob = model.predict_proba([[n_isc, n_comp, val]])[0][1]

        if pred == 1:
            st.success(f"✅ Lo studente è probabilmente **sufficiente** — confidenza: {prob * 100:.1f}%")
        else:
            st.error(f"❌ Lo studente è probabilmente **insufficiente** — confidenza: {(1 - prob) * 100:.1f}%")


# ── Tab 5: Export ─────────────────────────────────────────────────────────────
with tab5:
    st.subheader("Esporta i dati")

    exp1, exp2, exp3 = st.tabs(["Studenti", "Docenti", "Progetti"])

    with exp1:
        LABELS_S = {
            'nome': 'Nome', 'iscrizioni': 'Iscrizioni', 'completati': 'Completati',
            'progresso_medio': 'Progresso medio (%)', 'valutazione': 'Valutazione (0-5)',
            'sufficiente': 'Sufficiente',
        }
        df_s = studenti[list(LABELS_S)].rename(columns=LABELS_S)
        st.dataframe(df_s, use_container_width=True, hide_index=True)
        st.download_button(
            "📥 Scarica CSV studenti", df_s.to_csv(index=False).encode(),
            'studenti_export.csv', 'text/csv',
            use_container_width=True, type="primary",
        )

    with exp2:
        LABELS_D = {
            'nome': 'Nome', 'n_progetti': 'Progetti creati',
            'n_feedback': 'Feedback ricevuti',
            'valutazione_media': 'Valutazione media (1-5)', 'eccellente': 'Eccellente',
        }
        df_d = docenti[list(LABELS_D)].rename(columns=LABELS_D)
        st.dataframe(df_d, use_container_width=True, hide_index=True)
        st.download_button(
            "📥 Scarica CSV docenti", df_d.to_csv(index=False).encode(),
            'docenti_export.csv', 'text/csv',
            use_container_width=True, type="primary",
        )

    with exp3:
        LABELS_P = {
            'titolo': 'Titolo', 'stato': 'Stato', 'docente': 'Docente',
            'n_studenti': 'Studenti iscritti',
            'progresso_medio': 'Progresso medio (%)', 'n_feedback': 'Feedback ricevuti',
        }
        df_p = progetti[list(LABELS_P)].rename(columns=LABELS_P)
        st.dataframe(df_p, use_container_width=True, hide_index=True)
        st.download_button(
            "📥 Scarica CSV progetti", df_p.to_csv(index=False).encode(),
            'progetti_export.csv', 'text/csv',
            use_container_width=True, type="primary",
        )


# ── Auto-refresh ──────────────────────────────────────────────────────────────
if auto_refresh:
    time.sleep(10)
    st.rerun()
