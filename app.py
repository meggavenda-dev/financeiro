import streamlit as st
import pandas as pd
from datetime import date
import plotly.express as px
import os

# Configuração da página
st.set_page_config(page_title="MyFinance", page_icon="💳", layout="centered")

# CSS para melhorar a aparência no Mobile
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    div[data-testid="stExpander"] { border: none !important; box-shadow: none !important; }
    </style>
    """, unsafe_allow_html=True)

# --- PERSISTÊNCIA DE DADOS ---
DB_FILE = "finance_data.csv"

def carregar_dados():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE, parse_dates=['Data'])
    return pd.DataFrame(columns=['Data', 'Descrição', 'Valor', 'Tipo', 'Categoria'])

def salvar_dados(df):
    df.to_csv(DB_FILE, index=False)

if 'dados' not in st.session_state:
    st.session_state.dados = carregar_dados()

# --- HEADER ---
st.title("💳 MyFinance")
st.caption("Controle financeiro simples e rápido")

# --- RESUMO (CARDS) ---
df = st.session_state.dados
entradas = df[df['Tipo'] == 'Entrada']['Valor'].sum()
saidas = df[df['Tipo'] == 'Saída']['Valor'].sum()
saldo = entradas - saidas

c1, c2 = st.columns(2)
c1.metric("Ganhos", f"R$ {entradas:,.2f}")
c2.metric("Gastos", f"R$ {saidas:,.2f}", delta=f"-{saidas:,.2f}", delta_color="inverse")
st.metric("Saldo Atual", f"R$ {saldo:,.2f}")

# --- ENTRADA DE DADOS ---
with st.expander("➕ Novo Lançamento", expanded=False):
    with st.form("novo_registro", clear_on_submit=True):
        col_data, col_valor = st.columns(2)
        data = col_data.date_input("Data", date.today())
        valor = col_valor.number_input("Valor (R$)", min_value=0.0, step=0.50)
        
        desc = st.text_input("Descrição", placeholder="Ex: Mercado, Freelance...")
        
        col_tipo, col_cat = st.columns(2)
        tipo = col_tipo.selectbox("Fluxo", ["Saída", "Entrada"])
        
        # Categorias dinâmicas baseadas no tipo
        if tipo == "Saída":
            cat = col_cat.selectbox("Categoria", ["🏠 Casa", "🍔 Alimentação", "🚗 Transporte", "🎭 Lazer", "💡 Contas", "🛠 Outros"])
        else:
            cat = col_cat.selectbox("Categoria", ["💰 Salário", "📈 Investimento", "🎁 Presente", "🛠 Outros"])

        if st.form_submit_button("✅ Confirmar Lançamento", use_container_width=True):
            if desc and valor > 0:
                novo_item = pd.DataFrame([[pd.to_datetime(data), desc, valor, tipo, cat]], 
                                        columns=['Data', 'Descrição', 'Valor', 'Tipo', 'Categoria'])
                st.session_state.dados = pd.concat([st.session_state.dados, novo_item], ignore_index=True)
                salvar_dados(st.session_state.dados)
                st.toast("Lançado com sucesso!", icon="💰")
                st.rerun()
            else:
                st.error("Preencha a descrição e o valor.")

# --- VISUALIZAÇÃO ---
if not df.empty:
    st.divider()
    
    # Gráfico de Gastos por Categoria
    df_gastos = df[df['Tipo'] == 'Saída']
    if not df_gastos.empty:
        fig = px.pie(df_gastos, values='Valor', names='Categoria', hole=0.5,
                     color_discrete_sequence=px.colors.sequential.RdBu,
                     title="Distribuição de Gastos")
        fig.update_layout(showlegend=False, margin=dict(t=30, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)

    # Lista de Histórico Estilizada
    st.subheader("📋 Últimas Atividades")
    
    # Ordenar por data mais recente
    df_display = df.sort_values(by='Data', ascending=False).head(10)
    
    for i, row in df_display.iterrows():
        cor = "🟢" if row['Tipo'] == "Entrada" else "🔴"
        st.markdown(f"""
        **{cor} {row['Descrição']}** <small>{row['Categoria']} • {row['Data'].strftime('%d/%m/%Y')}</small>  
        **R$ {row['Valor']:,.2f}**
        ---
        """, unsafe_allow_html=True)

    if st.button("🗑 Limpar Todo Histórico"):
        st.session_state.dados = pd.DataFrame(columns=['Data', 'Descrição', 'Valor', 'Tipo', 'Categoria'])
        salvar_dados(st.session_state.dados)
        st.rerun()
else:
    st.info("Toque no botão '+' acima para começar.")
