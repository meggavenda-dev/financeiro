import streamlit as st
import pandas as pd
from datetime import date
import plotly.express as px

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

# --- INICIALIZAÇÃO DE DADOS ---
if 'dados' not in st.session_state:
    st.session_state.dados = pd.DataFrame(columns=['Data', 'Descrição', 'Valor', 'Tipo', 'Categoria'])

# --- BARRA SUPERIOR (FILTRO MENSAL) ---
st.markdown("<h1 style='text-align: center;'>🏡 Finanças da Família</h1>", unsafe_allow_html=True)

hoje = date.today()
meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

# Seletor de mês horizontal para facilitar no mobile
col_m, col_a = st.columns([2, 1])
mes_nome = col_m.selectbox("Mês", meses, index=hoje.month - 1)
ano_ref = col_a.number_input("Ano", value=hoje.year)
mes_num = meses.index(mes_nome) + 1

# Filtragem de dados
df = st.session_state.dados.copy()
df['Data'] = pd.to_datetime(df['Data'])
df_filtrado = df[(df['Data'].dt.month == mes_num) & (df['Data'].dt.year == ano_ref)]

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
        
        # Indicador de Saúde Financeira (Barra de Progresso)
        if entradas > 0:
            porcentagem = min(saidas / entradas, 1.0)
            cor_barra = "green" if porcentagem < 0.8 else "orange" if porcentagem < 0.95 else "red"
            st.write(f"**Uso da Renda: {porcentagem*100:.0f}%**")
            st.progress(porcentagem)
        
        st.markdown(f"""
            <div style="background: #3182CE; padding: 15px; border-radius: 20px; text-align: center; color: white; margin: 15px 0;">
                <p style='margin:0; font-size: 14px; opacity: 0.8;'>Saldo em {mes_nome}</p>
                <h2 style='margin:0; color: white;'>R$ {saldo:,.2f}</h2>
            </div>
        """, unsafe_allow_html=True)

        # Gráfico
        if saidas > 0:
            fig = px.pie(df_filtrado[df_filtrado['Tipo'] == 'Saída'], values='Valor', names='Categoria', 
                         hole=0.6, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("### 🕒 Histórico")
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
        st.info(f"Nenhum registro em {mes_nome}. Que tal adicionar um?")

# --- ABA NOVO ---
with aba_novo:
    st.markdown("### ✍️ Novo Lançamento")
    with st.form("add_form", clear_on_submit=True):
        valor = st.number_input("Valor (R$)", min_value=0.0, step=10.0)
        desc = st.text_input("Descrição", placeholder="Ex: Mercado Semanal")
        tipo = st.radio("Tipo", ["Saída", "Entrada"], horizontal=True)
        categoria = st.selectbox("Categoria", ["🛒 Mercado", "🏠 Moradia", "🚗 Transporte", "🍕 Lazer", "💡 Contas", "💰 Salário", "✨ Outros"])
        data_lan = st.date_input("Data", date.today())
        
        if st.form_submit_button("Salvar Registro"):
            if desc and valor > 0:
                novo = pd.DataFrame([[pd.to_datetime(data_lan), desc, valor, tipo, categoria]], 
                                   columns=['Data', 'Descrição', 'Valor', 'Tipo', 'Categoria'])
                st.session_state.dados = pd.concat([st.session_state.dados, novo], ignore_index=True)
                st.success("Feito!")
                st.rerun()

# --- ABA AJUSTES ---
with aba_ajustes:
    st.markdown("### 🔧 Gerenciar Dados")
    if not df_filtrado.empty:
        st.write("Selecione um item para remover:")
        for idx, row in df_filtrado.iterrows():
            if st.button(f"🗑️ Excluir: {row['Descrição']} (R$ {row['Valor']})", key=f"del_{idx}"):
                st.session_state.dados = st.session_state.dados.drop(idx)
                st.rerun()
    
    if st.button("🚨 Limpar TUDO (Reset)"):
        st.session_state.dados = pd.DataFrame(columns=['Data', 'Descrição', 'Valor', 'Tipo', 'Categoria'])
        st.rerun()
