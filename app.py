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
    /* Estilo para o seletor de data e inputs */
    div.stDateInput, div.stSelectbox, div.stNumberInput { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- SISTEMA DE ARQUIVOS (BANCO DE DADOS) ---
DB_FILE = "dados_financeiros.csv"

def salvar_dados(df):
    df.to_csv(DB_FILE, index=False)

def carregar_dados():
    if os.path.exists(DB_FILE):
        df_load = pd.read_csv(DB_FILE)
        df_load['Data'] = pd.to_datetime(df_load['Data'])
        return df_load
    return pd.DataFrame(columns=['Data', 'Descrição', 'Valor', 'Tipo', 'Categoria'])

# Inicialização da sessão
if 'dados' not in st.session_state:
    st.session_state.dados = carregar_dados()

# --- HEADER E FILTRO ---
st.markdown("<h1 style='text-align: center;'>🏡 Controle Familiar</h1>", unsafe_allow_html=True)

hoje = date.today()
meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

col_m, col_a = st.columns([2, 1])
mes_nome = col_m.selectbox("Mês de Referência", meses, index=hoje.month - 1)
ano_ref = col_a.number_input("Ano", value=hoje.year, step=1)
mes_num = meses.index(mes_nome) + 1

# Filtragem para a visualização
df_base = st.session_state.dados.copy()
if not df_base.empty:
    df_base['Data'] = pd.to_datetime(df_base['Data'])
    df_filtrado = df_base[(df_base['Data'].dt.month == mes_num) & (df_base['Data'].dt.year == ano_ref)]
else:
    df_filtrado = df_base

aba_resumo, aba_novo, aba_ajustes = st.tabs(["✨ Meu Mês", "➕ Novo", "⚙️ Ajustes"])

# --- ABA RESUMO ---
with aba_resumo:
    if not df_filtrado.empty:
        entradas = df_filtrado[df_filtrado['Tipo'] == 'Entrada']['Valor'].sum()
        saidas = df_filtrado[df_filtrado['Tipo'] == 'Saída']['Valor'].sum()
        saldo = entradas - saidas

        c1, c2 = st.columns(2)
        c1.metric("Ganhos", f"R$ {entradas:,.2f}")
        c2.metric("Gastos", f"R$ {saidas:,.2f}")
        
        # Barra de Saúde Financeira
        if entradas > 0:
            porcentagem = min(saidas / entradas, 1.0)
            st.write(f"**Uso da Renda: {porcentagem*100:.1f}%**")
            st.progress(porcentagem)
        
        st.markdown(f"""
            <div style="background: #3182CE; padding: 15px; border-radius: 20px; text-align: center; color: white; margin: 15px 0;">
                <p style='margin:0; font-size: 14px; opacity: 0.8;'>Saldo Final em {mes_nome}</p>
                <h2 style='margin:0; color: white;'>R$ {saldo:,.2f}</h2>
            </div>
        """, unsafe_allow_html=True)

        if saidas > 0:
            st.markdown("### 📊 Gastos por Categoria")
            fig = px.pie(df_filtrado[df_filtrado['Tipo'] == 'Saída'], values='Valor', names='Categoria', 
                         hole=0.6, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=True)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("### 🕒 Histórico do Mês")
        for idx, row in df_filtrado.sort_values(by='Data', ascending=False).iterrows():
            cor_v = "#38A169" if row['Tipo'] == "Entrada" else "#E53E3E"
            st.markdown(f"""
                <div class="transaction-card">
                    <div>
                        <strong style="color: #2D3748;">{row['Descrição']}</strong><br>
                        <span style="color: #A0AEC0; font-size: 11px;">{row['Categoria']} | {row['Data'].strftime('%d/%m')}</span>
                    </div>
                    <div style="color: {cor_v}; font-weight: bold;">R$ {row['Valor']:,.2f}</div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info(f"Nenhum registro encontrado para {mes_nome} de {ano_ref}.")

# --- ABA NOVO ---
with aba_novo:
    st.markdown("### ✍️ Registrar")
    with st.form("add_form", clear_on_submit=True):
        valor = st.number_input("Valor (R$)", min_value=0.0, step=1.0)
        desc = st.text_input("O que é?", placeholder="Ex: Compras no Carrefour")
        tipo = st.radio("Tipo", ["Saída", "Entrada"], horizontal=True)
        categoria = st.selectbox("Categoria", ["🛒 Mercado", "🏠 Moradia", "🚗 Transporte", "🍕 Lazer", "💡 Contas", "💰 Salário", "✨ Outros"])
        data_lan = st.date_input("Data", date.today())
        
        if st.form_submit_button("Salvar no Livro"):
            if desc and valor > 0:
                novo = pd.DataFrame([[pd.to_datetime(data_lan), desc, valor, tipo, categoria]], 
                                   columns=['Data', 'Descrição', 'Valor', 'Tipo', 'Categoria'])
                st.session_state.dados = pd.concat([st.session_state.dados, novo], ignore_index=True)
                salvar_dados(st.session_state.dados)
                st.toast("Sucesso!", icon="✅")
                st.rerun()
            else:
                st.warning("Por favor, preencha a descrição e o valor.")

# --- ABA AJUSTES ---
with aba_ajustes:
    st.markdown("### 🔧 Gerenciar Dados")
    if not df_filtrado.empty:
        st.write("Toque para remover um item deste mês:")
        for idx, row in df_filtrado.iterrows():
            if st.button(f"🗑️ Remover: {row['Descrição']} (R$ {row['Valor']})", key=f"del_{idx}"):
                st.session_state.dados = st.session_state.dados.drop(idx)
                salvar_dados(st.session_state.dados)
                st.rerun()
    
    st.divider()
    if st.button("🚨 Apagar todos os dados do App"):
        if st.checkbox("Eu tenho certeza que quero apagar tudo"):
            st.session_state.dados = pd.DataFrame(columns=['Data', 'Descrição', 'Valor', 'Tipo', 'Categoria'])
            salvar_dados(st.session_state.dados)
            st.rerun()
