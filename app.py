import streamlit as st

# --- UTILITÁRIO TEMPORÁRIO: Gerar salt/hash PBKDF2 no próprio app ---
# Remova este bloco depois de fazer o INSERT no Supabase.
import binascii, hashlib, secrets

with st.expander("🛠️ Utilitário temporário: Gerar salt/hash PBKDF2 (remova após uso)"):
    pwd = st.text_input("Digite a senha para gerar hash (não será salva)", type="password")
    user = st.text_input("Digite o usuário (ex.: alynne)", value="")
    if st.button("Gerar salt/hash"):
        if pwd and user:
            salt = secrets.token_bytes(16)
            dk   = hashlib.pbkdf2_hmac("sha256", pwd.encode("utf-8"), salt, 200_000)
            salt_hex = binascii.hexlify(salt).decode()
            hash_hex = binascii.hexlify(dk).decode()
            st.success("Gerado com sucesso! Use o SQL abaixo no Supabase:")
            st.code(
f"""insert into public.app_users (username, pwd_salt, pwd_hash, is_admin)
values ('{user}', '{salt_hex}', '{hash_hex}', true)
on conflict (username) do update set
  pwd_salt = excluded.pwd_salt,
  pwd_hash = excluded.pwd_hash,
  is_admin = excluded.is_admin;""",
                language="sql"
            )
            st.info("Depois de executar o INSERT no Supabase, REMOVA este bloco do app.py por segurança.")
        else:
            st.warning("Informe usuário e senha para gerar o hash.")
