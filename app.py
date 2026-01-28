# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client, Client
import io
import streamlit.components.v1 as components





# ============================
import os, base64, hashlib

def pbkdf2_hash(password: str, iterations: int = 260000) -> str:
    """Gera hash no formato: pbkdf2_sha256$<iter>$<salt_b64>$<hash_b64>"""
    salt = os.urandom(16)  # 128 bits
    dk   = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}$" \
           f"{base64.b64encode(salt).decode()}$" \
           f"{base64.b64encode(dk).decode()}"

def pbkdf2_verify(password: str, stored: str) -> bool:
    """Verifica a senha contra o hash guardado em stored."""
    try:
        algo, iter_s, salt_b64, hash_b64 = stored.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        iterations = int(iter_s)
        salt = base64.b64decode(salt_b64.encode())
        expected = base64.b64decode(hash_b64.encode())
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hashlib.compare_digest(dk, expected)
    except Exception:
        return False

# --- Troque para True APENAS UMA VEZ para criar/atualizar a usuária "alynne"
RUN_BOOTSTRAP = False

if RUN_BOOTSTRAP:
    try:
        senha_hash = pbkdf2_hash("862721*")
        # Usando a tabela e colunas que você tem: 'usuarios' com 'email', 'password_hash', 'nome'
        supabase.table("usuarios").upsert(
            {"email": "alynne", "password_hash": senha_hash, "nome": "Alynne"},
            on_conflict="email"   # funciona por causa do índice único
        ).execute()
        st.success("Usuária 'alynne' criada/atualizada com hash seguro.")
    except Exception as e:
        st.error(f"Falha no bootstrap de usuário: {e}")


def fetch_user_by_email(email_login: str):
    try:
        res = supabase.table("usuarios") \
            .select("user_id, email, nome, password_hash") \
            .eq("email", email_login) \
            .limit(1).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None

def login_view():
    st.markdown("### 🔐 Login")
    with st.form("login_form", clear_on_submit=False):
        u = st.text_input("Usuário (login)", value="", autocomplete="username", placeholder="alynne")
        p = st.text_input("Senha", value="", type="password", autocomplete="current-password", placeholder="••••••••")
        ok = st.form_submit_button("Entrar")

    if ok:
        user = fetch_user_by_email(u.strip())
        if user and user.get("password_hash") and pbkdf2_verify(p, user["password_hash"]):
            st.session_state["auth_user"] = {
                "id": user["user_id"],
                "username": user["email"],
                "nome": user.get("nome") or user["email"]
            }
            st.success(f"Bem-vinda, {st.session_state['auth_user']['nome']}! ✅")
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")

# Gate: se não logado, mostra login e interrompe
if "auth_user" not in st.session_state:
    login_view()
    st.stop()

# Sidebar (logout)
with st.sidebar:
    st.caption(f"Conectado como **{st.session_state['auth_user']['nome']}**")
    if st.button("Sair"):
        for k in list(st.session_state.keys()):
            if k not in ("SUPABASE_URL","SUPABASE_KEY"):
                del st.session_state[k]
        st.rerun()


#DELETAR AQUI PARA CIMA

# === NOVO: ReportLab para gerar PDF robusto (cabeçalho + paginação) ===
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm

