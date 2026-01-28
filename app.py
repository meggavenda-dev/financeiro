# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import date
import plotly.express as px  # (mantido se quiser usar gráficos depois)
from supabase import create_client, Client
import os
import io
from fpdf import FPDF
import streamlit.components.v1 as components

# ================================
# CONFIGURAÇÃO DA PÁGINA (MOBILE)
# ================================
st.set_page_config(
    page_title="Minha Casa",
    page_icon="🏡",
    layout="wide",                      # Usa toda a largura no iPhone
    initial_sidebar_state="collapsed"   # Esconde a sidebar por padrão
)

# =========================================================
# INJEÇÃO DE METATAGS E ÍCONES NO <HEAD> (iOS e PWA)
# =========================================================
def inject_head_for_ios():
    """
    Injeta metatags no HEAD para iPhone/iOS:
      - viewport-fit=cover (safe-area notch/gestures)
      - app-capable + status-bar-style
      - múltiplos tamanhos de apple-touch-icon para compatibilidade antiga
      - evita auto link de telefone
    """
    components.html("""
    <script>
    (function(){
      try {
        const head = document.head;

        function add(tag, attrs){
          const el = document.createElement(tag);
          for (const [k,v] of Object.entries(attrs)) el.setAttribute(k, v);
          head.appendChild(el);
        }

        // Remove metatags viewport preexistentes e insere uma adequada ao iOS
        [...head.querySelectorAll('meta[name="viewport"]')].forEach(m => m.remove());
        add('meta', {
          name: 'viewport',
          content: 'width=device-width, initial-scale=1, viewport-fit=cover, shrink-to-fit=no'
        });

        // App-like em tela inicial (PWA light)
        add('meta', { name: 'apple-mobile-web-app-capable', content: 'yes' });
        add('meta', { name: 'apple-mobile-web-app-status-bar-style', content: 'black-translucent' });
        add('meta', { name: 'apple-mobile-web-app-title', content: 'Minha Casa' });

        // Evita auto link de telefones (iOS antigo)
        add('meta', { name: 'format-detection', content: 'telephone=no' });

        // Ícones (substitua as URLs por ícone próprio 180x180 e variações)
        const icon180 = 'https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f3e1.png';
        const icon152 = icon180;
        const icon120 = icon180;
        const icon76  = icon180;

        add('link', { rel:'apple-touch-icon', sizes:'180x180', href: icon180 });
        add('link', { rel:'apple-touch-icon', sizes:'152x152', href: icon152 });
        add('link', { rel:'apple-touch-icon', sizes:'120x120', href: icon120 });
        add('link', { rel:'apple-touch-icon', sizes:'76x76',  href: icon76  });

        // Favicon (fallback)
        add('link', { rel:'icon', type:'image/png', href: icon180 });

      } catch (e) { console.warn('Head injection failed', e); }
    })();
    </script>
    """, height=0)

inject_head_for_ios()

