import streamlit as st
import pandas as pd
from datetime import date

# Configuração da página para Mobile
st.set_page_config(page_title="Finanças Familiares", layout="centered")

st.title("💰 Meu Financeiro")

# Simulação de banco de dados (Para produção, use st.connection ou Google Sheets)
if 'dados' not in st.session_state:
    st.session_state.dados = pd.DataFrame(columns=['Data', 'Descrição', 'Valor', 'Tipo'])

# --- FORMULÁRIO DE ENTRADA ---
with st.expander("➕ Adicionar Novo Lançamento"):
    with st.form("novo_registro"):
        data = st.date_input("Data", date.today())
        desc = st.text_input("Descrição (ex: Aluguel, Salário)")
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
        tipo = st.selectbox("Tipo", ["Saída", "Entrada"])
        
        enviar = st.form_submit_button("Salvar")
        
        if enviar:
            novo_item = pd.DataFrame([[data, desc, valor, tipo]], columns=['Data', 'Descrição', 'Valor', 'Tipo'])
            st.session_state.dados = pd.concat([st.session_state.dados, novo_item], ignore_index=True)
            st.success("Lançamento salvo!")

# --- RESUMO FINANCEIRO ---
st.divider()
df = st.session_state.dados

if not df.empty:
    entradas = df[df['Tipo'] == 'Entrada']['Valor'].sum()
    saidas = df[df['Tipo'] == 'Saída']['Valor'].sum()
    saldo = entradas - saidas

    col1, col2, col3 = st.columns(3)
    col1.metric("Ganhos", f"R$ {entradas:.2f}")
    col2.metric("Gastos", f"R$ {saidas:.2f}", delta_color="inverse")
    col3.metric("Saldo", f"R$ {saldo:.2f}")

    # --- TABELA DE HISTÓRICO ---
    st.subheader("📋 Histórico")
    st.dataframe(df.sort_values(by='Data', ascending=False), use_container_width=True)
else:
    st.info("Nenhum lançamento registrado ainda.")
