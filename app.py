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
    .reserva-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; padding: 20px; border-radius: 20px; text-align: center; margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE DADOS ---
DB_FILE = "dados_financeiros.csv"
META_FILE = "metas_financeiras.csv"
FIXO_FILE = "gastos_fixos.csv"

def carregar_dados(file, columns):
    if os.path.exists(file):
        try:
            df = pd.read_csv(file)
            if 'Data' in df.columns:
                df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
            return df
        except:
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

# Inicialização da Sessão
if 'dados' not in st.session_state:
    st.session_state.dados = carregar_dados(DB_FILE, ['Data', 'Descrição', 'Valor', 'Tipo', 'Categoria'])
if 'metas' not in st.session_state:
    if os.path.exists(META_FILE):
        try:
            st.session_state.metas = pd.read_csv(META_FILE, index_col='Categoria').to_dict()['Limite']
        except: st.session_state.metas = {}
    else: st.session_state.metas = {}
if 'fixos' not in st.session_state:
    st.session_state.fixos = carregar_dados(FIXO_FILE, ['Descrição', 'Valor', 'Categoria'])

CATEGORIAS = ["🛒 Mercado", "🏠 Moradia", "🚗 Transporte", "🍕 Lazer", "💡 Contas", "💰 Salário", "✨ Outros"]
meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

# --- HEADER ---
st.markdown("<h1 style='text-align: center;'>🏡 Controle Familiar</h1>", unsafe_allow_html=True)

hoje = date.today()
c_m, c_a = st.columns([2, 1])
mes_nome = c_m.selectbox("Mês", meses, index=hoje.month - 1)
ano_ref = c_a.number_input("Ano", value=hoje.year, step=1)
mes_num = meses.index(mes_nome) + 1

# --- PROCESSAMENTO DE DATAS SEGURO ---
df_geral = st.session_state.dados.copy()
# Garantir que a coluna 'Data' seja datetime antes de filtrar
if not df_geral.empty:
    df_geral['Data'] = pd.to_datetime(df_geral['Data'])
    df_mes = df_geral[(df_geral['Data'].dt.month == mes_num) & (df_geral['Data'].dt.year == ano_ref)]
else:
    df_mes = pd.DataFrame(columns=['Data', 'Descrição', 'Valor', 'Tipo', 'Categoria'])

# Cálculo Mês Anterior para Comparativo
mes_ant = 12 if mes_num == 1 else mes_num - 1
ano_ant = ano_ref - 1 if mes_num == 1 else ano_ref
if not df_geral.empty:
    df_ant = df_geral[(df_geral['Data'].dt.month == mes_ant) & (df_geral['Data'].dt.year == ano_ant)]
else:
    df_ant = pd.DataFrame()

aba_resumo, aba_novo, aba_metas, aba_reserva = st.tabs(["✨ Meu Mês", "➕ Novo", "🎯 Metas", "🏦 Reserva"])

# --- ABA RESUMO ---
with aba_resumo:
    if not df_mes.empty:
        entradas = df_mes[df_mes['Tipo'] == 'Entrada']['Valor'].sum()
        saidas = df_mes[df_mes['Tipo'] == 'Saída']['Valor'].sum()
        
        c1, c2 = st.columns(2)
        c1.metric("Ganhos", f"R$ {entradas:,.2f}")
        c2.metric("Gastos", f"R$ {saidas:,.2f}")

        # --- COMPARATIVO ---
        if not df_ant.empty:
            saidas_ant = df_ant[df_ant['Tipo'] == 'Saída']['Valor'].sum()
            fig_comp = px.bar(
                x=[meses[mes_ant-1], mes_nome], 
                y=[saidas_ant, saidas],
                title="Gastos vs Mês Anterior",
                labels={'x': '', 'y': 'Total R$'},
                color=[meses[mes_ant-1], mes_nome],
                color_discrete_sequence=["#CBD5E0", "#3182CE"]
            )
            fig_comp.update_layout(height=250, showlegend=False, margin=dict(t=30, b=0, l=0, r=0))
            st.plotly_chart(fig_comp, use_container_width=True)

        # --- METAS ---
        if st.session_state.metas:
            with st.expander("🎯 Status das Metas"):
                gastos_cat = df_mes[df_mes['Tipo'] == 'Saída'].groupby('Categoria')['Valor'].sum()
                for cat, lim in st.session_state.metas.items():
                    if lim > 0:
                        atual = gastos_cat.get(cat, 0)
                        perc = min(atual/lim, 1.0)
                        st.write(f"**{cat}** (R$ {atual:,.0f} / {lim:,.0f})")
                        st.progress(perc)

        st.markdown(f"### 🕒 Histórico")
        for idx, row in df_mes.sort_values(by='Data', ascending=False).iterrows():
            cor = "#38A169" if row['Tipo'] == "Entrada" else "#E53E3E"
            st.markdown(f'<div class="transaction-card"><div><strong>{row["Descrição"]}</strong><br><small>{row["Categoria"]}</small></div><div style="color: {cor}; font-weight: bold;">R$ {row["Valor"]:,.2f}</div></div>', unsafe_allow_html=True)
    else:
        st.info("Toque em 'Novo' para começar este mês!")

