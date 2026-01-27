import streamlit as st
import pandas as pd
from datetime import date
import plotly.express as px
import os

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Minha Casa", page_icon="🏡", layout="centered")

# CSS Avançado para Total Responsividade e Centralização (Mobile-First)
st.markdown("""
    <style>
    /* Fundo e Fontes */
    .stApp { background-color: #F7F9FC; }
    h1, h2, h3 { color: #2C3E50; font-family: 'Segoe UI', sans-serif; text-align: center; }
    
    /* Centralizar e tornar as ABAS RESPONSIVAS (Estilo App Mobile) */
    .stTabs [data-baseweb="tab-list"] {
        display: flex;
        justify-content: center; 
        gap: 4px;
        width: 100%;
        padding: 0px;
    }

    .stTabs [data-baseweb="tab"] {
        flex-grow: 1; 
        text-align: center;
        background-color: #FFFFFF;
        border-radius: 10px 10px 0px 0px;
        padding: 8px 2px !important;
        color: #718096;
        min-width: 50px; 
        font-size: 12px; /* Ajustado para caber 5 abas em telas pequenas */
    }

    /* Estilo da Aba Ativa */
    .stTabs [aria-selected="true"] {
        background-color: #EBF8FF !important;
        color: #3182CE !important;
        border-bottom: 3px solid #3182CE !important;
        font-weight: bold;
    }

    /* Cards de Métricas */
    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        border-radius: 20px;
        padding: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border: 1px solid #EDF2F7;
    }

    /* Botões Grandes para Mobile (Dedos) */
    .stButton>button {
        width: 100%;
        border-radius: 15px;
        background: #3182CE;
        color: white;
        border: none;
        padding: 12px;
        font-weight: bold;
    }

    /* Listagem de Transações */
    .transaction-card {
        background-color: #FFFFFF;
        padding: 12px;
        border-radius: 15px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02);
        border: 1px solid #F0F4F8;
    }

    /* Card de Reserva Premium */
    .reserva-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 20px;
    }

    /* UI Tweak: Esconder menus para parecer App nativo */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Espaçamento Mobile */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 5rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE DADOS ---
DB_FILE = "dados_financeiros.csv"
META_FILE = "metas_financeiras.csv"
FIXO_FILE = "gastos_fixos.csv"

def carregar_dados(file, columns):
    if os.path.exists(file):
        df = pd.read_csv(file)
        if 'Data' in df.columns: 
            df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        return df
    return pd.DataFrame(columns=columns)

# Inicialização de Estado
if 'dados' not in st.session_state:
    st.session_state.dados = carregar_dados(DB_FILE, ['Data', 'Descrição', 'Valor', 'Tipo', 'Categoria'])
if 'metas' not in st.session_state:
    if os.path.exists(META_FILE):
        st.session_state.metas = pd.read_csv(META_FILE, index_col='Categoria').to_dict()['Limite']
    else: st.session_state.metas = {}
if 'fixos' not in st.session_state:
    st.session_state.fixos = carregar_dados(FIXO_FILE, ['Descrição', 'Valor', 'Categoria'])

CATEGORIAS = ["🛒 Mercado", "🏠 Moradia", "🚗 Transporte", "🍕 Lazer", "💡 Contas", "💰 Salário", "✨ Outros"]
meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

# --- HEADER ---
st.markdown("<h1>🏡 Controle Familiar</h1>", unsafe_allow_html=True)

hoje = date.today()
c_m, c_a = st.columns([2, 1])
mes_nome = c_m.selectbox("Mês", meses, index=hoje.month - 1)
ano_ref = c_a.number_input("Ano", value=hoje.year, step=1)
mes_num = meses.index(mes_nome) + 1

# --- PROCESSAMENTO ---
df_geral = st.session_state.dados.copy()
if not df_geral.empty:
    df_geral['Data'] = pd.to_datetime(df_geral['Data'])
    df_mes = df_geral[(df_geral['Data'].dt.month == mes_num) & (df_geral['Data'].dt.year == ano_ref)]
    
    mes_ant = 12 if mes_num == 1 else mes_num - 1
    ano_ant = ano_ref - 1 if mes_num == 1 else ano_ref
    df_ant = df_geral[(df_geral['Data'].dt.month == mes_ant) & (df_geral['Data'].dt.year == ano_ant)]
else:
    df_mes = pd.DataFrame()
    df_ant = pd.DataFrame()

# ABAS CENTRALIZADAS E RESPONSIVAS
aba_resumo, aba_novo, aba_metas, aba_reserva, aba_sonhos = st.tabs(["✨ Mês", "➕ Novo", "🎯 Metas", "🏦 Caixa", "🎯 Sonhos"])

# --- ABA RESUMO ---
with aba_resumo:
    if not df_mes.empty:
        entradas = df_mes[df_mes['Tipo'] == 'Entrada']['Valor'].sum()
        saidas = df_mes[df_mes['Tipo'] == 'Saída']['Valor'].sum()
        
        c1, c2 = st.columns(2)
        c1.metric("Ganhos", f"R$ {entradas:,.2f}")
        c2.metric("Gastos", f"R$ {saidas:,.2f}")

        if not df_ant.empty:
            saidas_ant = df_ant[df_ant['Tipo'] == 'Saída']['Valor'].sum()
            fig_comp = px.bar(
                x=[meses[mes_ant-1], mes_nome], 
                y=[saidas_ant, saidas],
                title="Gastos vs Mês Anterior",
                color_discrete_sequence=["#CBD5E0", "#3182CE"]
            )
            fig_comp.update_layout(height=230, showlegend=False, margin=dict(t=30, b=0, l=0, r=0))
            st.plotly_chart(fig_comp, use_container_width=True)

        if st.session_state.metas:
            with st.expander("🎯 Status das Metas"):
                gastos_cat = df_mes[df_mes['Tipo'] == 'Saída'].groupby('Categoria')['Valor'].sum()
                for cat, lim in st.session_state.metas.items():
                    if lim > 0:
                        atual = gastos_cat.get(cat, 0)
                        st.write(f"**{cat}** (R$ {atual:,.0f} / {lim:,.0f})")
                        st.progress(min(atual/lim, 1.0))

        st.markdown(f"### Histórico")
        for idx, row in df_mes.sort_values(by='Data', ascending=False).iterrows():
            cor = "#38A169" if row['Tipo'] == "Entrada" else "#E53E3E"
            st.markdown(f'<div class="transaction-card"><div><strong>{row["Descrição"]}</strong><br><small>{row["Categoria"]}</small></div><div style="color: {cor}; font-weight: bold;">R$ {row["Valor"]:,.2f}</div></div>', unsafe_allow_html=True)
    else:
        st.info("Nenhum dado este mês.")

# --- ABA NOVO ---
with aba_novo:
    aba_unit, aba_fixo = st.tabs(["Único", "🗓️ Fixos"])
    with aba_unit:
        with st.form("form_novo", clear_on_submit=True):
            v = st.number_input("Valor", min_value=0.0)
            d = st.text_input("Descrição")
            t = st.radio("Tipo", ["Saída", "Entrada"], horizontal=True)
            c = st.selectbox("Categoria", CATEGORIAS, key="cat_unit")
            dt = st.date_input("Data", date.today())
            fixo_check = st.checkbox("Salvar como Fixo")
            if st.form_submit_button("Salvar"):
                novo = pd.DataFrame([[pd.to_datetime(dt), d, v, t, c]], columns=['Data', 'Descrição', 'Valor', 'Tipo', 'Categoria'])
                st.session_state.dados = pd.concat([st.session_state.dados, novo], ignore_index=True)
                st.session_state.dados.to_csv(DB_FILE, index=False)
                if fixo_check:
                    n_fixo = pd.DataFrame([[d, v, c]], columns=['Descrição', 'Valor', 'Categoria'])
                    st.session_state.fixos = pd.concat([st.session_state.fixos, n_fixo], ignore_index=True).drop_duplicates()
                    st.session_state.fixos.to_csv(FIXO_FILE, index=False)
                st.rerun()
    with aba_fixo:
        st.markdown("### Lançar Recorrentes")
        if not st.session_state.fixos.empty:
            for idx, row in st.session_state.fixos.iterrows():
                col1, col2 = st.columns([3, 1])
                col1.write(f"**{row['Descrição']}** R$ {row['Valor']:,.2f}")
                if col2.button("OK", key=f"f_{idx}"):
                    df_f = pd.to_datetime(date(ano_ref, mes_num, 1))
                    n = pd.DataFrame([[df_f, row['Descrição'], row['Valor'], "Saída", row['Categoria']]], columns=['Data', 'Descrição', 'Valor', 'Tipo', 'Categoria'])
                    st.session_state.dados = pd.concat([st.session_state.dados, n], ignore_index=True)
                    st.session_state.dados.to_csv(DB_FILE, index=False)
                    st.toast("Lançado!")
                    st.rerun()
        else: st.caption("Sem fixos cadastrados.")

# --- ABA METAS ---
with aba_metas:
    for cat in CATEGORIAS:
        if cat != "💰 Salário":
            st.session_state.metas[cat] = st.number_input(f"Meta {cat}", min_value=0.0, value=float(st.session_state.metas.get(cat, 0)))
    if st.button("Salvar Metas"):
        pd.DataFrame.from_dict(st.session_state.metas, orient='index', columns=['Limite']).to_csv(META_FILE)
        st.success("Metas salvas!")

# --- ABA RESERVA ---
with aba_reserva:
    total_in = df_geral[df_geral['Tipo'] == 'Entrada']['Valor'].sum() if not df_geral.empty else 0
    total_out = df_geral[df_geral['Tipo'] == 'Saída']['Valor'].sum() if not df_geral.empty else 0
    balanco = total_in - total_out
    
    st.markdown(f'<div class="reserva-card"><p style="margin:0;opacity:0.8">Patrimônio Acumulado</p><h2>R$ {balanco:,.2f}</h2></div>', unsafe_allow_html=True)
    
    if not df_geral.empty:
        df_geral['MesAno'] = df_geral['Data'].dt.to_period('M').astype(str)
        mensal = df_geral.groupby(['MesAno', 'Tipo'])['Valor'].sum().unstack(fill_value=0)
        if 'Entrada' in mensal and 'Saída' in mensal:
            st.line_chart(mensal['Entrada'] - mensal['Saída'])

    if st.button("🚨 Resetar Tudo"):
        for f in [DB_FILE, META_FILE, FIXO_FILE]:
            if os.path.exists(f): os.remove(f)
        st.session_state.clear()
        st.rerun()

# --- ABA SONHOS ---
with aba_sonhos:
    st.markdown("### 🎯 Calculadora de Sonhos")
    n_sonho = st.text_input("Objetivo", placeholder="Ex: Reforma")
    v_sonho = st.number_input("Custo (R$)", min_value=0.0, key="v_sonho")
    
    if not df_geral.empty and v_sonho > 0:
        df_geral['MesAno'] = df_geral['Data'].dt.to_period('M').astype(str)
        bal_m = df_geral.groupby(['MesAno', 'Tipo'])['Valor'].sum().unstack(fill_value=0)
        if 'Entrada' in bal_m and 'Saída' in bal_m:
            sobra_m = (bal_m['Entrada'] - bal_m['Saída']).mean()
            if sobra_m > 0:
                m_faltam = int(v_sonho / sobra_m) + 1
                st.success(f"Sobra média: R$ {sobra_m:,.2f}/mês")
                st.info(f"Para o sonho **{n_sonho}**, faltam aprox. **{m_faltam} meses**.")
                st.progress(min(max(balanco/v_sonho, 0.0), 1.0))
            else: st.warning("Sua sobra média está negativa.")
