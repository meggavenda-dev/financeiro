import streamlit as st
import pandas as pd
from datetime import date
import plotly.express as px

# Configuração Mobile-First
st.set_page_config(page_title="Finanças Casa", page_icon="🏠", layout="centered")

# CSS para esconder menus desnecessários e ajustar fontes
st.markdown("""
    <style>
    [data-testid="stHeader"] {background: rgba(0,0,0,0);}
    .stMetric { background-color: #ffffff; border-radius: 10px; padding: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

if 'dados' not in st.session_state:
    st.session_state.dados = pd.DataFrame(columns=['Data', 'Descrição', 'Valor', 'Tipo', 'Categoria'])

# --- LÓGICA DE DATAS ---
hoje = date.today()
meses_nomes = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

st.title("🏠 Finanças da Casa")

# Seletor de Mês no topo (Fácil de tocar no celular)
col_m, col_a = st.columns([2, 1])
mes_sel = col_m.selectbox("Mês de Referência", meses_nomes, index=hoje.month - 1)
ano_sel = col_a.number_input("Ano", value=hoje.year)

# --- FILTRAGEM ---
df = st.session_state.dados
df['Data'] = pd.to_datetime(df['Data'])
df_mes = df[(df['Data'].dt.month == meses_nomes.index(mes_sel) + 1) & (df['Data'].dt.year == ano_sel)]

# --- RESUMO VISUAL ---
if not df_mes.empty:
    entradas = df_mes[df_mes['Tipo'] == 'Entrada']['Valor'].sum()
    saidas = df_mes[df_mes['Tipo'] == 'Saída']['Valor'].sum()
    saldo = entradas - saidas

    # Cards de Resumo
    c1, c2 = st.columns(2)
    c1.metric("Recebido", f"R$ {entradas:,.2f}")
    c2.metric("Gasto", f"R$ {saidas:,.2f}", delta=f"R$ {saldo:,.2f}", delta_color="normal")
    
    # Barra de Saúde Financeira
    if entradas > 0:
        progresso = min(saidas / entradas, 1.0)
        st.write(f"**Uso da Renda: {progresso*100:.1f}%**")
        st.progress(progresso)
else:
    st.warning(f"Sem registros para {mes_sel}/{ano_sel}")

# --- FORMULÁRIO (EXPANDER) ---
with st.expander("➕ Lançar Gasto/Renda"):
    with st.form("add_lançamento", clear_on_submit=True):
        valor = st.number_input("Valor R$", min_value=0.0, step=10.0)
        desc = st.text_input("O que é?")
        tipo = st.radio("Tipo", ["Saída", "Entrada"], horizontal=True)
        cat = st.selectbox("Categoria", ["🛒 Mercado", "🔌 Contas Fixas", "🚗 Transporte", "🍕 Lazer", "💰 Salário", "🛠 Outros"])
        data_lan = st.date_input("Data", date.today())
        
        if st.form_submit_button("Salvar Registro", use_container_width=True):
            novo = pd.DataFrame([[pd.to_datetime(data_lan), desc, valor, tipo, cat]], 
                               columns=['Data', 'Descrição', 'Valor', 'Tipo', 'Categoria'])
            st.session_state.dados = pd.concat([st.session_state.dados, novo], ignore_index=True)
            st.rerun()

# --- GRÁFICO ---
if not df_mes.empty and saidas > 0:
    st.subheader("Para onde foi o dinheiro?")
    fig = px.pie(df_mes[df_mes['Tipo'] == 'Saída'], values='Valor', names='Categoria', hole=0.4)
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

# --- HISTÓRICO EM CARDS (MELHOR QUE TABELA NO CELULAR) ---
st.subheader("📋 Movimentações")
if not df_mes.empty:
    for i, row in df_mes.sort_values("Data", ascending=False).iterrows():
        cor = "#2ecc71" if row['Tipo'] == 'Entrada' else "#e74c3c"
        with st.container():
            st.markdown(f"""
            <div style="border-left: 5px solid {cor}; padding: 10px; margin-bottom: 10px; background: #fff; border-radius: 5px;">
                <small>{row['Data'].strftime('%d/%m')}</small> | <b>{row['Descrição']}</b><br>
                <span style="color: {cor}; font-weight: bold;">R$ {row['Valor']:,.2f}</span> | <small>{row['Categoria']}</small>
            </div>
            """, unsafe_allow_html=True)
