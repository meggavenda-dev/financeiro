# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client, Client
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
        // Remove viewports existentes e aplica o ideal p/ iOS
        [...head.querySelectorAll('meta[name="viewport"]')].forEach(m => m.remove());
        add('meta', { name:'viewport', content:'width=device-width, initial-scale=1, viewport-fit=cover, shrink-to-fit=no' });

        // PWA light no iOS
        add('meta', { name:'apple-mobile-web-app-capable', content:'yes' });
        add('meta', { name:'apple-mobile-web-app-status-bar-style', content:'black-translucent' });
        add('meta', { name:'apple-mobile-web-app-title', content:'Minha Casa' });

        // Evita autolink de telefone em iOS antigo
        add('meta', { name:'format-detection', content:'telephone=no' });

        // Ícones (substitua as URLs pelos seus se quiser)
        const icon180 = 'https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f3e1.png';
        ['180x180','152x152','120x120','76x76'].forEach(size => {
          add('link', { rel:'apple-touch-icon', sizes:size, href: icon180 });
        });
        add('link', { rel:'icon', type:'image/png', href: icon180 });
      } catch (e) { console.warn('Head injection failed', e); }
    })();
    </script>
    """, height=0)

inject_head_for_ios()

# =========================================================
# CSS MID-CONTRAST (claro por padrão) + Dark Mode moderado
# Corrige: pouca legibilidade no claro + overlap do ícone
# =========================================================
st.markdown("""
<style>
/* ========= PALETA MID-CONTRAST (claro por padrão) ========= */
:root{
  --bg:#F3F5F9;      /* cinza claro (não estoura como branco 100%) */
  --text:#0A1628;    /* texto principal bem escuro */
  --muted:#334155;   /* texto secundário */
  --brand:#2563EB;   /* azul */
  --brand-600:#1D4ED8;
  --ok:#0EA5A4;
  --warn:#D97706;
  --danger:#DC2626;
  --card:#FFFFFF;    /* cards brancos */
  --line:#D6DEE8;    /* borda nítida */
  --soft-line:#E6ECF3;
}

html, body, [class*="css"] {
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
}
html, body { background: var(--bg); color: var(--text); -webkit-text-size-adjust: 100%; }
.stApp { background: var(--bg); }

/* Safe-area iOS */
@supports(padding: max(0px)) {
  .stApp, .block-container {
    padding-top: max(10px, env(safe-area-inset-top)) !important;
    padding-bottom: max(12px, env(safe-area-inset-bottom)) !important;
  }
}

