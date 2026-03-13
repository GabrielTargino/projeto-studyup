import streamlit as st
import time
import plotly.express as px
from database.connection import StudyDB
from logic.pomodoro import formatar_tempo
from logic.analytics import buscar_dados_progresso, buscar_alertas_revisao

# Inicialização da classe de banco de dados
db = StudyDB()

st.set_page_config(page_title="StudyUp", layout="wide")

# CSS Customizado
st.markdown("""
    <style>
    div[data-baseweb="select"], button, .stSelectbox { cursor: pointer !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 StudyUp - Gerenciador de Estudos")

# --- MENU LATERAL ---
st.sidebar.header("Menu de Navegação")
opcao = st.sidebar.selectbox("Ir para:", ["Dashboard", "Cadastrar Disciplina", "Cadastrar Tópico", "Pomodoro", "Flashcards"])

# --- PÁGINA: DASHBOARD ---
if opcao == "Dashboard":
    st.header("📊 Painel de Desempenho")
    df_progresso = buscar_dados_progresso()
    
    if df_progresso.empty:
        st.warning("Ainda não há dados. Realize uma sessão de estudo!")
    else:
        fig = px.bar(df_progresso, x='Disciplina', y='percentual', color='percentual',
                     color_continuous_scale='RdYlGn', range_y=[0, 100], text_auto='.1f')
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("🔔 Tópicos para Revisar Hoje")
    df_revisao = buscar_alertas_revisao()
    if df_revisao.empty:
        st.success("Tudo em dia!")
    else:
        st.dataframe(df_revisao, use_container_width=True)

# --- PÁGINA: CADASTRAR DISCIPLINA ---
elif opcao == "Cadastrar Disciplina":
    st.header("📚 Gerenciar Disciplinas")
    nova_disc = st.text_input("Nome da Disciplina:")
    if st.button("Salvar Disciplina"):
        if nova_disc:
            if db.adicionar_disciplina(nova_disc):
                st.success("Disciplina adicionada!")
            else:
                st.error("Erro: Já existe ou campo inválido.")
    
    st.divider()
    for d in db.listar_disciplinas():
        st.write(f"- {d[1]}")

# --- PÁGINA: CADASTRAR TÓPICO ---
elif opcao == "Cadastrar Tópico":
    st.header("📝 Cadastrar Conteúdo")
    disciplinas = db.listar_disciplinas()
    if not disciplinas:
        st.warning("Cadastre uma disciplina primeiro!")
    else:
        dict_disc = {d[1]: d[0] for d in disciplinas}
        escolha = st.selectbox("Selecione a Disciplina:", list(dict_disc.keys()))
        nome_topico = st.text_input("Nome do Tópico:")
        if st.button("Salvar Tópico"):
            if nome_topico:
                db.adicionar_topico(dict_disc[escolha], nome_topico)
                st.success(f"Tópico '{nome_topico}' adicionado!")

# --- PÁGINA: POMODORO ---
elif opcao == "Pomodoro":
    st.header("⏳ Timer Pomodoro")
    disciplinas = db.listar_disciplinas()
    if not disciplinas:
        st.info("Cadastre disciplina e tópico antes.")
    else:
        dict_disc = {d[1]: d[0] for d in disciplinas}
        esc_disc = st.selectbox("Disciplina:", list(dict_disc.keys()))
        topicos = db.listar_topicos_por_disciplina(dict_disc[esc_disc])
        
        if not topicos:
            st.warning("Cadastre tópicos para esta disciplina.")
        else:
            dict_topicos = {t[2]: t[0] for t in topicos}
            esc_topico = st.selectbox("Tópico:", list(dict_topicos.keys()))
            
            if st.button("Iniciar 25min"):
                tempo = 25 * 60
                prog = st.progress(0)
                txt = st.empty()
                for s in range(tempo, -1, -1):
                    txt.subheader(f"Restante: {formatar_tempo(s)}")
                    prog.progress((tempo - s) / tempo)
                    time.sleep(1)
                st.success("Sessão Finalizada!")
                st.balloons()

            st.divider()
            st.subheader("📊 Registrar Desempenho")
            with st.form("form_desempenho"):
                col1, col2 = st.columns(2)
                q = col1.number_input("Questões", min_value=0, step=1)
                a = col2.number_input("Acertos", min_value=0, step=1)
                if st.form_submit_button("Salvar"):
                    if q > 0 and a <= q:
                        db.registrar_desempenho(dict_topicos[esc_topico], q, a)
                        st.success("Desempenho salvo!")
                    elif a > q:
                        st.error("Acertos não podem ser maiores que o total de questões.")

# --- PÁGINA: FLASHCARDS ---
elif opcao == "Flashcards":
    st.header("🗂️ Flashcards")
    aba_cad, aba_est = st.tabs(["🆕 Cadastrar", "🧠 Estudar"])

    with aba_cad:
        disciplinas = db.listar_disciplinas()
        if disciplinas:
            dict_disc = {d[1]: d[0] for d in disciplinas}
            esc_disc = st.selectbox("Disciplina:", list(dict_disc.keys()), key="fc_d")
            topicos = db.listar_topicos_por_disciplina(dict_disc[esc_disc])
            if topicos:
                dict_topicos = {t[2]: t[0] for t in topicos}
                esc_topico = st.selectbox("Tópico:", list(dict_topicos.keys()), key="fc_t")
                p = st.text_area("Pergunta:")
                r = st.text_area("Resposta:")
                if st.button("Salvar Flashcard"):
                    if p and r:
                        db.adicionar_flashcard(dict_topicos[esc_topico], p, r)
                        st.success("Flashcard salvo!")

    with aba_est:
        # Reutilizando seletores para filtrar estudo
        disciplinas = db.listar_disciplinas()
        if disciplinas:
            dict_disc = {d[1]: d[0] for d in disciplinas}
            esc_disc_est = st.selectbox("Filtrar Disciplina:", list(dict_disc.keys()), key="est_d")
            topicos_est = db.listar_topicos_por_disciplina(dict_disc[esc_disc_est])
            if topicos_est:
                dict_topicos_est = {t[2]: t[0] for t in topicos_est}
                esc_topico_est = st.selectbox("Filtrar Tópico:", list(dict_topicos_est.keys()), key="est_t")
                cards = db.listar_flashcards_por_topico(dict_topicos_est[esc_topico_est])
                for card in cards:
                    with st.expander(f"❓ {card[2]}"):
                        st.write(f"💡 **Resposta:** {card[3]}")