# =========================================================
# CSS ALTO CONTRASTE (iOS-friendly): safe-area, inputs 16px,
# botões maiores, hierarquia visual e Dark Mode opcional
# =========================================================
st.markdown("""
<style>
/* ============= CORES BASE (ALTO CONTRASTE) ============= */
:root{
  --bg:#EEF2F6;        /* Fundo levemente mais escuro que branco */
  --text:#0B1220;      /* Texto principal mais escuro */
  --muted:#334155;     /* Texto secundário mais escuro */
  --brand:#2563EB;
  --brand-600:#1D4ED8;
  --ok:#0EA5A4;
  --warn:#D97706;
  --danger:#DC2626;
  --card:#FFFFFF;
  --line:#CBD5E1;      /* borda perceptível */
  --soft-line:#E2E8F0;
}

html, body, [class*="css"] {
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
}
html, body { background: var(--bg); color: var(--text); -webkit-text-size-adjust: 100%; }
.stApp { background: var(--bg); }

/* Safe-area iOS (notch/gestos) */
@supports(padding: max(0px)) {
  .stApp, .block-container {
    padding-top: max(10px, env(safe-area-inset-top)) !important;
    padding-bottom: max(12px, env(safe-area-inset-bottom)) !important;
  }
}

/* Inputs >= 16px => evita zoom automático no iOS */
input, select, textarea,
.stTextInput input, .stNumberInput input, .stDateInput input,
.stSelectbox div[data-baseweb="select"] {
  font-size: 16px !important; color: var(--text) !important;
}

/* Widgets com fundo branco, borda visível e texto escuro */
.stTextInput input, .stNumberInput input, .stDateInput input {
  background: var(--card) !important;
  border: 1px solid var(--line) !important;
  border-radius: 12px !important;
  color: var(--text) !important;
}
.stSelectbox > div[data-baseweb="select"]{
  background: var(--card) !important;
  border: 1px solid var(--line) !important;
  border-radius: 12px !important;
  color: var(--text) !important;
}
.stSelectbox [data-baseweb="select"] div { color: var(--text) !important; }

/* Labels com contraste */
legend, label, .stRadio label, .stSelectbox label, .stDateInput label,
.stNumberInput label, .stTextInput label {
  color: var(--muted) !important; font-weight: 700 !important;
}

/* Placeholders e ícones dos inputs com mais contraste */
::placeholder { color: #475569 !important; opacity: 1 !important; }
.stDateInput input::placeholder { color: #475569 !important; }
.stSelectbox svg, .stNumberInput svg { color: #1F2937 !important; opacity: 1 !important; }

/* Evita highlight azul ao toque no iOS */
* { -webkit-tap-highlight-color: transparent; }

/* Cabeçalho */
.header-container { text-align: center; padding: 0 10px 18px 10px; }
.main-title {
  background: linear-gradient(90deg, #1E293B, var(--brand));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  font-weight: 800; font-size: 2rem; margin: 0;
}
.slogan { color: var(--muted); font-size: .95rem; font-weight: 600; }

/* Abas com contraste maior */
.stTabs [data-baseweb="tab-list"]{
  display:flex; gap:6px; width:100%;
  background:#E5EAF1; border:1px solid var(--line); border-radius:16px; padding:4px;
}
.stTabs [data-baseweb="tab"]{
  flex:1 1 auto; text-align:center; background:transparent; border-radius:12px;
  padding:12px 6px !important; color: var(--muted); font-size:14px; font-weight:800;
  border:none !important;
}
.stTabs [aria-selected="true"]{
  background: var(--card) !important; color: var(--brand) !important;
  box-shadow: 0 2px 6px rgba(0,0,0,.08);
  border:1px solid var(--line);
}

/* Métricas: força cor/opacidade dos textos */
[data-testid="stMetric"]{
  background: var(--card);
  border-radius: 14px; padding: 14px;
  border: 1px solid var(--line);
  box-shadow: 0 2px 8px rgba(0,0,0,.06);
  color: var(--text);
}
[data-testid="stMetric"] * { opacity: 1 !important; color: var(--text) !important; }
[data-testid="stMetricLabel"] { color: #0F172A !important; font-weight: 800 !important; }
[data-testid="stMetricValue"] { color: #0B1220 !important; font-weight: 900 !important; }

/* Botões */
.stButton>button{
  width:100%; min-height:48px; border-radius:14px; background: var(--brand);
  color:#fff; border:1px solid #1E40AF; padding:12px 14px; font-weight:900; letter-spacing:.2px;
  box-shadow: 0 2px 10px rgba(29,78,216,.25);
  transition: transform .12s ease, box-shadow .12s ease, background .12s ease;
}
.stButton>button:active{ transform: scale(.98); }
.stButton>button:hover{ background: var(--brand-600); }

/* Botão Excluir */
.btn-excluir > div > button{
  background: transparent !important; color: var(--danger) !important;
  border: none !important; font-size: 14px !important; font-weight: 800 !important;
  min-height: 44px !important;
}

/* Cards de transação: texto forte e borda visível */
.transaction-card{
  background: var(--card); padding: 14px; border-radius: 14px;
  margin-bottom: 8px; display:flex; justify-content:space-between; gap:12px;
  align-items:center; border:1px solid var(--line);
  box-shadow: 0 2px 8px rgba(0,0,0,.05); color: var(--text);
}
.transaction-card *{ opacity:1 !important; }
.card-icon{
  background: #E8EEF6; width: 44px; height: 44px; border-radius: 10px;
  display:flex; align-items:center; justify-content:center; font-size: 20px; color:#0F172A;
}

/* Badges de status com contraste */
.status-badge{
  font-size: 11px; padding: 3px 8px; border-radius: 10px; font-weight: 900;
  text-transform: uppercase; margin-top: 6px; display:inline-block; letter-spacing:.2px;
}
.status-badge.pago{ background:#DCFCE7; color:#065F46; border:1px solid #86EFAC; }
.status-badge.pendente{ background:#FEF3C7; color:#92400E; border:1px solid #FCD34D; }
.status-badge.negociacao{ background:#DBEAFE; color:#1E3A8A; border:1px solid #93C5FD; }

/* Vencimento visível */
.vencimento-alerta { color: #B91C1C; font-size: 12px; font-weight: 800; }

/* Card Patrimônio com contraste */
.reserva-card{
  background: linear-gradient(135deg, #0B1220 0%, #1F2937 100%);
  color: #F8FAFC; padding: 22px; border-radius: 16px; text-align: center;
  box-shadow: 0 8px 18px rgba(0,0,0,.25); border:1px solid #111827;
}

/* Expanders */
[data-testid="stExpander"] > details{
  border:1px solid var(--line); border-radius:14px; padding:6px 10px; background: var(--card);
}
[data-testid="stExpander"] summary { padding:10px; font-weight: 800; color: var(--text); }

/* Colunas no iPhone */
@media (max-width: 480px){
  [data-testid="column"]{ width:100% !important; flex:1 1 100% !important; }
  .main-title{ font-size:1.7rem; }
}

/* Remover itens padrão do Streamlit */
#MainMenu, footer, header{ visibility: hidden; }
.block-container{ padding-top: 1.0rem !important; }

/* ======== DARK MODE (opcional, segue sistema do iPhone) ======== */
@media (prefers-color-scheme: dark){
  :root{
    --bg:#0B1220; --text:#E8EDF5; --muted:#C7D2FE;
    --card:#111827; --line:#243047; --soft-line:#1F2937;
    --brand:#60A5FA; --brand-600:#3B82F6;
    --ok:#34D399; --warn:#FBBF24; --danger:#F87171;
  }
  html, body { background: var(--bg); color: var(--text); }
  .stApp, .block-container { background: var(--bg); }
  .stTabs [data-baseweb="tab-list"]{ background:#0F172A; border-color:#1F2937; }
  .stTabs [aria-selected="true"]{ border-color:#334155; }
  .transaction-card, [data-testid="stMetric"], [data-testid="stExpander"] > details{
    background: var(--card); border-color:#334155; box-shadow: 0 1px 8px rgba(0,0,0,.35);
  }
  .card-icon{ background:#1F2937; color:#E5E7EB; }
  .slogan{ color:#94A3B8; }
  ::placeholder{ color:#94A3B8 !important; }
}
</style>
""", unsafe_allow_html=True)

