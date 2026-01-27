import streamlit as st
import pandas as pd
from datetime import date
import plotly.express as px
from supabase import create_client, Client
import os
import io
from fpdf import FPDF

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

# Injeção de Meta Tags para Android PWA e Estilos Globais
st.markdown(f"""
    <style>
        iframe[title="st.components.v1.html"] {{ display: none; }}
        /* Badge de Status */
        .status-badge {{
            font-size: 10px; padding: 2px 8px; border-radius: 10px; font-weight: 700;
            text-transform: uppercase; margin-top: 4px; display: inline-block;
        }}
        /* Estilo para Vencimento */
        .vencimento-alerta {{
            color: #EF4444; font-size: 11px; font-weight: 600;
        }}
    </style>
    <link rel="shortcut icon" href="https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f3e1.png">
    <link rel="apple-touch-icon" href="https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f3e1.png">
    <link rel="icon" type="image/png" href="https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f3e1.png">
""", unsafe_allow_html=True)

# CSS PREMIUM ATUALIZADO
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #F8FAFC; }

    .header-container { text-align: center; padding-bottom: 20px; }
    .main-title { 
        background: linear-gradient(90deg, #1E293B, #3B82F6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700; font-size: 2.5rem; margin-bottom: 0px;
    }
    .slogan { color: #64748B; font-size: 1rem; font-weight: 400; }

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

    [data-testid="stMetric"] {
        background-color: #FFFFFF; border-radius: 22px; padding: 15px;
        box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.05); border: 1px solid #F1F5F9;
    }

    .stButton>button {
        width: 100%; border-radius: 16px; background: #3B82F6;
        color: white; border: none; padding: 12px; font-weight: 700;
        transition: all 0.2s ease;
    }
    .stButton>button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4); }

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

    .reserva-card {
        background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
        color: white; padding: 25px; border-radius: 24px; text-align: center;
        box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1); margin-bottom: 25px;
    }

    .meta-container {
        background-color: #F1F5F9; padding: 12px; border-radius: 12px; margin-bottom: 10px;
    }

    .btn-excluir > div > button {
        background-color: transparent !important; color: #EF4444 !important;
        border: none !important; font-size: 12px !important;
        font-weight: 400 !important; margin-top: -10px !important; text-align: right !important;
    }

    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .block-container { padding-top: 2rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE BANCO DE DADOS ---
def buscar_dados():
    res = supabase.table("transacoes").select("*").execute()
    df = pd.DataFrame(res.data)
    colunas = ['id', 'data', 'descricao', 'valor', 'tipo', 'categoria', 'status']
    if df.empty: return pd.DataFrame(columns=colunas)
    df['data'] = pd.to_datetime(df['data'])
    if 'status' not in df.columns: df['status'] = 'Pago'
    return df

def buscar_metas():
    res = supabase.table("metas").select("*").execute()
    return {item['categoria']: item['limite'] for item in res.data} if res.data else {}

def buscar_fixos():
    res = supabase.table("fixos").select("*").execute()
    df = pd.DataFrame(res.data)
    if df.empty: return pd.DataFrame(columns=['id', 'descricao', 'valor', 'categoria'])
    return df

# --- FUNÇÕES DE RELATÓRIO ---
def gerar_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_exp = df.copy()
        df_exp['data'] = df_exp['data'].dt.strftime('%d/%m/%Y')
        df_exp.to_excel(writer, index=False, sheet_name='Lançamentos')
    return output.getvalue()

def gerar_pdf(df, nome_mes):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(200, 10, f"Relatorio Financeiro - {nome_mes}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 10)
    cols = ["Data", "Descricao", "Valor", "Tipo", "Status"]
    for col in cols: pdf.cell(38, 10, col, 1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    for _, row in df.iterrows():
        pdf.cell(38, 10, row['data'].strftime('%d/%m/%y'), 1)
        pdf.cell(38, 10, str(row['descricao'])[:18], 1)
        pdf.cell(38, 10, f"R$ {row['valor']:.2f}", 1)
        pdf.cell(38, 10, row['tipo'], 1)
        pdf.cell(38, 10, row['status'], 1)
        pdf.ln()
    return bytes(pdf.output())

# Sincronização Inicial
if 'dados' not in st.session_state: st.session_state.dados = buscar_dados()
if 'metas' not in st.session_state: st.session_state.metas = buscar_metas()
if 'fixos' not in st.session_state: st.session_state.fixos = buscar_fixos()

CATEGORIAS = ["🛒 Mercado", "🏠 Moradia", "🚗 Transporte", "🍕 Lazer", "💡 Contas", "💰 Salário", "✨ Outros"]
meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

st.markdown("""
    <div class="header-container">
        <div class="main-title">🏡 Financeiro</div>
        <div class="slogan">Gestão inteligente para o seu lar</div>
    </div>
""", unsafe_allow_html=True)

hoje = date.today()
c_m, c_a = st.columns([2, 1])
mes_nome = c_m.selectbox("Mês", meses, index=hoje.month - 1)
ano_ref = c_a.number_input("Ano", value=hoje.year, step=1)
mes_num = meses.index(mes_nome) + 1

# --- PROCESSAMENTO DE DADOS ---
df_geral = st.session_state.dados.copy()
colunas_padrao = ['id', 'data', 'descricao', 'valor', 'tipo', 'categoria', 'status']
df_mes = pd.DataFrame(columns=colunas_padrao)
df_atrasados_passado = pd.DataFrame(columns=colunas_padrao)
total_in = 0.0
total_out_pagas = 0.0
balanco = 0.0

if not df_geral.empty:
    total_in = df_geral[df_geral['tipo'] == 'Entrada']['valor'].sum()
    # Lógica de Negociação: Apenas subtrai do balanço se estiver "Pago"
    total_out_pagas = df_geral[(df_geral['tipo'] == 'Saída') & (df_geral['status'] == 'Pago')]['valor'].sum()
    balanco = total_in - total_out_pagas
    
    df_mes = df_geral[(df_geral['data'].dt.month == mes_num) & (df_geral['data'].dt.year == ano_ref)]
    
    data_inicio_mes_selecionado = pd.Timestamp(date(ano_ref, mes_num, 1))
    df_atrasados_passado = df_geral[(df_geral['status'] == 'Pendente') & (df_geral['data'] < data_inicio_mes_selecionado) & (df_geral['tipo'] == 'Saída')]

# --- ABAS ---
aba_resumo, aba_novo, aba_metas, aba_reserva, aba_sonhos = st.tabs(["📊 Mês", "➕ Novo", "🎯 Metas", "🏦 Caixa", "🚀 Sonhos"])

with aba_resumo:
    # Controle de Atrasados (Passado)
    if not df_atrasados_passado.empty:
        total_atrasado = df_atrasados_passado['valor'].sum()
        with st.expander(f"⚠️ CONTAS PENDENTES DE MESES ANTERIORES: R$ {total_atrasado:,.2f}", expanded=True):
            for _, row in df_atrasados_passado.iterrows():
                col_at1, col_at2 = st.columns([3, 1])
                col_at1.write(f"**{row['descricao']}** ({row['data'].strftime('%d/%m/%y')})")
                if col_at2.button("✔ Pagar", key=f"pay_at_{row['id']}"):
                    supabase.table("transacoes").update({"status": "Pago"}).eq("id", row['id']).execute()
                    st.session_state.dados = buscar_dados(); st.rerun()

    if not df_mes.empty:
        entradas = df_mes[df_mes['tipo'] == 'Entrada']['valor'].sum()
        saidas_pagas = df_mes[(df_mes['tipo'] == 'Saída') & (df_mes['status'] == 'Pago')]['valor'].sum()
        saldo_mes = entradas - saidas_pagas

        c1, c2, c3 = st.columns(3)
        c1.metric("Ganhos", f"R$ {entradas:,.2f}")
        c2.metric("Gastos (Pagos)", f"R$ {saidas_pagas:,.2f}")
        c3.metric("Saldo Real", f"R$ {saldo_mes:,.2f}")

        if st.session_state.metas:
            with st.expander("🎯 Status das Metas"):
                gastos_cat = df_mes[(df_mes['tipo'] == 'Saída') & (df_mes['status'] == 'Pago')].groupby('categoria')['valor'].sum()
                for cat, lim in st.session_state.metas.items():
                    if lim > 0:
                        atual = gastos_cat.get(cat, 0)
                        st.markdown(f'<div class="meta-container"><b>{cat}</b> (R$ {atual:,.0f} / {lim:,.0f})</div>', unsafe_allow_html=True)
                        st.progress(min(atual/lim, 1.0))

        st.markdown(f"### Histórico")
        for idx, row in df_mes.sort_values(by='data', ascending=False).iterrows():
            cor = "#10B981" if row['tipo'] == "Entrada" else "#EF4444"
            icon = row['categoria'].split()[0] if " " in row['categoria'] else "💸"
            s_text = row.get('status', 'Pago')
            
            # Cores para o badge de status (Novo: Em Negociação)
            if s_text == "Pago": s_color, s_bg = "#10B981", "#D1FAE5"
            elif s_text == "Pendente": s_color, s_bg = "#F59E0B", "#FEF3C7"
            else: s_color, s_bg = "#3B82F6", "#DBEAFE" # Azul para Negociação
            
            # Acompanhamento por Vencimento
            txt_venc = ""
            if s_text == "Pendente" and row['tipo'] == "Saída":
                dias_diff = (row['data'].date() - hoje).days
                if dias_diff < 0:
                    txt_venc = f" <span class='vencimento-alerta'>Atrasada há {-dias_diff} dias</span>"
                elif dias_diff == 0:
                    txt_venc = f" <span class='vencimento-alerta' style='color:#F59E0B'>Vence Hoje!</span>"

            st.markdown(f"""
                <div class="transaction-card">
                    <div style="display: flex; align-items: center;">
                        <div class="card-icon">{icon}</div>
                        <div>
                            <div style="font-weight: 600; color: #1E293B;">{row["descricao"]}</div>
                            <div style="font-size: 11px; color: #64748B;">{row["data"].strftime('%d %b')}{txt_venc}</div>
                            <div class="status-badge" style="background: {s_bg}; color: {s_color};">{s_text}</div>
                        </div>
                    </div>
                    <div style="color: {cor}; font-weight: 700;">R$ {row["valor"]:,.2f}</div>
                </div>
            """, unsafe_allow_html=True)
            
            cp, cd = st.columns([1, 1])
            with cp:
                if s_text != "Pago" and st.button("✔ Pagar", key=f"pay_{row['id']}"):
                    supabase.table("transacoes").update({"status": "Pago"}).eq("id", row['id']).execute()
                    st.session_state.dados = buscar_dados(); st.rerun()
            with cd:
                st.markdown('<div class="btn-excluir">', unsafe_allow_html=True)
                if st.button("Excluir", key=f"del_{row['id']}"):
                    supabase.table("transacoes").delete().eq("id", row['id']).execute()
                    st.session_state.dados = buscar_dados(); st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
    else: st.info("Toque em 'Novo' para começar!")

with aba_novo:
    aba_unit, aba_fixo = st.tabs(["Lançamento Único", "🗓️ Gerenciar Fixos"])
    with aba_unit:
        with st.form("form_novo", clear_on_submit=True):
            v = st.number_input("Valor", min_value=0.0); d = st.text_input("Descrição")
            t = st.radio("Tipo", ["Saída", "Entrada"], horizontal=True)
            # Lógica: Adicionado o status "Em Negociação"
            stat = st.selectbox("Status", ["Pago", "Pendente", "Em Negociação"])
            c = st.selectbox("Categoria", CATEGORIAS); dt = st.date_input("Data/Vencimento", date.today())
            fixo_check = st.checkbox("Salvar na lista de Fixos")
            if st.form_submit_button("Salvar"):
                if v > 0:
                    supabase.table("transacoes").insert({"data": str(dt), "descricao": d, "valor": v, "tipo": t, "categoria": c, "status": stat}).execute()
                    if fixo_check: supabase.table("fixos").insert({"descricao": d, "valor": v, "categoria": c}).execute()
                    st.success("Cadastrado!"); st.session_state.dados = buscar_dados(); st.session_state.fixos = buscar_fixos(); st.rerun()
                else: st.error("O valor deve ser maior que zero.")

    with aba_fixo:
        if not st.session_state.fixos.empty:
            for idx, row in st.session_state.fixos.iterrows():
                with st.expander(f"📌 {row['descricao']} - R$ {row['valor']:,.2f}"):
                    if st.button("Lançar neste mês", key=f"launch_{row['id']}"):
                        d_f = str(date(ano_ref, mes_num, 1))
                        supabase.table("transacoes").insert({"data": d_f, "descricao": row['descricao'], "valor": row['valor'], "tipo": "Saída", "categoria": row['categoria'], "status": "Pago"}).execute()
                        st.session_state.dados = buscar_dados(); st.toast("Lançado!"); st.rerun()
                    st.divider()
                    new_desc = st.text_input("Editar Descrição", value=row['descricao'], key=f"ed_d_{row['id']}")
                    new_val = st.number_input("Editar Valor", value=float(row['valor']), key=f"ed_v_{row['id']}")
                    col_ed1, col_ed2 = st.columns(2)
                    if col_ed1.button("Salvar Alterações", key=f"save_fix_{row['id']}"):
                        supabase.table("fixos").update({"descricao": new_desc, "valor": new_val}).eq("id", row['id']).execute()
                        st.session_state.fixos = buscar_fixos(); st.rerun()
                    if col_ed2.button("❌ Remover Fixo", key=f"del_fix_{row['id']}"):
                        supabase.table("fixos").delete().eq("id", row['id']).execute()
                        st.session_state.fixos = buscar_fixos(); st.rerun()
        else: st.caption("Sem fixos configurados.")

with aba_metas:
    st.info("💡 Exemplo: Defina R$ 1.000,00 para '🛒 Mercado' para controlar seus gastos essenciais.")
    for cat in CATEGORIAS:
        if cat != "💰 Salário":
            atual_m = float(st.session_state.metas.get(cat, 0))
            nova_meta = st.number_input(f"Meta {cat}", min_value=0.0, value=atual_m)
            if nova_meta != atual_m and st.button(f"Atualizar {cat}"):
                supabase.table("metas").upsert({"categoria": cat, "limite": nova_meta}).execute()
                st.session_state.metas = buscar_metas(); st.rerun()

with aba_reserva:
    st.markdown(f'<div class="reserva-card"><p style="margin:0;opacity:0.8;font-size:14px;">PATRIMÔNIO REAL</p><h2>R$ {balanco:,.2f}</h2></div>', unsafe_allow_html=True)
    
    # Resumo de Dívidas em Negociação
    if not df_geral.empty:
        total_negoc = df_geral[df_geral['status'] == "Em Negociação"]['valor'].sum()
        if total_negoc > 0:
            st.warning(f"⚠️ Você possui **R$ {total_negoc:,.2f}** em dívidas em negociação (não afetando o patrimônio real).")

    st.markdown("### 📄 Relatórios")
    if not df_mes.empty:
        col_rel1, col_rel2 = st.columns(2)
        with col_rel1:
            st.download_button(label="📥 Baixar Excel", data=gerar_excel(df_mes), file_name=f"Financeiro_{mes_nome}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with col_rel2:
            st.download_button(label="📥 Baixar PDF", data=gerar_pdf(df_mes, mes_nome), file_name=f"Financeiro_{mes_nome}.pdf", mime="application/pdf")
    else:
        st.caption("Selecione um mês com dados para gerar relatórios.")

with aba_sonhos:
    st.markdown("### 🎯 Calculadora de Sonhos")
    st.info("💡 Exemplo: 'Viagem de Férias' ou 'Troca de Carro'.")
    v_sonho = st.number_input("Custo do Objetivo (R$)", min_value=0.0)
    if v_sonho > 0:
        try:
            entradas_sonho = df_mes[df_mes['tipo'] == 'Entrada']['valor'].sum()
            saidas_sonho = df_mes[(df_mes['tipo'] == 'Saída') & (df_mes['status'] == 'Pago')]['valor'].sum()
            sobra_m = entradas_sonho - saidas_sonho
            if sobra_m > 0:
                m_f = int(v_sonho / sobra_m) + 1
                st.info(f"Faltam aprox. **{m_f} meses**."); st.progress(min(max(balanco/v_sonho, 0.0), 1.0))
            else: st.warning("Economize este mês para alimentar seu sonho!")
        except: st.info("Projeção indisponível no momento.")