/* Inputs >= 16px => sem zoom no iOS, mais contraste */
input, select, textarea,
.stTextInput input, .stNumberInput input, .stDateInput input,
.stSelectbox div[data-baseweb="select"] {
  font-size: 16px !important; color: var(--text) !important;
}
.stTextInput input, .stNumberInput input, .stDateInput input {
  background: var(--card) !important;
  border: 1px solid var(--line) !important;
  border-radius: 12px !important;
}
.stSelectbox > div[data-baseweb="select"]{
  background: var(--card) !important;
  border: 1px solid var(--line) !important;
  border-radius: 12px !important;
}
::placeholder { color: #475569 !important; opacity: 1 !important; }
.stSelectbox svg, .stNumberInput svg { color: #1F2937 !important; opacity: 1 !important; }

/* Cabeçalho */
.header-container { text-align: center; padding: 0 10px 16px 10px; }
.main-title {
  background: linear-gradient(90deg, #1E293B, var(--brand));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  font-weight: 800; font-size: 1.9rem; margin: 0;
}
.slogan { color: var(--muted); font-size: .95rem; font-weight: 600; }

/* Abas (claras com contraste) */
.stTabs [data-baseweb="tab-list"]{
  display:flex; gap:6px; width:100%;
  background:#E9EEF5; border:1px solid var(--line); border-radius:16px; padding:4px;
}
.stTabs [data-baseweb="tab"]{
  flex:1 1 auto; text-align:center; background:transparent; border-radius:12px;
  padding:12px 6px !important; color: var(--muted); font-size:14px; font-weight:800;
  border:none !important;
}
.stTabs [aria-selected="true"]{
  background: var(--card) !important; color: var(--brand) !important;
  box-shadow: 0 1px 4px rgba(0,0,0,.06);
  border:1px solid var(--line);
}

/* Métricas (legíveis no claro) */
[data-testid="stMetric"]{
  background: var(--card);
  border-radius: 14px; padding: 14px;
  border: 1px solid var(--line);
  box-shadow: 0 1px 6px rgba(0,0,0,.05);
  color: var(--text);
}
[data-testid="stMetric"] * { opacity: 1 !important; color: var(--text) !important; }
[data-testid="stMetricLabel"] { color: #0F172A !important; font-weight: 800 !important; }
[data-testid="stMetricValue"] { color: #0A1628 !important; font-weight: 900 !important; }

/* Botões */
.stButton>button{
  width:100%; min-height:46px; border-radius:12px; background: var(--brand);
  color:#fff; border:1px solid #1E40AF; padding:10px 14px; font-weight:800; letter-spacing:.2px;
  box-shadow: 0 1px 8px rgba(29,78,216,.18);
  transition: transform .12s ease, box-shadow .12s ease, background .12s ease;
}
.stButton>button:active{ transform: scale(.98); }
.stButton>button:hover{ background: var(--brand-600); }

/* Botão Excluir (texto, sem “pill” azul) */
.btn-excluir > div > button{
  background: transparent !important; color: var(--danger) !important;
  border: none !important; font-size: 14px !important; font-weight: 800 !important;
  min-height: 42px !important; box-shadow:none !important;
}

/* ===== Cards de transação — correção do overlap ===== */
.transaction-card{
  background: var(--card); padding: 12px; border-radius: 14px;
  margin-bottom: 10px; display:flex; justify-content:space-between; gap:12px;
  align-items:flex-start; border:1px solid var(--line);
  box-shadow: 0 1px 6px rgba(0,0,0,.05); color: var(--text);
}
.transaction-left{
  display:flex; align-items:flex-start; gap:12px; min-width:0;
}
.card-icon{
  background: #EBF1FA; width: 42px; height: 42px; border-radius: 10px;
  display:flex; align-items:center; justify-content:center; font-size: 20px; color:#0F172A;
  flex:0 0 42px;
}
.tc-info{
  display:flex; flex-direction:column; gap:4px; min-width:0; /* evita quebra por cima */
}
.tc-title{
  font-weight: 700; color: #0A1628; line-height: 1.15; word-break: break-word;
}
.tc-meta{
  font-size: 12px; color: #334155; line-height: 1.1;
}
.status-badge{
  font-size: 11px; padding: 3px 8px; border-radius: 10px; font-weight: 900;
  text-transform: uppercase; display:inline-block; letter-spacing:.2px; width: fit-content;
}
.status-badge.pago{ background:#DCFCE7; color:#065F46; border:1px solid #86EFAC; }
.status-badge.pendente{ background:#FEF3C7; color:#92400E; border:1px solid #FCD34D; }
.status-badge.negociacao{ background:#DBEAFE; color:#1E3A8A; border:1px solid #93C5FD; }

.transaction-right{
  color:#0A1628; font-weight: 800; white-space: nowrap; margin-left:auto;
}
.transaction-right.entrada{ color:#0EA5A4; }
.transaction-right.saida{ color:#DC2626; }

/* Vencimento visível */
.vencimento-alerta { color: #B91C1C; font-size: 12px; font-weight: 800; }

/* Card Patrimônio (claro) */
.reserva-card{
  background: linear-gradient(135deg, #F8FAFF 0%, #E9EEF7 100%);
  color: #0A1628; padding: 18px; border-radius: 14px; text-align: center;
  box-shadow: 0 1px 8px rgba(0,0,0,.06); border:1px solid var(--line);
}

/* Metas */
.meta-container{
  background:#F6F9FC; border:1px solid var(--line);
  border-radius:10px; padding:10px; margin-bottom:8px;
  color:#0A1628; font-weight:600;
}

/* Expanders */
[data-testid="stExpander"] > details{
  border:1px solid var(--line); border-radius:14px; padding:6px 10px; background: var(--card);
}
[data-testid="stExpander"] summary { padding:10px; font-weight: 800; color: var(--text); }

/* Colunas no iPhone */
@media (max-width: 480px){
  [data-testid="column"]{ width:100% !important; flex:1 1 100% !important; }
  .main-title{ font-size:1.65rem; }
}

/* Remover itens padrão do Streamlit */
#MainMenu, footer, header{ visibility: hidden; }
.block-container{ padding-top: 0.9rem !important; }

/* ========= DARK MODE autom. (mais claro que o anterior) ========= */
@media (prefers-color-scheme: dark){
  :root{
    --bg:#0F172A; --text:#E7EEF8; --muted:#C8D4EE;
    --card:#141C2F; --line:#24324A; --soft-line:#1F2A3E;
    --brand:#7AA7FF; --brand-600:#5E90FF;
    --ok:#34D399; --warn:#FBBF24; --danger:#F87171;
  }
  html, body { background: var(--bg); color: var(--text); }
  .stApp, .block-container { background: var(--bg); }
  .stTabs [data-baseweb="tab-list"]{ background:#18223A; border-color:#25314A; }
  .stTabs [aria-selected="true"]{ border-color:#2E3C59; box-shadow: 0 1px 6px rgba(0,0,0,.35); }

  .transaction-card, [data-testid="stMetric"], [data-testid="stExpander"] > details{
    background: var(--card); border-color:#2A3952; box-shadow: 0 1px 10px rgba(0,0,0,.32);
  }
  .card-icon{ background:#223049; color:#E5E7EB; }
  .slogan{ color:#B8C3D9; }
  ::placeholder{ color:#A8B5CC !important; }
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
    # Normaliza tipos
    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    if 'status' not in df.columns:
        df['status'] = 'Pago'
    df['status'] = df['status'].fillna('Pago')
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
        # Garante data formatada
        df_exp['data'] = pd.to_datetime(df_exp['data'], errors='coerce').dt.strftime('%d/%m/%Y')
        df_exp.to_excel(writer, index=False, sheet_name='Lançamentos')
    return output.getvalue()

def gerar_pdf(df, nome_mes):
    """
    Gera um PDF tabular com quebra de página, repetição de cabeçalho
    e colunas dimensionadas para A4 retrato. NÃO descarta linhas.
    """
    # Se vier nulo ou vazio, gera um PDF informativo
    if df is None or df.empty:
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, f"Relatorio Financeiro - {nome_mes}", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 8, "Sem lancamentos no periodo.", ln=True)
        try:
            return bytes(pdf.output())
        except Exception:
            return pdf.output(dest="S").encode("latin-1", "replace")

    # Cópia + sanitização sem excluir linhas
    df_exp = df.copy()

    # Normaliza tipos sem dropar: data->datetime (erros viram NaT, mas mantemos a linha)
    if 'data' in df_exp.columns:
        df_exp['data'] = pd.to_datetime(df_exp['data'], errors='coerce')

    # Colunas auxiliares
    df_exp['data_fmt'] = df_exp['data'].dt.strftime('%d/%m/%Y')
    df_exp['data_fmt'] = df_exp['data_fmt'].fillna('')  # se NaT, fica vazio
    df_exp['descricao'] = df_exp['descricao'].fillna('').astype(str)
    df_exp['valor'] = pd.to_numeric(df_exp['valor'], errors='coerce').fillna(0.0)
    if 'tipo' not in df_exp.columns: df_exp['tipo'] = ''
    if 'status' not in df_exp.columns: df_exp['status'] = 'Pago'
    df_exp['tipo'] = df_exp['tipo'].fillna('').astype(str)
    df_exp['status'] = df_exp['status'].fillna('Pago').astype(str)

    # Ordena por data (NaT no fim), depois descrição
    if 'data' in df_exp.columns:
        df_exp = df_exp.sort_values(by=['data', 'descricao'], na_position='last')
    else:
        df_exp = df_exp.sort_values(by=['descricao'])

    # Configuração do PDF
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)  # margem para rodapé
    pdf.add_page()

    # Medidas
    left_margin = 10
    right_margin = 10
    page_w = 210
    usable_w = page_w - left_margin - right_margin

    # Larguras das colunas (somatório == usable_w)
    col_w = {
        "Data": 22,
        "Descricao": 92,
        "Valor": 28,
        "Tipo": 24,
        "Status": 24,
    }
    total_w = sum(col_w.values())
    if abs(total_w - usable_w) > 0.5:
        escala = usable_w / total_w
        for k in col_w:
            col_w[k] = round(col_w[k] * escala, 2)

    row_h = 8
    header_h = 9

    def draw_title():
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, f"Relatorio Financeiro - {nome_mes}", ln=True, align='C')
        pdf.ln(2)

    def draw_header():
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(230, 236, 245)
        pdf.set_draw_color(200, 210, 220)
        pdf.set_text_color(20, 30, 40)
        pdf.cell(col_w["Data"],     header_h, "Data",      border=1, ln=0, align='C', fill=True)
        pdf.cell(col_w["Descricao"], header_h, "Descricao", border=1, ln=0, align='C', fill=True)
        pdf.cell(col_w["Valor"],    header_h, "Valor",     border=1, ln=0, align='C', fill=True)
        pdf.cell(col_w["Tipo"],     header_h, "Tipo",      border=1, ln=0, align='C', fill=True)
        pdf.cell(col_w["Status"],   header_h, "Status",    border=1, ln=1, align='C', fill=True)
        pdf.set_text_color(0, 0, 0)

    def ensure_space(next_block_height):
        # Se não houver espaço para a próxima linha, cria nova página e redesenha header
        if pdf.get_y() + next_block_height + 15 > pdf.h:
            pdf.add_page()
            draw_header()

    draw_title()
    draw_header()
    pdf.set_font("Helvetica", "", 9)

    for _, row in df_exp.iterrows():
        ensure_space(row_h)

        # Data
        pdf.cell(col_w["Data"], row_h, row["data_fmt"], border=1, ln=0, align='C')

        # Descrição (trunca em 1 linha com "…", sem remover a linha)
        desc = str(row["descricao"])
        max_w = col_w["Descricao"] - 2
        while pdf.get_string_width(desc) > max_w and len(desc) > 0:
            desc = desc[:-1]
        if desc != str(row["descricao"]) and len(desc) >= 1:
            desc = desc[:-1] + "…"
        pdf.cell(col_w["Descricao"], row_h, desc, border=1, ln=0, align='L')

        # Valor (pt-BR simples)
        valor_txt = f"R$ {row['valor']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        pdf.cell(col_w["Valor"], row_h, valor_txt, border=1, ln=0, align='R')

        # Tipo
        pdf.cell(col_w["Tipo"], row_h, row["tipo"], border=1, ln=0, align='C')

        # Status
        pdf.cell(col_w["Status"], row_h, row["status"], border=1, ln=1, align='C')

    try:
        return bytes(pdf.output())
    except Exception:
        return pdf.output(dest="S").encode("latin-1", "replace")

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

    df_mes = df_geral[
        (df_geral['data'].dt.month == mes_num) &
        (df_geral['data'].dt.year == ano_ref)
    ]

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
            # Classes/cores para valor
            valor_class = "entrada" if row['tipo'] == "Entrada" else "saida"
            icon = row['categoria'].split()[0] if " " in row['categoria'] else "💸"
            s_text = row.get('status', 'Pago')

            # Classe do badge
            if s_text == "Pago":
                s_class = "pago"
            elif s_text == "Pendente":
                s_class = "pendente"
            else:
                s_class = "negociacao"

            # Vencimento
            txt_venc = ""
            if s_text == "Pendente" and row['tipo'] == "Saída":
                dias_diff = (row['data'].date() - hoje).days
                if dias_diff < 0:
                    txt_venc = f" <span class='vencimento-alerta'>Atrasada há {-dias_diff} dias</span>"
                elif dias_diff == 0:
                    txt_venc = f" <span class='vencimento-alerta' style='color:#D97706'>Vence Hoje!</span>"

            # ---- CARD DE TRANSAÇÃO (layout corrigido) ----
            st.markdown(f"""
              <div class="transaction-card">
                <div class="transaction-left">
                  <div class="card-icon">{icon}</div>
                  <div class="tc-info">
                    <div class="tc-title">{row["descricao"]}</div>
                    <div class="tc-meta">{row["data"].strftime('%d %b')}{txt_venc}</div>
                    <div class="status-badge {s_class}">{s_text}</div>
                  </div>
                </div>
                <div class="transaction-right {valor_class}">R$ {row["valor"]:,.2f}</div>
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

    # >>> Recalcula o DF para o período selecionado no momento do download
    if not st.session_state.dados.empty:
        df_para_relatorio = st.session_state.dados.copy()
        df_para_relatorio['data'] = pd.to_datetime(df_para_relatorio['data'], errors='coerce')
        mask = (
            (df_para_relatorio['data'].dt.month == mes_num) &
            (df_para_relatorio['data'].dt.year == ano_ref)
        )
        df_para_relatorio = df_para_relatorio[mask].copy()
        df_para_relatorio = df_para_relatorio.sort_values(by=['data', 'descricao'], na_position='last')

        # Debug rápido: quantas linhas irão para o arquivo?
        st.caption(f"🧾 Lançamentos no relatório: **{len(df_para_relatorio)}**")

        if not df_para_relatorio.empty:
            col_rel1, col_rel2 = st.columns(2)
            with col_rel1:
                st.download_button(
                    label="📥 Baixar Excel",
                    data=gerar_excel(df_para_relatorio),
                    file_name=f"Financeiro_{mes_nome}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            with col_rel2:
                st.download_button(
                    label="📥 Baixar PDF",
                    data=gerar_pdf(df_para_relatorio, mes_nome),
                    file_name=f"Financeiro_{mes_nome}.pdf",
                    mime="application/pdf"
                )
        else:
            st.caption("Selecione um mês com dados para gerar relatórios.")
    else:
        st.caption("Sem dados para gerar relatórios.")

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
        except Exception:
            st.info("Projeção indisponível no momento.")