# ================================
# CONFIGURAÇÃO DA PÁGINA (MOBILE)
# ================================
st.set_page_config(
    page_title="Minha Casa",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# INJEÇÃO DE METATAGS E ÍCONES NO <HEAD> (iOS e PWA)
# =========================================================
def inject_head_for_ios():
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
        // Viewport ideal para iOS (safe-area)
        [...head.querySelectorAll('meta[name="viewport"]')].forEach(m => m.remove());
        add('meta', { name:'viewport', content:'width=device-width, initial-scale=1, viewport-fit=cover, shrink-to-fit=no' });
        // PWA light no iOS
        add('meta', { name:'apple-mobile-web-app-capable', content:'yes' });
        add('meta', { name:'apple-mobile-web-app-status-bar-style', content:'black-translucent' });
        add('meta', { name:'apple-mobile-web-app-title', content:'Minha Casa' });
        // Evita autolink de telefone
        add('meta', { name:'format-detection', content:'telephone=no' });
        // Ícones (troque pelas suas imagens se quiser)
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
:root{
  --bg:#F3F5F9; --text:#0A1628; --muted:#334155;
  --brand:#2563EB; --brand-600:#1D4ED8;
  --ok:#0EA5A4; --warn:#D97706; --danger:#DC2626;
  --card:#FFFFFF; --line:#D6DEE8; --soft-line:#E6ECF3;
}
html, body, [class*="css"] { font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif; }
html, body { background: var(--bg); color: var(--text); -webkit-text-size-adjust: 100%; }
.stApp { background: var(--bg); }

/* Safe-area iOS */
@supports(padding: max(0px)) {
  .stApp, .block-container {
    padding-top: max(10px, env(safe-area-inset-top)) !important;
    padding-bottom: max(12px, env(safe-area-inset-bottom)) !important;
  }
}

/* Inputs >=16px (sem zoom no iOS) */
input, select, textarea,
.stTextInput input, .stNumberInput input, .stDateInput input,
.stSelectbox div[data-baseweb="select"] {
  font-size: 16px !important; color: var(--text) !important;
}
.stTextInput input, .stNumberInput input, .stDateInput input {
  background: var(--card) !important; border: 1px solid var(--line) !important; border-radius: 12px !important;
}
.stSelectbox > div[data-baseweb="select"]{ background: var(--card) !important; border: 1px solid var(--line) !important; border-radius: 12px !important; }
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

/* Abas */
.stTabs [data-baseweb="tab-list"]{
  display:flex; gap:6px; width:100%; background:#E9EEF5; border:1px solid var(--line); border-radius:16px; padding:4px;
}
.stTabs [data-baseweb="tab"]{
  flex:1 1 auto; text-align:center; background:transparent; border-radius:12px;
  padding:12px 6px !important; color: var(--muted); font-size:14px; font-weight:800; border:none !important;
}
.stTabs [aria-selected="true"]{ background: var(--card) !important; color: var(--brand) !important; box-shadow: 0 1px 4px rgba(0,0,0,.06); border:1px solid var(--line); }

/* Métricas */
[data-testid="stMetric"]{
  background: var(--card); border-radius: 14px; padding: 14px; border: 1px solid var(--line);
  box-shadow: 0 1px 6px rgba(0,0,0,.05); color: var(--text);
}
[data-testid="stMetric"] * { opacity: 1 !important; color: var(--text) !important; }
[data-testid="stMetricLabel"] { color: #0F172A !important; font-weight: 800 !important; }
[data-testid="stMetricValue"] { color: #0A1628 !important; font-weight: 900 !important; }

/* Botões */
.stButton>button{
  width:100%; min-height:46px; border-radius:12px; background: var(--brand);
  color:#fff; border:1px solid #1E40AF; padding:10px 14px; font-weight:800; letter-spacing:.2px;
  box-shadow: 0 1px 8px rgba(29,78,216,.18); transition: transform .12s ease, box-shadow .12s ease, background .12s ease;
}
.stButton>button:active{ transform: scale(.98); }
.stButton>button:hover{ background: var(--brand-600); }

/* Botão Excluir */
.btn-excluir > div > button{ background: transparent !important; color: var(--danger) !important; border: none !important; font-size: 14px !important; font-weight: 800 !important; min-height: 42px !important; box-shadow:none !important; }

/* Cards de transação (sem overlap) */
.transaction-card{
  background: var(--card); padding: 12px; border-radius: 14px; margin-bottom: 10px; display:flex; justify-content:space-between; gap:12px;
  align-items:flex-start; border:1px solid var(--line); box-shadow: 0 1px 6px rgba(0,0,0,.05); color: var(--text);
}
.transaction-left{ display:flex; align-items:flex-start; gap:12px; min-width:0; }
.card-icon{ background: #EBF1FA; width: 42px; height: 42px; border-radius: 10px; display:flex; align-items:center; justify-content:center; font-size: 20px; color:#0F172A; flex:0 0 42px; }
.tc-info{ display:flex; flex-direction:column; gap:4px; min-width:0; }
.tc-title{ font-weight: 700; color: #0A1628; line-height: 1.15; word-break: break-word; }
.tc-meta{ font-size: 12px; color: #334155; line-height: 1.1; }
.status-badge{ font-size: 11px; padding: 3px 8px; border-radius: 10px; font-weight: 900; text-transform: uppercase; display:inline-block; letter-spacing:.2px; width: fit-content; }
.status-badge.pago{ background:#DCFCE7; color:#065F46; border:1px solid #86EFAC; }
.status-badge.pendente{ background:#FEF3C7; color:#92400E; border:1px solid #FCD34D; }
.status-badge.negociacao{ background:#DBEAFE; color:#1E3A8A; border:1px solid #93C5FD; }
.transaction-right{ color:#0A1628; font-weight: 800; white-space: nowrap; margin-left:auto; }
.transaction-right.entrada{ color:#0EA5A4; }
.transaction-right.saida{ color:#DC2626; }

.vencimento-alerta { color: #B91C1C; font-size: 12px; font-weight: 800; }

/* Card Patrimônio */
.reserva-card{ background: linear-gradient(135deg, #F8FAFF 0%, #E9EEF7 100%); color: #0A1628; padding: 18px; border-radius: 14px; text-align: center; box-shadow: 0 1px 8px rgba(0,0,0,.06); border:1px solid var(--line); }

/* Metas */
.meta-container{ background:#F6F9FC; border:1px solid var(--line); border-radius:10px; padding:10px; margin-bottom:8px; color:#0A1628; font-weight:600; }

/* Expanders */
[data-testid="stExpander"] > details{ border:1px solid var(--line); border-radius:14px; padding:6px 10px; background: var(--card); }
[data-testid="stExpander"] summary { padding:10px; font-weight: 800; color: var(--text); }

/* iPhone */
@media (max-width: 480px){ [data-testid="column"]{ width:100% !important; flex:1 1 100% !important; } .main-title{ font-size:1.65rem; } }

/* Limpeza */
#MainMenu, footer, header{ visibility: hidden; }
.block-container{ padding-top: 0.9rem !important; }

/* Dark Mode moderado */
@media (prefers-color-scheme: dark){
  :root{ --bg:#0F172A; --text:#E7EEF8; --muted:#C8D4EE; --card:#141C2F; --line:#24324A; --soft-line:#1F2A3E; --brand:#7AA7FF; --brand-600:#5E90FF; --ok:#34D399; --warn:#FBBF24; --danger:#F87171; }
  html, body { background: var(--bg); color: var(--text); }
  .stApp, .block-container { background: var(--bg); }
  .stTabs [data-baseweb="tab-list"]{ background:#18223A; border-color:#25314A; }
  .stTabs [aria-selected="true"]{ border-color:#2E3C59; box-shadow: 0 1px 6px rgba(0,0,0,.35); }
  .transaction-card, [data-testid="stMetric"], [data-testid="stExpander"] > details{ background: var(--card); border-color:#2A3952; box-shadow: 0 1px 10px rgba(0,0,0,.32); }
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
        df_exp['data'] = pd.to_datetime(df_exp['data'], errors='coerce').dt.strftime('%d/%m/%Y')
        df_exp.to_excel(writer, index=False, sheet_name='Lançamentos')
    return output.getvalue()

def gerar_pdf(df, nome_mes):
    """
    Gera PDF com ReportLab (tabela com cabeçalho repetido e paginação automática).
    Nenhuma linha é descartada.
    """
    buffer = io.BytesIO()

    # Sanitiza (sem dropar linhas)
    df_exp = df.copy()
    df_exp['data'] = pd.to_datetime(df_exp['data'], errors='coerce')
    df_exp['data_fmt'] = df_exp['data'].dt.strftime('%d/%m/%Y').fillna('')
    df_exp['descricao'] = df_exp['descricao'].fillna('').astype(str)
    df_exp['valor'] = pd.to_numeric(df_exp['valor'], errors='coerce').fillna(0.0)
    df_exp['tipo'] = df_exp.get('tipo', '').fillna('').astype(str)
    df_exp['status'] = df_exp.get('status', 'Pago')
    if not isinstance(df_exp['status'], pd.Series):
        df_exp['status'] = 'Pago'
    df_exp['status'] = df_exp['status'].fillna('Pago').astype(str)

    # Ordena como no histórico
    df_exp = df_exp.sort_values(by=['data', 'descricao'], na_position='last')

    # Documento
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=12*mm, rightMargin=12*mm,
        topMargin=14*mm, bottomMargin=14*mm
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleCenter',
        parent=styles['Heading1'],
        alignment=1,  # center
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        spaceAfter=6
    )
    normal_style = styles['Normal']

    elements = []
    elements.append(Paragraph(f"Relatorio Financeiro - {nome_mes}", title_style))
    elements.append(Spacer(1, 6))

    # Tabela
    header = ["Data", "Descricao", "Valor", "Tipo", "Status"]
    data_rows = []
    for _, r in df_exp.iterrows():
        valor_txt = f"R$ {r['valor']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        data_rows.append([r['data_fmt'], r['descricao'], valor_txt, r['tipo'], r['status']])

    table_data = [header] + data_rows

    # Larguras para A4 (somam ~ 186mm -> dentro das margens)
    col_widths = [25*mm, 90*mm, 28*mm, 23*mm, 20*mm]

    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ('FONT', (0,0), (-1,0), 'Helvetica-Bold', 10),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E6ECF5")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#141A22")),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),

        ('FONT', (0,1), (-1,-1), 'Helvetica', 9),
        ('TEXTCOLOR', (0,1), (-1,-1), colors.black),

        ('ALIGN', (2,1), (2,-1), 'RIGHT'),     # Valor
        ('ALIGN', (0,1), (0,-1), 'CENTER'),    # Data
        ('ALIGN', (3,1), (4,-1), 'CENTER'),    # Tipo/Status

        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#C8D2DC")),

        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#FAFBFD")]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))

    elements.append(tbl)
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

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
    # Atrasados (passado)
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
            valor_class = "entrada" if row['tipo'] == "Entrada" else "saida"
            icon = row['categoria'].split()[0] if " " in row['categoria'] else "💸"
            s_text = row.get('status', 'Pago')

            if s_text == "Pago":
                s_class = "pago"
            elif s_text == "Pendente":
                s_class = "pendente"
            else:
                s_class = "negociacao"

            txt_venc = ""
            if s_text == "Pendente" and row['tipo'] == "Saída":
                dias_diff = (row['data'].date() - hoje).days
                if dias_diff < 0:
                    txt_venc = f" <span class='vencimento-alerta'>Atrasada há {-dias_diff} dias</span>"
                elif dias_diff == 0:
                    txt_venc = f" <span class='vencimento-alerta' style='color:#D97706'>Vence Hoje!</span>"

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

    # >>> Recalcula o DF no momento do download (evita staleness)
    if not st.session_state.dados.empty:
        df_para_relatorio = st.session_state.dados.copy()
        df_para_relatorio['data'] = pd.to_datetime(df_para_relatorio['data'], errors='coerce')
        mask = (
            (df_para_relatorio['data'].dt.month == mes_num) &
            (df_para_relatorio['data'].dt.year == ano_ref)
        )
        df_para_relatorio = df_para_relatorio[mask].copy()
        df_para_relatorio = df_para_relatorio.sort_values(by=['data', 'descricao'], na_position='last')

        # Debug: quantas linhas vão?
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
