import streamlit as st
import pandas as pd
from datetime import date
import plotly.express as px
import os

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Minha Casa", page_icon="🏡", layout="centered")

# CSS Amigável (Soft UI)
st.markdown("""
    <style>
    .stApp { background-color: #F7F9FC; }
    h1, h2, h3 { color: #2C3E50; font-family: 'Segoe UI', sans-serif; }
    [data-testid="stMetric"] {
        background-color: #FFFFFF; border-radius: 20px; padding: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #EDF2F7;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #FFFFFF; border-radius: 12px; padding: 8px 16px; color: #718096;
    }
    .stTabs [aria-selected="true"] { background-color: #EBF8FF !important; color: #3182CE !important; }
    .stButton>button {
        width: 100%; border-radius: 15px; background: #3182CE; color: white; border: none; padding: 10px;
    }
    .transaction-card {
        background-color: #FFFFFF; padding: 12px; border-radius: 15px; margin-bottom: 8px;
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02); border: 1px solid #F0F4F8;
    }
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE DADOS ---
DB_FILE = "dados_financeiros.csv"
META_FILE = "metas_financeiras.csv"

def carregar_dados():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['Data'] = pd.to_datetime(df['Data'])
        return df
    return pd.DataFrame(columns=['Data', 'Descrição', 'Valor', 'Tipo', 'Categoria'])

def carregar_metas():
    if os.path.exists(META_FILE):
        return pd.read_csv(META_FILE, index_col='Categoria').to_dict()['Limite']
    return {}

# Inicialização
if 'dados' not in st.session_state:
    st.session_state.dados = carregar_dados()
if 'metas' not in st.session_state:
    st.session_state.metas = carregar_metas()

CATEGORIAS = ["🛒 Mercado", "🏠 Moradia", "🚗 Transporte", "🍕 Lazer", "💡 Contas", "💰 Salário", "✨ Outros"]

# --- HEADER ---
st.markdown("<h1 style='text-align: center;'>🏡 Controle Familiar</h1>", unsafe_allow_html=True)

hoje = date.today()
meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

c_m, c_a = st.columns([2, 1])
mes_nome = c_m.selectbox("Mês", meses, index=hoje.month - 1)
ano_ref = c_a.number_input("Ano", value=hoje.year, step=1)
mes_num = meses.index(mes_nome) + 1

# Filtragem
df_filtrado = st.session_state.dados.copy()
if not df_filtrado.empty:
    df_filtrado = df_filtrado[(df_filtrado['Data'].dt.month == mes_num) & (df_filtrado['Data'].dt.year == ano_ref)]

aba_resumo, aba_novo, aba_metas, aba_ajustes = st.tabs(["✨ Meu Mês", "➕ Novo", "🎯 Metas", "⚙️"])

# --- ABA RESUMO ---
with aba_resumo:
    if not df_filtrado.empty:
        entradas = df_filtrado[df_filtrado['Tipo'] == 'Entrada']['Valor'].sum()
        saidas = df_filtrado[df_filtrado['Tipo'] == 'Saída']['Valor'].sum()
        
        c1, c2 = st.columns(2)
        c1.metric("Ganhos", f"R$ {entradas:,.2f}")
        c2.metric("Gastos", f"R$ {saidas:,.2f}")

        # --- SEÇÃO DE METAS NO RESUMO ---
        if st.session_state.metas:
            st.markdown("### 🎯 Limite por Categoria")
            gastos_por_cat = df_filtrado[df_filtrado['Tipo'] == 'Saída'].groupby('Categoria')['Valor'].sum()
            
            for cat, limite in st.session_state.metas.items():
                if limite > 0:
                    gasto_atual = gastos_por_cat.get(cat, 0)
                    progresso = min(gasto_atual / limite, 1.0)
                    cor = "red" if gasto_atual > limite else "green"
                    st.write(f"**{cat}**: R$ {gasto_atual:,.2f} de R$ {limite:,.2f}")
                    st.progress(progresso)
                    if gasto_atual > limite:
                        st.caption(f"⚠️ Você ultrapassou R$ {gasto_atual - limite:,.2f} do limite!")

        st.markdown(f"### 🕒 Histórico de {mes_nome}")
        for idx, row in df_filtrado.sort_values(by='Data', ascending=False).iterrows():
            cor_v = "#38A169" if row['Tipo'] == "Entrada" else "#E53E3E"
            st.markdown(f"""
                <div class="transaction-card">
                    <div>
                        <strong>{row['Descrição']}</strong><br>
                        <small>{row['Categoria']} | {row['Data'].strftime('%d/%m')}</small>
                    </div>
                    <div style="color: {cor_v}; font-weight: bold;">R$ {row['Valor']:,.2f}</div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Nenhum dado este mês.")

# --- ABA NOVO ---
with aba_novo:
    with st.form("add_form", clear_on_submit=True):
        valor = st.number_input("Valor (R$)", min_value=0.0)
        desc = st.text_input("Descrição")
        tipo = st.radio("Tipo", ["Saída", "Entrada"], horizontal=True)
        cat = st.selectbox("Categoria", CATEGORIAS)
        data_lan = st.date_input("Data", date.today())
        if st.form_submit_button("Salvar"):
            novo = pd.DataFrame([[pd.to_datetime(data_lan), desc, valor, tipo, cat]], columns=['Data', 'Descrição', 'Valor', 'Tipo', 'Categoria'])
            st.session_state.dados = pd.concat([st.session_state.dados, novo], ignore_index=True)
            st.session_state.dados.to_csv(DB_FILE, index=False)
            st.rerun()

# --- ABA METAS ---
with aba_metas:
    st.markdown("### 🎯 Definir Orçamentos")
    st.caption("Quanto você planeja gastar no máximo em cada categoria por mês?")
    
    for cat in CATEGORIAS:
        if cat != "💰 Salário":
            atual = st.session_state.metas.get(cat, 0.0)
            nova_meta = st.number_input(f"Limite para {cat}", min_value=0.0, value=float(atual), key=f"meta_{cat}")
            st.session_state.metas[cat] = nova_meta
    
    if st.button("Salvar Metas"):
        df_metas = pd.DataFrame.from_dict(st.session_state.metas, orient='index', columns=['Limite'])
        df_metas.index.name = 'Categoria'
        df_metas.to_csv(META_FILE)
        st.success("Metas atualizadas!")
        st.rerun()

# --- ABA AJUSTES ---
with aba_ajustes:
    if st.button("🗑️ Limpar Todos os Dados"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        if os.path.exists(META_FILE): os.remove(META_FILE)
        st.session_state.dados = pd.DataFrame(columns=['Data', 'Descrição', 'Valor', 'Tipo', 'Categoria'])
        st.session_state.metas = {}
        st.rerun()