# ============================
# CONFIGURAÇÃO SUPABASE
# ============================
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Erro ao conectar ao banco de dados. Verifique os Secrets.")
    st.stop()

# ============================
# FUNÇÕES DE BANCO DE DADOS
# ============================
def buscar_dados():
    res = supabase.table("transacoes").select("*").execute()
    df = pd.DataFrame(res.data)
    colunas = ['id', 'data', 'descricao', 'valor', 'tipo', 'categoria', 'status']
    if df.empty:
        return pd.DataFrame(columns=colunas)
    df['data'] = pd.to_datetime(df['data'])
    if 'status' not in df.columns:
        df['status'] = 'Pago'
    return df

def buscar_metas():
    res = supabase.table("metas").select("*").execute()
    return {item['categoria']: item['limite'] for item in res.data} if res.data else {}

def buscar_fixos():
    res = supabase.table("fixos").select("*").execute()
    df = pd.DataFrame(res.data)
    if df.empty:
        return pd.DataFrame(columns=['id', 'descricao', 'valor', 'categoria'])
    return df

# ============================
# FUNÇÕES DE RELATÓRIO
# ============================
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
    for col in cols:
        pdf.cell(38, 10, col, 1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    for _, row in df.iterrows():
        pdf.cell(38, 10, row['data'].strftime('%d/%m/%y'), 1)
        pdf.cell(38, 10, str(row['descricao'])[:18], 1)
        pdf.cell(38, 10, f"R$ {row['valor']:.2f}", 1)
        pdf.cell(38, 10, row['tipo'], 1)
        pdf.cell(38, 10, row['status'], 1)
        pdf.ln()
    # Compatibilidade de retorno do FPDF
    try:
        return bytes(pdf.output())
    except:
        return pdf.output(dest="S").encode("latin-1")

# ============================
# SINCRONIZAÇÃO INICIAL
# ============================
if 'dados' not in st.session_state:
    st.session_state.dados = buscar_dados()
if 'metas' not in st.session_state:
    st.session_state.metas = buscar_metas()
if 'fixos' not in st.session_state:
    st.session_state.fixos = buscar_fixos()

CATEGORIAS = ["🛒 Mercado", "🏠 Moradia", "🚗 Transporte", "🍕 Lazer", "💡 Contas", "💰 Salário", "✨ Outros"]
meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

# ============================
# HEADER
# ============================
st.markdown("""
    <div class="header-container">
        <div class="main-title">🏡 Financeiro</div>
        <div class="slogan">Gestão inteligente para o seu lar</div>
    </div>
""", unsafe_allow_html=True)

# ============================
# FILTROS DE MÊS/ANO
# ============================
hoje = date.today()
c_m, c_a = st.columns([2, 1])
mes_nome = c_m.selectbox("Mês", meses, index=hoje.month - 1)
ano_ref = c_a.number_input("Ano", value=hoje.year, step=1)
mes_num = meses.index(mes_nome) + 1

# ============================
# PROCESSAMENTO DE DADOS
# ============================
df_geral = st.session_state.dados.copy()
colunas_padrao = ['id', 'data', 'descricao', 'valor', 'tipo', 'categoria', 'status']
df_mes = pd.DataFrame(columns=colunas_padrao)
df_atrasados_passado = pd.DataFrame(columns=colunas_padrao)
total_in = 0.0
total_out_pagas = 0.0
balanco = 0.0

if not df_geral.empty:
    total_in = df_geral[df_geral['tipo'] == 'Entrada']['valor'].sum()
    # Somente Saídas pagas entram no balanço
    total_out_pagas = df_geral[(df_geral['tipo'] == 'Saída') & (df_geral['status'] == 'Pago')]['valor'].sum()
    balanco = total_in - total_out_pagas

    df_mes = df_geral[(df_geral['data'].dt.month == mes_num) & (df_geral['data'].dt.year == ano_ref)]

    data_inicio_mes_selecionado = pd.Timestamp(date(ano_ref, mes_num, 1))
    df_atrasados_passado = df_geral[
        (df_geral['status'] == 'Pendente') &
        (df_geral['data'] < data_inicio_mes_selecionado) &
        (df_geral['tipo'] == 'Saída')
    ]

# ============================
# ABAS
# ============================
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

        st.markdown("### Histórico")
        for idx, row in df_mes.sort_values(by='data', ascending=False).iterrows():
            cor = "#10B981" if row['tipo'] == "Entrada" else "#EF4444"
            icon = row['categoria'].split()[0] if " " in row['categoria'] else "💸"
            s_text = row.get('status', 'Pago')

            # Definição de classe/cores do badge (alto contraste)
            if s_text == "Pago":
                s_class = "pago"; s_color, s_bg = "#065F46", "#DCFCE7"
            elif s_text == "Pendente":
                s_class = "pendente"; s_color, s_bg = "#92400E", "#FEF3C7"
            else:
                s_class = "negociacao"; s_color, s_bg = "#1E3A8A", "#DBEAFE"  # Em Negociação

            # Vencimento
            txt_venc = ""
            if s_text == "Pendente" and row['tipo'] == "Saída":
                dias_diff = (row['data'].date() - hoje).days
                if dias_diff < 0:
                    txt_venc = f" <span class='vencimento-alerta'>Atrasada há {-dias_diff} dias</span>"
                elif dias_diff == 0:
                    txt_venc = f" <span class='vencimento-alerta' style='color:#D97706'>Vence Hoje!</span>"

            st.markdown(f"""
                <div class="transaction-card">
                    <div style="display: flex; align-items: center;">
                        <div class="card-icon">{icon}</div>
                        <div>
                            <div style="font-weight: 700; color: #0B1220;">{row["descricao"]}</div>
                            <div style="font-size: 12px; color: #334155;">{row["data"].strftime('%d %b')}{txt_venc}</div>
                            <div class="status-badge {s_class}">{s_text}</div>
                        </div>
                    </div>
                    <div style="color: {cor}; font-weight: 800;">R$ {row["valor"]:,.2f}</div>
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
    else:
        st.info("Toque em 'Novo' para começar!")

with aba_novo:
    aba_unit, aba_fixo = st.tabs(["Lançamento Único", "🗓️ Gerenciar Fixos"])
    with aba_unit:
        with st.form("form_novo", clear_on_submit=True):
            v = st.number_input("Valor", min_value=0.0)
            d = st.text_input("Descrição")
            t = st.radio("Tipo", ["Saída", "Entrada"], horizontal=True)
            stat = st.selectbox("Status", ["Pago", "Pendente", "Em Negociação"])
            c = st.selectbox("Categoria", CATEGORIAS)
            dt = st.date_input("Data/Vencimento", date.today())
            fixo_check = st.checkbox("Salvar na lista de Fixos")
            if st.form_submit_button("Salvar"):
                if v > 0:
                    supabase.table("transacoes").insert({
                        "data": str(dt), "descricao": d, "valor": v,
                        "tipo": t, "categoria": c, "status": stat
                    }).execute()
                    if fixo_check:
                        supabase.table("fixos").insert({
                            "descricao": d, "valor": v, "categoria": c
                        }).execute()
                    st.success("Cadastrado!")
                    st.session_state.dados = buscar_dados()
                    st.session_state.fixos = buscar_fixos()
                    st.rerun()
                else:
                    st.error("O valor deve ser maior que zero.")

    with aba_fixo:
        if not st.session_state.fixos.empty:
            for idx, row in st.session_state.fixos.iterrows():
                with st.expander(f"📌 {row['descricao']} - R$ {row['valor']:,.2f}"):
                    if st.button("Lançar neste mês", key=f"launch_{row['id']}"):
                        d_f = str(date(ano_ref, mes_num, 1))
                        supabase.table("transacoes").insert({
                            "data": d_f, "descricao": row['descricao'], "valor": row['valor'],
                            "tipo": "Saída", "categoria": row['categoria'], "status": "Pago"
                        }).execute()
                        st.session_state.dados = buscar_dados()
                        st.toast("Lançado!")
                        st.rerun()
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
        else:
            st.caption("Sem fixos configurados.")

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
    st.markdown(
        f'<div class="reserva-card"><p style="margin:0;opacity:0.9;font-size:14px;">PATRIMÔNIO REAL</p><h2 style="margin:.4rem 0 0 0;">R$ {balanco:,.2f}</h2></div>',
        unsafe_allow_html=True
    )

    # Resumo de Dívidas em Negociação
    if not df_geral.empty:
        total_negoc = df_geral[df_geral['status'] == "Em Negociação"]['valor'].sum()
        if total_negoc > 0:
            st.warning(f"⚠️ Você possui **R$ {total_negoc:,.2f}** em dívidas em negociação (não afetando o patrimônio real).")

    st.markdown("### 📄 Relatórios")
    if not df_mes.empty:
        col_rel1, col_rel2 = st.columns(2)
        with col_rel1:
            st.download_button(
                label="📥 Baixar Excel",
                data=gerar_excel(df_mes),
                file_name=f"Financeiro_{mes_nome}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        with col_rel2:
            st.download_button(
                label="📥 Baixar PDF",
                data=gerar_pdf(df_mes, mes_nome),
                file_name=f"Financeiro_{mes_nome}.pdf",
                mime="application/pdf"
            )
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
                st.info(f"Faltam aprox. **{m_f} meses**.")
                st.progress(min(max(balanco/v_sonho, 0.0), 1.0))
            else:
                st.warning("Economize este mês para alimentar seu sonho!")
        except:
            st.info("Projeção indisponível no momento.")
