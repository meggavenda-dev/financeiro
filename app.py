import streamlit as st
import pandas as pd
from datetime import date
import plotly.express as px
from supabase import create_client, Client

# --- CONFIGURAÇÃO SUPABASE ---
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Erro ao conectar ao banco de dados. Verifique os Secrets.")
    st.stop()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Minha Casa", page_icon="🏡", layout="centered")

# CSS PREMIUM: Design Mobile-First, Neumorfismo e Glassmorphism
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #F8FAFC; }

    /* Estilização do Título Principal */
    .main-title {
        font-weight: 700; color: #1E293B; font-size: 2rem;
        text-align: center; margin-bottom: 0.5rem; letter-spacing: -1px;
    }

    /* CENTRALIZAÇÃO E RESPONSIVIDADE DAS ABAS */
    .stTabs [data-baseweb="tab-list"] {
        display: flex; justify-content: center; gap: 4px; width: 100%;
        background-color: #E2E8F0; border-radius: 16px; padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        flex-grow: 1; text-align: center; background-color: transparent;
        border-radius: 12px; padding: 10px 2px !important; color: #64748B;
        font-size: 13px; font-weight: 600; border: none !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important; color: #3b82f6 !important;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    }

    /* CARDS DE MÉTRICAS */
    [data-testid="stMetric"] {
        background-color: #FFFFFF; border-radius: 24px; padding: 15px;
        box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.05); border: 1px solid #F1F5F9;
    }
    [data-testid="stMetricValue"] { font-weight: 700; color: #0F172A; }

    /* BOTÕES ESTILIZADOS */
    .stButton>button {
        width: 100%; border-radius: 16px; background: #3b82f6;
        color: white; border: none; padding: 14px; font-weight: 700;
        transition: all 0.2s ease; box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.3);
    }
    .stButton>button:hover { background: #2563eb; transform: translateY(-1px); }

    /* CARTÕES DE TRANSAÇÃO (WALLET STYLE) */
    .transaction-card {
        background-color: #FFFFFF; padding: 16px; border-radius: 20px;
        margin-bottom: 12px; display: flex; justify-content: space-between;
        align-items: center; border: 1px solid #F1F5F9;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.02);
    }
    .card-icon {
        background: #F1F5F9; width: 42px; height: 42px; border-radius: 12px;
        display: flex; align-items: center; justify-content: center; font-size: 20px;
        margin-right: 12px;
    }

    /* CARD DE RESERVA (GLASSMORPHISM) */
    .reserva-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        color: white; padding: 30px; border-radius: 28px; text-align: center;
        box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1); margin-bottom: 25px;
    }

    /* ESCONDER ELEMENTOS STREAMLIT */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .block-container { padding-top: 1.5rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE BANCO DE DADOS ---
def buscar_dados():
    res = supabase.table("transacoes").select("*").execute()
    df = pd.DataFrame(res.data)
    if not df.empty:
        df['data'] = pd.to_datetime(df['data'])
    return df

def buscar_metas():
    res = supabase.table("metas").select("*").execute()
    return {item['categoria']: item['limite'] for item in res.data} if res.data else {}

def buscar_fixos():
    res = supabase.table("fixos").select("*").execute()
    return pd.DataFrame(res.data)

# Sincronização de Estado
if 'dados' not in st.session_state: st.session_state.dados = buscar_dados()
if 'metas' not in st.session_state: st.session_state.metas = buscar_metas()
if 'fixos' not in st.session_state: st.session_state.fixos = buscar_fixos()

CATEGORIAS = ["🛒 Mercado", "🏠 Moradia", "🚗 Transporte", "🍕 Lazer", "💡 Contas", "💰 Salário", "✨ Outros"]
meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

# --- HEADER ---
st.markdown('<div class="main-title">MyFinance Casa</div>', unsafe_allow_html=True)

hoje = date.today()
c_m, c_a = st.columns([1.5, 1])
mes_nome = c_m.selectbox("", meses, index=hoje.month - 1, label_visibility="collapsed")
ano_ref = c_a.number_input("", value=hoje.year, step=1, label_visibility="collapsed")
mes_num = meses.index(mes_nome) + 1

# --- PROCESSAMENTO ---
df_geral = st.session_state.dados.copy()
if not df_geral.empty:
    df_mes = df_geral[(df_geral['data'].dt.month == mes_num) & (df_geral['data'].dt.year == ano_ref)]
    mes_ant = 12 if mes_num == 1 else mes_num - 1
    ano_ant = ano_ref - 1 if mes_num == 1 else ano_ref
    df_ant = df_geral[(df_geral['data'].dt.month == mes_ant) & (df_geral['data'].dt.year == ano_ant)]
else:
    df_mes, df_ant = pd.DataFrame(), pd.DataFrame()

# ABAS COM DESIGN DE APP
aba_resumo, aba_novo, aba_metas, aba_reserva, aba_sonhos = st.tabs(["📊 Mês", "➕ Novo", "🎯 Metas", "🏦 Caixa", "🚀 Sonhos"])

# --- ABA RESUMO ---
with aba_resumo:
    if not df_mes.empty:
        entradas = df_mes[df_mes['tipo'] == 'Entrada']['valor'].sum()
        saidas = df_mes[df_mes['tipo'] == 'Saída']['valor'].sum()
        
        c1, c2 = st.columns(2)
        c1.metric("Entradas", f"R$ {entradas:,.2f}")
        c2.metric("Saídas", f"R$ {saidas:,.2f}")

        if not df_ant.empty:
            saidas_ant = df_ant[df_ant['tipo'] == 'Saída']['valor'].sum()
            fig_comp = px.bar(x=[meses[mes_ant-1], mes_nome], y=[saidas_ant, saidas], 
                              color_discrete_sequence=["#CBD5E0", "#3b82f6"])
            fig_comp.update_layout(height=230, showlegend=False, paper_bgcolor='rgba(0,0,0,0)', 
                                  plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=30, b=0, l=0, r=0))
            st.plotly_chart(fig_comp, use_container_width=True)

        st.markdown(f"### Histórico")
        for idx, row in df_mes.sort_values(by='data', ascending=False).iterrows():
            cor = "#10b981" if row['tipo'] == "Entrada" else "#ef4444"
            icon = row['categoria'].split()[0] if " " in row['categoria'] else "💰"
            st.markdown(f"""
                <div class="transaction-card">
                    <div style="display: flex; align-items: center;">
                        <div class="card-icon">{icon}</div>
                        <div>
                            <div style="font-weight: 600; color: #1e293b;">{row['descricao']}</div>
                            <div style="font-size: 11px; color: #64748b;">{row['data'].strftime('%d %b')}</div>
                        </div>
                    </div>
                    <div style="color: {cor}; font-weight: 700; text-align: right;">
                        {' + ' if row['tipo'] == 'Entrada' else ' - '} R$ {row['valor']:,.2f}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if st.button(f"Remover {row['descricao']}", key=f"del_{row['id']}", type="secondary"):
                supabase.table("transacoes").delete().eq("id", row['id']).execute()
                st.session_state.dados = buscar_dados()
                st.rerun()
    else:
        st.info("Toque em 'Novo' para registrar movimentações.")

# --- ABA NOVO ---
with aba_novo:
    with st.form("form_novo", clear_on_submit=True):
        st.markdown("### Novo Lançamento")
        v = st.number_input("Valor", min_value=0.0, step=10.0)
        d = st.text_input("Descrição", placeholder="Ex: Compras Mensais")
        t = st.radio("Tipo", ["Saída", "Entrada"], horizontal=True)
        c = st.selectbox("Categoria", CATEGORIAS)
        dt = st.date_input("Data", date.today())
        fixo = st.checkbox("Salvar como Gasto Fixo")
        if st.form_submit_button("Confirmar Lançamento"):
            supabase.table("transacoes").insert({"data": str(dt), "descricao": d, "valor": v, "tipo": t, "categoria": c}).execute()
            if fixo: supabase.table("fixos").insert({"descricao": d, "valor": v, "categoria": c}).execute()
            st.session_state.dados = buscar_dados()
            st.rerun()

# --- ABA RESERVA E SONHOS ---
with aba_reserva:
    total_in = df_geral[df_geral['tipo'] == 'Entrada']['valor'].sum() if not df_geral.empty else 0
    total_out = df_geral[df_geral['tipo'] == 'Saída']['valor'].sum() if not df_geral.empty else 0
    balanco = total_in - total_out
    st.markdown(f"""
        <div class="reserva-card">
            <p style="margin:0; opacity:0.7; font-size: 14px; font-weight: 600;">PATRIMÔNIO ACUMULADO</p>
            <h2 style="margin:0; color:white; font-size: 32px;">R$ {balanco:,.2f}</h2>
        </div>
    """, unsafe_allow_html=True)

with aba_sonhos:
    st.markdown("### 🚀 Calculadora de Sonhos")
    v_sonho = st.number_input("Quanto custa o seu objetivo? (R$)", min_value=0.0)
    if not df_geral.empty and v_sonho > 0:
        df_geral['ma'] = df_geral['data'].dt.to_period('M').astype(str)
        mensal = df_geral.groupby(['ma', 'tipo'])['valor'].sum().unstack(fill_value=0)
        if 'Entrada' in mensal and 'Saída' in mensal:
            sobra = (mensal['Entrada'] - mensal['Saída']).mean()
            if sobra > 0:
                m_f = int(v_sonho / sobra) + 1
                st.success(f"Com uma sobra média de R$ {sobra:,.2f}, você conquista em **{m_f} meses**.")
                st.progress(min(max(balanco/v_sonho, 0.0), 1.0))
            else: st.warning("Ajuste seus gastos para aumentar sua sobra mensal.")
