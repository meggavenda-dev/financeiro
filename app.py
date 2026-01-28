# app.py — Utilitário temporário para gerar salt/hash (PBKDF2-SHA256)
# Use apenas para gerar o SQL do usuário admin no Supabase e depois remova.

import binascii
import hashlib
import secrets
import streamlit as st

# 1) Config de página ANTES de qualquer componente
st.set_page_config(page_title="Gerar Hash Admin", page_icon="🔑", layout="centered")

def main():
    st.title("🔐 Gerar salt/hash (PBKDF2-SHA256) para o Supabase")
    st.caption("Use TEMPORARIAMENTE. Após gerar e inserir no banco, remova este utilitário.")

    with st.expander("🛠️ Abrir utilitário"):
        user = st.text_input("Usuário (ex.: alynne)", value="")
        pwd  = st.text_input("Senha (não será salva)", type="password", value="")
        iters = st.number_input(
            "Iterações PBKDF2",
            min_value=100_000, max_value=1_000_000, value=200_000, step=50_000,
            help="200k é um bom equilíbrio entre segurança e desempenho."
        )

        if st.button("Gerar salt/hash agora", type="primary"):
            if not user or not pwd:
                st.warning("Informe usuário e senha para gerar o hash.")
            else:
                # 2) Gera salt e hash PBKDF2-SHA256
                salt = secrets.token_bytes(16)  # 16 bytes
                dk   = hashlib.pbkdf2_hmac("sha256", pwd.encode("utf-8"), salt, int(iters))
                salt_hex = binascii.hexlify(salt).decode()
                hash_hex = binascii.hexlify(dk).decode()

                st.success("Gerado com sucesso! Copie e execute o SQL no Supabase:")
                st.code(
f"""insert into public.app_users (username, pwd_salt, pwd_hash, is_admin)
values ('{user}', '{salt_hex}', '{hash_hex}', true)
on conflict (username) do update set
  pwd_salt = excluded.pwd_salt,
  pwd_hash = excluded.pwd_hash,
  is_admin = excluded.is_admin;""",
                    language="sql"
                )
                st.info("Depois de executar o INSERT no Supabase, remova este utilitário do app.")

if __name__ == "__main__":
    main()
