import streamlit as st
import pandas as pd
from datetime import date
import plotly.express as px

# Configuração da Página
st.set_page_config(page_title="Minha Casa", page_icon="🏡", layout="centered")

# CSS Customizado para Visual Amigável (Soft UI)
st.markdown("""
    <style>
    /* Fundo suave */
    .stApp { background-color: #F7F9FC; }
    
    /* Títulos e textos */
    h1, h2, h3 { color: #2C3E50; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    /* Cards de métricas brancos e arredondados */
    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border: 1px solid #EDF2F7;
    }
    
    /* Estilização das Abas */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #FFFFFF;
        border-radius: 10px 10px 0px 0px;
        padding: 10px 20px;
        color: #718096;
    }
    .stTabs [aria-selected="true"] { background-color: #EBF8FF !important; color: #3182CE !important; font-weight: bold; }

    /* Botão Principal */
    .stButton>button {
        width: 100%;
        border-radius: 15px;
        background: #3182CE;
        color: white;
        border: none;
        padding: 12px;
        transition: 0.3s;
    }
    .stButton>button:hover { background: #2B6CB0; transform: translateY(-1px); }

    /* Card de Transação */
    .transaction-card {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 15px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02);
        border: 1px solid #F0F4F8;
    }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZAÇÃO ---
if 'dados' not in st.session_state:
    st.session_state.dados = pd.DataFrame(columns=['Data', 'Descrição', 'Valor', 'Tipo', 'Categoria'])

# --- CONTEÚDO ---
st.markdown("<h1 style='text-align: center;'>🏡 Finanças da Família</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #718096;'>Tudo organizado, vida tranquila.</p>", unsafe_allow_html=True)

aba_resumo, aba_novo = st.tabs(["✨ Meu Mês", "➕ Novo Gasto"])

with aba_resumo:
    df = st.session_state.dados
    df['Data'] = pd.to_datetime(df['Data'])
    
    # Cálculos
    entradas = df[df['Tipo'] == 'Entrada']['Valor'].sum()
    saidas = df[df['Tipo'] == 'Saída']['Valor'].sum()
    saldo = entradas - saidas

    # Resumo visual em colunas
    c1, c2 = st.columns(2)
    c1.metric("Ganhos", f"R$ {entradas:,.2f}")
    c2.metric("Gastos", f"R$ {saidas:,.2f}")
    
    st.markdown(f"""
        <div style="background: #3182CE; padding: 20px; border-radius: 20px; text-align: center; color: white; margin-bottom: 25px;">
            <p style='margin:0; font-size: 14px; opacity: 0.9;'>Saldo Disponível</p>
            <h2 style='margin:0; color: white;'>R$ {saldo:,.2f}</h2>
        </div>
    """, unsafe_allow_html=True)

    if not df.empty:
        # Gráfico Amigável
        st.markdown("### 📊 Para onde vai o dinheiro?")
        df_saidas = df[df['Tipo'] == 'Saída']
        if not df_saidas.empty:
            fig = px.pie(df_saidas, values='Valor', names='Categoria', hole=0.6,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=True)
            st.plotly_chart(fig, use_container_width=True)

        # Histórico Estilizado
        st.markdown("### 🕒 Últimos Lançamentos")
        for idx, row in df.sort_values(by='Data', ascending=False).head(10).iterrows():
            cor_valor = "#38A169" if row['Tipo'] == "Entrada" else "#E53E3E"
            prefixo = "+" if row['Tipo'] == "Entrada" else "-"
            
            st.markdown(f"""
                <div class="transaction-card">
                    <div>
                        <strong style="color: #2D3748;">{row['Descrição']}</strong><br>
                        <span style="color: #A0AEC0; font-size: 12px;">{row['Categoria']} • {row['Data'].strftime('%d/%m')}</span>
                    </div>
                    <div style="color: {cor_valor}; font-weight: bold;">
                        {prefixo} R$ {row['Valor']:,.2f}
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Comece adicionando seu primeiro salário ou gasto na aba ao lado! 🚀")

with aba_novo:
    st.markdown("### 📝 O que aconteceu?")
    with st.container():
        with st.form("add_form", clear_on_submit=True):
            valor = st.number_input("Quanto? (R$)", min_value=0.0, step=1.0)
            desc = st.text_input("Com o que?", placeholder="Ex: Compras do mês")
            
            c1, c2 = st.columns(2)
            tipo = c1.selectbox("Tipo", ["Saída", "Entrada"])
            categoria = c2.selectbox("Categoria", ["🛒 Mercado", "🏠 Aluguel/Casa", "🚗 Transporte", "🍕 Lazer", "💡 Contas", "💰 Salário", "✨ Outros"])
            
            data = st.date_input("Quando?", date.today())
            
            if st.form_submit_button("Salvar no Livro"):
                if desc and valor > 0:
                    novo = pd.DataFrame([[pd.to_datetime(data), desc, valor, tipo, categoria]], 
                                       columns=['Data', 'Descrição', 'Valor', 'Tipo', 'Categoria'])
                    st.session_state.dados = pd.concat([st.session_state.dados, novo], ignore_index=True)
                    st.toast("Registrado com sucesso!", icon="✅")
                    st.rerun()
