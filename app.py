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

# CSS PREMIUM (Somente Aparência + Botão de Excluir Sutil)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #F8FAFC; }

    /* Estilização do Título */
    h1 { 
        background: linear-gradient(90deg, #1E293B, #3B82F6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700; padding-bottom: 10px;
    }

    /* ABAS CENTRALIZADAS E RESPONSIVAS (App Style) */
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
        background-color: #FFFFFF !important; color: #3B82F6 !important;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    }

    /* CARDS DE MÉTRICAS */
    [data-testid="stMetric"] {
        background-color: #FFFFFF; border-radius: 22px; padding: 15px;
        box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.05); border: 1px solid #F1F5F9;
    }

    /* BOTÕES */
    .stButton>button {
        width: 100%; border-radius: 16px; background: #3B82F6;
        color: white; border: none; padding: 12px; font-weight: 700;
        transition: all 0.2s ease;
    }
    .stButton>button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4); }

    /* TRANSACTION CARDS (Wallet Style) */
    .transaction-card {
        background-color: #FFFFFF; padding: 16px; border-radius: 20px;
        margin-bottom: 0px; display: flex; justify-content: space-between;
        align-items: center; border: 1px solid #F1F5F9;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .card-icon {
        background: #F1F5F9; width: 40px; height: 40px; border-radius: 12px;
        display: flex; align-items: center; justify-content: center; font-size: 18px;
        margin-right: 12px;
    }

    /* CAIXA / RESERVA CARD */
    .reserva-card {
        background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
        color: white; padding: 25px; border-radius: 24px; text-align: center;
        box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1); margin-bottom: 25px;
    }

    /* BOTÃO EXCLUIR SUTIL */
    .btn-excluir > div > button {
        background-color: transparent !important;
        color: #EF4444 !important;
        border: none !important;
        font-size: 12px !important;
        font-weight: 400 !important;
        margin-top: -10px !important;
        text-align: right !important;
    }

    /* UI CLEANUP */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .block-container { padding-top: 2rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE BANCO DE DADOS (MANTIDAS) ---
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

# Sincronização Inicial
if 'dados' not in st.session_state:
    st.session_state.dados = buscar_dados()
if 'metas' not in st.session_state:
    st.session_state.metas = buscar_metas()
if 'fixos' not in st.session_state:
    st.session_state.fixos = buscar_fixos()

CATEGORIAS = ["🛒 Mercado", "🏠 Moradia", "🚗 Transporte", "🍕 Lazer", "💡 Contas", "💰 Salário", "✨ Outros"]
meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

# --- HEADER ---
st.markdown("<h1>🏡 Financeiro</h1>", unsafe_allow_html=True)

hoje = date.today()
c_m, c_a = st.columns([2, 1])
mes_nome = c_m.selectbox("Mês", meses, index=hoje.month - 1)
ano_ref = c_a.number_input("Ano", value=hoje.year, step=1)
mes_num = meses.index(mes_nome) + 1

# --- PROCESSAMENTO (MANTIDO) ---
df_geral = st.session_state.dados.copy()
if not df_geral.empty:
    df_mes = df_geral[(df_geral['data'].dt.month == mes_num) & (df_geral['data'].dt.year == ano_ref)]
    mes_ant = 12 if mes_num == 1 else mes_num - 1
    ano_ant = ano_ref - 1 if mes_num == 1 else ano_ref
    df_ant = df_geral[(df_geral['data'].dt.month == mes_ant) & (df_geral['data'].dt.year == ano_ant)]
else:
    df_mes = pd.DataFrame()
    df_ant = pd.DataFrame()

# ABAS CENTRALIZADAS
aba_resumo, aba_novo, aba_metas, aba_reserva, aba_sonhos = st.tabs(["📊 Mês", "➕ Novo", "🎯 Metas", "🏦 Caixa", "🚀 Sonhos"])

# --- ABA RESUMO ---
with aba_resumo:
    if not df_mes.empty:
        entradas = df_mes[df_mes['tipo'] == 'Entrada']['valor'].sum()
        saidas = df_mes[df_mes['tipo'] == 'Saída']['valor'].sum()
        
        c1, c2 = st.columns(2)
        c1.metric("Ganhos", f"R$ {entradas:,.2f}")
        c2.metric("Gastos", f"R$ {saidas:,.2f}")

        if not df_ant.empty:
            saidas_ant = df_ant[df_ant['tipo'] == 'Saída']['valor'].sum()
            fig_comp = px.bar(x=[meses[mes_ant-1], mes_nome], y=[saidas_ant, saidas], 
                              color_discrete_sequence=["#CBD5E0", "#3B82F6"])
            fig_comp.update_layout(height=230, showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, b=0, l=0, r=0))
            st.plotly_chart(fig_comp, use_container_width=True)

        if st.session_state.metas:
            with st.expander("🎯 Status das Metas"):
                gastos_cat = df_mes[df_mes['tipo'] == 'Saída'].groupby('categoria')['valor'].sum()
                for cat, lim in st.session_state.metas.items():
                    if lim > 0:
                        atual = gastos_cat.get(cat, 0)
                        st.write(f"**{cat}** (R$ {atual:,.0f} / {lim:,.0f})")
                        st.progress(min(atual/lim, 1.0))

        st.markdown(f"### Histórico")
        for idx, row in df_mes.sort_values(by='data', ascending=False).iterrows():
            cor = "#10B981" if row['tipo'] == "Entrada" else "#EF4444"
            icon = row['categoria'].split()[0] if " " in row['categoria'] else "💸"
            
            # Card da transação
            st.markdown(f"""
                <div class="transaction-card">
                    <div style="display: flex; align-items: center;">
                        <div class="card-icon">{icon}</div>
                        <div>
                            <div style="font-weight: 600; color: #1E293B;">{row["descricao"]}</div>
                            <div style="font-size: 11px; color: #64748B;">{row["data"].strftime('%d %b')}</div>
                        </div>
                    </div>
                    <div style="color: {cor}; font-weight: 700;">R$ {row["valor"]:,.2f}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Botão de excluir sutil alinhado à direita
            col_v, col_del = st.columns([4, 1])
            with col_del:
                st.markdown('<div class="btn-excluir">', unsafe_allow_html=True)
                if st.button("Excluir", key=f"del_{row['id']}"):
                    supabase.table("transacoes").delete().eq("id", row['id']).execute()
                    st.session_state.dados = buscar_dados()
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.info("Toque em 'Novo' para começar!")

# --- ABA NOVO ---
with aba_novo:
    aba_unit, aba_fixo = st.tabs(["Lançamento Único", "🗓️ Fixos"])
    with aba_unit:
        with st.form("form_novo", clear_on_submit=True):
            v = st.number_input("Valor", min_value=0.0)
            d = st.text_input("Descrição")
            t = st.radio("Tipo", ["Saída", "Entrada"], horizontal=True)
            c = st.selectbox("Categoria", CATEGORIAS)
            dt = st.date_input("Data", date.today())
            fixo_check = st.checkbox("Salvar como Fixo")
            if st.form_submit_button("Salvar"):
                supabase.table("transacoes").insert({"data": str(dt), "descricao": d, "valor": v, "tipo": t, "categoria": c}).execute()
                if fixo_check:
                    supabase.table("fixos").insert({"descricao": d, "valor": v, "categoria": c}).execute()
                st.session_state.dados = buscar_dados()
                st.session_state.fixos = buscar_fixos()
                st.rerun()

    with aba_fixo:
        if not st.session_state.fixos.empty:
            for idx, row in st.session_state.fixos.iterrows():
                col1, col2 = st.columns([3, 1])
                col1.write(f"**{row['descricao']}** R$ {row['valor']:,.2f}")
                if col2.button("OK", key=f"f_{idx}"):
                    d_f = str(date(ano_ref, mes_num, 1))
                    supabase.table("transacoes").insert({"data": d_f, "descricao": row['descricao'], "valor": row['valor'], "tipo": "Saída", "categoria": row['categoria']}).execute()
                    st.session_state.dados = buscar_dados()
                    st.toast("Lançado!")
                    st.rerun()
        else: st.caption("Sem fixos cadastrados.")

# --- ABA METAS ---
with aba_metas:
    for cat in CATEGORIAS:
        if cat != "💰 Salário":
            atual_m = float(st.session_state.metas.get(cat, 0))
            nova_meta = st.number_input(f"Meta {cat}", min_value=0.0, value=atual_m)
            if nova_meta != atual_m:
                if st.button(f"Atualizar {cat}"):
                    supabase.table("metas").upsert({"categoria": cat, "limite": nova_meta}).execute()
                    st.session_state.metas = buscar_metas()
                    st.rerun()

# --- ABA RESERVA ---
with aba_reserva:
    total_in = df_geral[df_geral['tipo'] == 'Entrada']['valor'].sum() if not df_geral.empty else 0
    total_out = df_geral[df_geral['tipo'] == 'Saída']['valor'].sum() if not df_geral.empty else 0
    balanco = total_in - total_out
    st.markdown(f'<div class="reserva-card"><p style="margin:0;opacity:0.8;font-size:14px;">PATRIMÔNIO ACUMULADO</p><h2>R$ {balanco:,.2f}</h2></div>', unsafe_allow_html=True)
    
    if not df_geral.empty:
        df_geral['MesAno'] = df_geral['data'].dt.to_period('M').astype(str)
        mensal = df_geral.groupby(['MesAno', 'tipo'])['valor'].sum().unstack(fill_value=0)
        if 'Entrada' in mensal and 'Saída' in mensal:
            fig_res = px.line(mensal, y=mensal['Entrada'] - mensal['Saída'], title="Saúde Financeira Mensal", markers=True)
            fig_res.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_res, use_container_width=True)

# --- ABA SONHOS ---
with aba_sonhos:
    st.markdown("### 🎯 Calculadora de Sonhos")
    v_sonho = st.number_input("Custo do Objetivo (R$)", min_value=0.0)
    if not df_geral.empty and v_sonho > 0:
        df_geral['MesAno'] = df_geral['data'].dt.to_period('M').astype(str)
        bal_m = df_geral.groupby(['MesAno', 'tipo'])['valor'].sum().unstack(fill_value=0)
        if 'Entrada' in bal_m and 'Saída' in bal_m:
            sobra_m = (bal_m['Entrada'] - bal_m['Saída']).mean()
            if sobra_m > 0:
                m_f = int(v_sonho / sobra_m) + 1
                st.info(f"Com uma sobra média de R$ {sobra_m:,.2f}, faltam aprox. **{m_f} meses**.")
                st.progress(min(max(balanco/v_sonho, 0.0), 1.0))
            else: st.warning("Sua sobra média está negativa.")