# --- ABA NOVO (INCLUINDO RECORRÊNCIA) ---
with aba_novo:
    aba_unit, aba_fixo = st.tabs(["Único", "🗓️ Gastos Fixos"])
    
    with aba_unit:
        with st.form("form_novo", clear_on_submit=True):
            v = st.number_input("Valor", min_value=0.0, step=0.01)
            d = st.text_input("Descrição")
            t = st.radio("Tipo", ["Saída", "Entrada"], horizontal=True)
            c = st.selectbox("Categoria", CATEGORIAS, key="cat_unit")
            dt = st.date_input("Data", date.today())
            fixo = st.checkbox("Salvar como Gasto Fixo (Recorrente)")
            
            if st.form_submit_button("Salvar"):
                if d and v > 0:
                    novo = pd.DataFrame([[pd.to_datetime(dt), d, v, t, c]], columns=['Data', 'Descrição', 'Valor', 'Tipo', 'Categoria'])
                    st.session_state.dados = pd.concat([st.session_state.dados, novo], ignore_index=True)
                    st.session_state.dados.to_csv(DB_FILE, index=False)
                    if fixo:
                        novo_fixo = pd.DataFrame([[d, v, c]], columns=['Descrição', 'Valor', 'Categoria'])
                        st.session_state.fixos = pd.concat([st.session_state.fixos, novo_fixo], ignore_index=True).drop_duplicates()
                        st.session_state.fixos.to_csv(FIXO_FILE, index=False)
                    st.rerun()

    with aba_fixo:
        st.markdown("### Seus Gastos Recorrentes")
        if not st.session_state.fixos.empty:
            for idx, row in st.session_state.fixos.iterrows():
                col1, col2 = st.columns([3, 1])
                col1.write(f"**{row['Descrição']}** - R$ {row['Valor']:,.2f}")
                if col2.button("Lançar", key=f"fixo_{idx}"):
                    # Lança no dia 1 do mês selecionado no topo
                    d_fixa = pd.to_datetime(date(ano_ref, mes_num, 1))
                    n = pd.DataFrame([[d_fixa, row['Descrição'], row['Valor'], "Saída", row['Categoria']]], columns=['Data', 'Descrição', 'Valor', 'Tipo', 'Categoria'])
                    st.session_state.dados = pd.concat([st.session_state.dados, n], ignore_index=True)
                    st.session_state.dados.to_csv(DB_FILE, index=False)
                    st.toast(f"{row['Descrição']} lançado!")
                    st.rerun()
            
            st.divider()
            if st.button("Limpar Lista de Fixos"):
                if os.path.exists(FIXO_FILE): os.remove(FIXO_FILE)
                st.session_state.fixos = pd.DataFrame(columns=['Descrição', 'Valor', 'Categoria'])
                st.rerun()
        else: st.caption("Marque 'Salvar como Gasto Fixo' ao lançar um gasto comum para ele aparecer aqui.")

# --- ABA METAS ---
with aba_metas:
    st.markdown("### 🎯 Definir Orçamentos")
    for cat in CATEGORIAS:
        if cat != "💰 Salário":
            st.session_state.metas[cat] = st.number_input(f"Meta {cat}", min_value=0.0, value=float(st.session_state.metas.get(cat, 0)))
    if st.button("Salvar Metas"):
        pd.DataFrame.from_dict(st.session_state.metas, orient='index', columns=['Limite']).to_csv(META_FILE)
        st.success("Metas salvas!")

# --- ABA RESERVA (ECONOMIA ACUMULADA) ---
with aba_reserva:
    if not df_geral.empty:
        total_in = df_geral[df_geral['Tipo'] == 'Entrada']['Valor'].sum()
        total_out = df_geral[df_geral['Tipo'] == 'Saída']['Valor'].sum()
        balanco = total_in - total_out
        
        st.markdown(f"""
            <div class="reserva-card">
                <p style='margin:0; opacity:0.8;'>Patrimônio Acumulado (Sobras)</p>
                <h2 style='margin:0; color:white;'>R$ {balanco:,.2f}</h2>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("### 📈 Evolução do Balanço")
        df_geral['MesAno'] = df_geral['Data'].dt.to_period('M').astype(str)
        resumo_mes = df_geral.groupby(['MesAno', 'Tipo'])['Valor'].sum().unstack(fill_value=0)
        
        if 'Entrada' in resumo_mes and 'Saída' in resumo_mes:
            resumo_mes['Sobra'] = resumo_mes['Entrada'] - resumo_mes['Saída']
            st.line_chart(resumo_mes['Sobra'])
        else:
            st.info("Dados insuficientes para gerar o gráfico de evolução.")
    else:
        st.info("Nenhum dado registrado para calcular a reserva.")

    st.divider()
    if st.button("🚨 Resetar Tudo"):
        for f in [DB_FILE, META_FILE, FIXO_FILE]:
            if os.path.exists(f): os.remove(f)
        st.session_state.clear()
        st.rerun()
