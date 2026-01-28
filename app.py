# --- UTILITÁRIO TEMPORÁRIO: Gerar salt/hash PBKDF2 no próprio app ---
import binascii, hashlib, secrets
with st.expander("🛠️ Utilitário temporário: Gerar salt/hash PBKDF2 (remova após uso)"):
    pwd = st.text_input("Digite a senha para gerar hash (não será salva)", type="password")
    if st.button("Gerar salt/hash"):
        if pwd:
            salt = secrets.token_bytes(16)
            dk   = hashlib.pbkdf2_hmac("sha256", pwd.encode("utf-8"), salt, 200_000)
            salt_hex = binascii.hexlify(salt).decode()
            hash_hex = binascii.hexlify(dk).decode()
            st.code(f"pwd_salt: {salt_hex}\npwd_hash: {hash_hex}", language="text")
            st.info("Copie os valores acima e faça o INSERT no Supabase. Depois remova este bloco do app.py.")
        else:
            st.warning("Digite uma senha para gerar o hash.")
