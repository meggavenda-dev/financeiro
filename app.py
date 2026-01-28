import hashlib, secrets, binascii, getpass
username = "alynne"
password = getpass.getpass("Senha: ")  # digite 862721*
salt = secrets.token_bytes(16)
dk   = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
print("pwd_salt:", binascii.hexlify(salt).decode())
print("pwd_hash:", binascii.hexlify(dk).decode())
