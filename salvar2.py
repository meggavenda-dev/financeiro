import streamlit as st
import pandas as pd
from datetime import date
import plotly.express as px
from supabase import create_client, Client
import os

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

# Injeção de Meta Tags para Android PWA e Ícone
st.markdown(f"""
    <style>
        iframe[title="st.components.v1.html"] {{ display: none; }}
        /* Badge de Status */
        .status-badge {{
            font-size: 10px; padding: 2px 8px; border-radius: 10px; font-weight: 700;
            text-transform: uppercase; margin-top: 4px; display: inline-block;
        }}
    </style>
    <link rel="shortcut icon" href="https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f3e1.png">
    <link rel="apple-touch-icon" href="https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f3e1.png">
    <link rel="icon" type="image/png" href="https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f3e1.png">
""", unsafe_allow_html=True)

# CSS PREMIUM
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #F8FAFC; }
    .header-container { text-align: center; padding-bottom: 20px; }
    .main-title { background: linear-gradient(90deg, #1E293B, #3B82F6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 700; font-size: 2.5rem; margin-bottom: 0px; }
    .slogan { color: #64748B; font-size: 1rem; font-weight: 400; }
    .stTabs [data-baseweb="tab-list"] { display: flex; justify-content: center; gap: 4px; width: 100%; background-color: #E2E8F0; border-radius: 16px; padding: 4px; }
    .stTabs [data-baseweb="tab"] { flex-grow: 1; text-align: center; background-color: transparent; border-radius: 12px; padding: 10px 2px !important; color: #64748B; font-size: 13px; font-weight: 600; border: none !important; }
    .stTabs [aria-selected="true"] { background-color: #FFFFFF !important; color: #3B82F6 !important; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }
    [data-testid="stMetric"] { background-color: #FFFFFF; border-radius: 22px; padding: 15px; box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.05); border: 1px solid #F1F5F9; }
    .stButton>button { width: 100%; border-radius: 16px; background: #3B82F6; color: white; border: none; padding: 12px; font-weight: 700; transition: all 0.2s ease; }
    .transaction-card { background-color: #FFFFFF; padding: 16px; border-radius: 20px; margin-bottom: 0px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #F1F5F9; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
    .card-icon { background: #F1F5F9; width: 40px; height: 40px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 18px; margin-right: 12px; }
    .reserva-card { background: linear-gradient(135deg, #1E293B 0%, #334155 100%); color: white; padding: 25px; border-radius: 24px; text-align: center; box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1); margin-bottom: 25px; }
    .btn-excluir > div > button { background-color: transparent !important; color: #EF4444 !important; border: none !important; font-size: 12px !important; font-weight: 400 !important; margin-top: -10px !important; text-align: right !important; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .block-container { padding-top: 2rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE BANCO DE DADOS ---
def buscar_dados():
    res = supabase.table("transacoes").select("*").execute()
    df = pd.DataFrame(res.data)
    
    # Colunas padrão para evitar KeyError se o banco estiver vazio
    colunas = ['id', 'data', 'descricao', 'valor', 'tipo', 'categoria', 'status']
    
    if df.empty:
        return pd.DataFrame(columns=colunas)
    
    df['data'] = pd.to_datetime(df['data'])
    
    # Garante que a coluna status existe no DataFrame (retrocompatibilidade)
    if 'status' not in df.columns:
        df['status'] = 'Pago'
        
    return df

def buscar_metas():
    res = supabase.table("metas").select("*").execute()
    return {item['categoria']: item['limite'] for item in res.data} if res.data else {}

def buscar_fixos():
    res = supabase.table("fixos").select("*").execute()
    return pd.DataFrame(res.data)

# Sincronização Inicial
if 'dados' not in st.session_state: st.session_state.dados = buscar_dados()
if 'metas' not in st.session_state: st.session_state.metas = buscar_metas()
if 'fixos' not in st.session_state: st.session_state.fixos = buscar_fixos()

CATEGORIAS = ["🛒 Mercado", "🏠 Moradia", "🚗 Transporte", "🍕 Lazer", "💡 Contas", "💰 Salário", "✨ Outros"]
meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

st.markdown("""<div class="header-container"><div class="main-title">🏡 Financeiro</div><div class="slogan">Gestão inteligente para o seu lar</div></div>""", unsafe_allow_html=True)

hoje = date.today()
c_m, c_a = st.columns([2, 1])
mes_nome = c_m.selectbox("Mês", meses, index=hoje.month - 1)
ano_ref = c_a.number_input("Ano", value=hoje.year, step=1)
mes_num = meses.index(mes_nome) + 1

# --- PROCESSAMENTO DE DADOS (CORREÇÃO DE NameError E INICIALIZAÇÃO) ---
df_geral = st.session_state.dados.copy()

# Inicializamos DataFrames vazios com as colunas corretas para evitar erros
colunas_trans = ['id', 'data', 'descricao', 'valor', 'tipo', 'categoria', 'status']
df_mes = pd.DataFrame(columns=colunas_trans)
df_ant = pd.DataFrame(columns=colunas_trans)
total_in = 0.0
total_out_pagas = 0.0
balanco = 0.0

if not df_geral.empty:
    # Cálculos Globais de Patrimônio (Regra: Desconta apenas o que foi Pago)
    total_in = df_geral[df_geral['tipo'] == 'Entrada']['valor'].sum()
    # Caso a coluna status ainda não exista fisicamente no banco, tratamos como Pago
    status_col = 'status' if 'status' in df_geral.columns else None
    
    if status_col:
        total_out_pagas = df_geral[(df_geral['tipo'] == 'Saída') & (df_geral['status'] == 'Pago')]['valor'].sum()
    else:
        total_out_pagas = df_geral[df_geral['tipo'] == 'Saída']['valor'].sum()
        
    balanco = total_in - total_out_pagas
    
    # Filtro do Mês Selecionado
    df_mes = df_geral[(df_geral['data'].dt.month == mes_num) & (df_geral['data'].dt.year == ano_ref)]
    
    # Mês Anterior para Gráficos
    mes_ant_num = 12 if mes_num == 1 else mes_num - 1
    ano_ant_num = ano_ref - 1 if mes_num == 1 else ano_ref
    df_ant = df_geral[(df_geral['data'].dt.month == mes_ant_num) & (df_geral['data'].dt.year == ano_ant_num)]

# --- ABAS ---
aba_resumo, aba_novo, aba_metas, aba_reserva, aba_sonhos = st.tabs(["📊 Mês", "➕ Novo", "🎯 Metas", "🏦 Caixa", "🚀 Sonhos"])

with aba_resumo:
    if not df_mes.empty:
        entradas = df_mes[df_mes['tipo'] == 'Entrada']['valor'].sum()
        
        # Lógica de Saldo Real (Apenas Saídas Pagas)
        if 'status' in df_mes.columns:
            saidas_pagas = df_mes[(df_mes['tipo'] == 'Saída') & (df_mes['status'] == 'Pago')]['valor'].sum()
            saidas_pendentes = df_mes[(df_mes['tipo'] == 'Saída') & (df_mes['status'] == 'Pendente')]['valor'].sum()
        else:
            saidas_pagas = df_mes[df_mes['tipo'] == 'Saída']['valor'].sum()
            saidas_pendentes = 0.0
            
        saldo_mes = entradas - saidas_pagas

        c1, c2, c3 = st.columns(3)
        c1.metric("Ganhos", f"R$ {entradas:,.2f}")
        c2.metric("Gastos (Pagos)", f"R$ {saidas_pagas:,.2f}")
        c3.metric("Saldo Real", f"R$ {saldo_mes:,.2f}")

        if saidas_pendentes > 0:
            st.warning(f"⚠️ R$ {saidas_pendentes:,.2f} pendentes de pagamento este mês.")

        if st.session_state.metas:
            with st.expander("🎯 Status das Metas"):
                # Metas baseadas em gastos efetivados (Pagos)
                base_gastos = df_mes[df_mes['tipo'] == 'Saída']
                if 'status' in base_gastos.columns:
                    base_gastos = base_gastos[base_gastos['status'] == 'Pago']
                
                gastos_cat = base_gastos.groupby('categoria')['valor'].sum()
                for cat, lim in st.session_state.metas.items():
                    if lim > 0:
                        atual = gastos_cat.get(cat, 0)
                        st.markdown(f'<div class="meta-container"><b>{cat}</b> (R$ {atual:,.0f} / {lim:,.0f})</div>', unsafe_allow_html=True)
                        st.progress(min(atual/lim, 1.0))

        st.markdown(f"### Histórico")
        for idx, row in df_mes.sort_values(by='data', ascending=False).iterrows():
            cor = "#10B981" if row['tipo'] == "Entrada" else "#EF4444"
            icon = row['categoria'].split()[0] if " " in row['categoria'] else "💸"
            
            # Badge de Status Visual
            s_text = row.get('status', 'Pago')
            s_color = "#10B981" if s_text == "Pago" else "#F59E0B"
            s_bg = "#D1FAE5" if s_text == "Pago" else "#FEF3C7"

            st.markdown(f"""
                <div class="transaction-card">
                    <div style="display: flex; align-items: center;">
                        <div class="card-icon">{icon}</div>
                        <div>
                            <div style="font-weight: 600; color: #1E293B;">{row["descricao"]}</div>
                            <div style="font-size: 11px; color: #64748B;">{row["data"].strftime('%d %b')}</div>
                            <div class="status-badge" style="background: {s_bg}; color: {s_color};">{s_text}</div>
                        </div>
                    </div>
                    <div style="color: {cor}; font-weight: 700;">R$ {row["valor"]:,.2f}</div>
                </div>
            """, unsafe_allow_html=True)
            
            col_pago, col_del = st.columns([1, 1])
            with col_pago:
                if s_text == "Pendente":
                    if st.button("✔ Pagar", key=f"pay_{row['id']}"):
                        supabase.table("transacoes").update({"status": "Pago"}).eq("id", row['id']).execute()
                        st.session_state.dados = buscar_dados()
                        st.rerun()
            with col_del:
                st.markdown('<div class="btn-excluir">', unsafe_allow_html=True)
                if st.button("Excluir", key=f"del_{row['id']}"):
                    supabase.table("transacoes").delete().eq("id", row['id']).execute()
                    st.session_state.dados = buscar_dados()
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
    else: st.info("Toque em 'Novo' para começar!")

with aba_novo:
    aba_unit, aba_fixo = st.tabs(["Lançamento Único", "🗓️ Fixos"])
    with aba_unit:
        with st.form("form_novo", clear_on_submit=True):
            v = st.number_input("Valor", min_value=0.0)
            d = st.text_input("Descrição")
            t = st.radio("Tipo", ["Saída", "Entrada"], horizontal=True)
            stat = st.selectbox("Status", ["Pago", "Pendente"])
            c = st.selectbox("Categoria", CATEGORIAS)
            dt = st.date_input("Data", date.today())
            if st.form_submit_button("Salvar"):
                if v > 0:
                    supabase.table("transacoes").insert({
                        "data": str(dt), 
                        "descricao": d, 
                        "valor": v, 
                        "tipo": t, 
                        "categoria": c, 
                        "status": stat
                    }).execute()
                    st.success(f"{t} cadastrada!")
                    st.session_state.dados = buscar_dados()
                    st.rerun()
                else: st.error("O valor deve ser maior que zero.")

    with aba_fixo:
        if not st.session_state.fixos.empty:
            for idx, row in st.session_state.fixos.iterrows():
                col1, col2 = st.columns([3, 1])
                col1.write(f"**{row['descricao']}** R$ {row['valor']:,.2f}")
                if col2.button("Lançar", key=f"f_{idx}"):
                    d_f = str(date(ano_ref, mes_num, 1))
                    supabase.table("transacoes").insert({
                        "data": d_f, 
                        "descricao": row['descricao'], 
                        "valor": row['valor'], 
                        "tipo": "Saída", 
                        "categoria": row['categoria'], 
                        "status": "Pago"
                    }).execute()
                    st.session_state.dados = buscar_dados()
                    st.rerun()
        else: st.caption("Sem fixos cadastrados.")

with aba_metas:
    st.info("💡 Exemplo: Defina R$ 1.000,00 para '🛒 Mercado'.")
    for cat in CATEGORIAS:
        if cat != "💰 Salário":
            atual_m = float(st.session_state.metas.get(cat, 0))
            nova_meta = st.number_input(f"Meta {cat}", min_value=0.0, value=atual_m)
            if nova_meta != atual_m:
                if st.button(f"Atualizar {cat}"):
                    supabase.table("metas").upsert({"categoria": cat, "limite": nova_meta}).execute()
                    st.session_state.metas = buscar_metas()
                    st.rerun()

with aba_reserva:
    st.markdown(f'<div class="reserva-card"><p style="margin:0;opacity:0.8;font-size:14px;">PATRIMÔNIO REAL</p><h2>R$ {balanco:,.2f}</h2></div>', unsafe_allow_html=True)
    
    if not df_geral.empty:
        df_geral['MesAno'] = df_geral['data'].dt.to_period('M').astype(str)
        mensal = df_geral.groupby(['MesAno', 'tipo'])['valor'].sum().unstack(fill_value=0)
        st.plotly_chart(px.line(mensal, title="Evolução Financeira"), use_container_width=True)

with aba_sonhos:
    st.markdown("### 🚀 Calculadora de Sonhos")
    st.info("💡 Exemplo: Uma viagem ou um carro.")
    v_sonho = st.number_input("Custo do Objetivo (R$)", min_value=0.0)
    if v_sonho > 0:
        # Tenta usar o saldo_mes calculado na aba_resumo, caso contrário 0
        try:
            entradas_sonho = df_mes[df_mes['tipo'] == 'Entrada']['valor'].sum()
            saidas_sonho = df_mes[(df_mes['tipo'] == 'Saída') & (df_mes['status'] == 'Pago')]['valor'].sum()
            sobra_m = entradas_sonho - saidas_sonho
        except:
            sobra_m = 0
            
        if sobra_m > 0:
            m_f = int(v_sonho / sobra_m) + 1
            st.info(f"Faltam aprox. **{m_f} meses** com base no saldo atual.")
            st.progress(min(max(balanco/v_sonho, 0.0), 1.0))
        else:
            st.warning("Economize este mês para alimentar seu sonho!")
