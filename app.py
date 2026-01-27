import streamlit as st
import pandas as pd
from datetime import date
import plotly.express as px

# Configurações de Aparência
st.set_page_config(page_title="FamilyCash", layout="centered")

# CSS Customizado para transformar o Streamlit em um App Mobile Premium
st.markdown("""
    <style>
    /* Fundo e Container */
    .stApp { background-color: #0E1117; }
    
    /* Estilização dos Cards de Métrica */
    [data-testid="stMetric"] {
        background-color: #1E2129;
        border-radius: 15px;
        padding: 15px;
        border: 1px solid #2D3139;
        box-shadow: 5px 5px 15px rgba(0,0,0,0.2);
    }
    
    /* Botões Modernos */
    .stButton>button {
        width: 100%;
        border-radius: 25px;
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        font-weight: bold;
        border: none;
        padding: 10px;
    }

    /* Input Fields */
    input, select, textarea {
        border-radius: 10px !important;
    }

    /* Esconder o menu padrão do Streamlit para parecer App nativo */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZAÇÃO ---
if 'dados' not in st.session_state:
    st.session_state.dados = pd.DataFrame(columns=['Data', 'Descrição', 'Valor', 'Tipo', 'Categoria'])

# --- HEADER APP ---
st.markdown("<h2 style='text-align: center; color: white;'>💎 FamilyCash</h2>", unsafe_allow_html=True)

# Navegação por abas (Estilo Mobile)
aba1, aba2 = st.tabs(["📊 Visão Geral", "➕ Lançar"])

# --- ABA 1: VISÃO GERAL ---
with aba1:
    # Filtro de Mês Rápido
    mes_atual = date.today().strftime("%m")
    df = st.session_state.dados
    df['Data'] = pd.to_datetime(df['Data'])
    
    # Resumo Matemático
    entradas = df[df['Tipo'] == 'Entrada']['Valor'].sum()
    saidas = df[df['Tipo'] == 'Saída']['Valor'].sum()
    saldo = entradas - saidas

    # Layout de Cards
    c1, c2 = st.columns(2)
    c1.metric("Ganhos", f"R$ {entradas:,.2f}")
    c2.metric("Gastos", f"R$ {saidas:,.2f}", delta_color="inverse")
    st.metric("Saldo em Conta", f"R$ {saldo:,.2f}")

    if not df.empty:
        # Gráfico Donut Moderno
        df_saidas = df[df['Tipo'] == 'Saída']
        if not df_saidas.empty:
            fig = px.pie(df_saidas, values='Valor', names='Categoria', hole=0.7,
                         color_discrete_sequence=px.colors.sequential.AliceBlue_r)
            fig.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', 
                              plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"),
                              margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
        
        # Lista de transações estilo Apple Wallet
        st.markdown("### 📋 Recentes")
        for idx, row in df.sort_values(by='Data', ascending=False).head(5).iterrows():
            cor_valor = "#00FF7F" if row['Tipo'] == "Entrada" else "#FF4B4B"
            simbolo = "+" if row['Tipo'] == "Entrada" else "-"
            st.markdown(f"""
                <div style="background-color: #1E2129; padding: 15px; border-radius: 15px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="color: white; font-weight: bold;">{row['Descrição']}</span><br>
                            <span style="color: #888; font-size: 12px;">{row['Categoria']} • {row['Data'].strftime('%d/%m')}</span>
                        </div>
                        <span style="color: {cor_valor}; font-weight: bold;">{simbolo} R$ {row['Valor']:,.2f}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Toque na aba 'Lançar' para começar!")

# --- ABA 2: LANÇAR ---
with aba2:
    st.markdown("### Novo Registro")
    with st.form("form_add", clear_on_submit=True):
        valor = st.number_input("Valor", min_value=0.0, step=1.0)
        desc = st.text_input("Descrição", placeholder="Ex: Aluguel, Supermercado")
        tipo = st.selectbox("Tipo", ["Saída", "Entrada"])
        categoria = st.selectbox("Categoria", ["🏠 Casa", "🛒 Comida", "🚗 Transporte", "💊 Saúde", "🎮 Lazer", "💰 Salário", "🛠 Outros"])
        data = st.date_input("Data", date.today())
        
        if st.form_submit_button("Confirmar Lançamento"):
            if desc and valor > 0:
                novo = pd.DataFrame([[pd.to_datetime(data), desc, valor, tipo, categoria]], 
                                   columns=['Data', 'Descrição', 'Valor', 'Tipo', 'Categoria'])
                st.session_state.dados = pd.concat([st.session_state.dados, novo], ignore_index=True)
                st.success("Salvo!")
                st.rerun()
