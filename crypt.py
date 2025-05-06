import bcrypt

username = "hcoded_admin_!@!"
password = "4c@d3d_P@5$w()rd_{h3X}"

hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

print(f"PASSWORD_HASH={hashed_pw}")
plain = b"4c@d3d_P@5$w()rd_{h3X}"
hashed = b"$2b$12$mCo7WxWg5IoEsHfzU8lxie.14N5Upc2C8gTWceFGc0hByLphQYVi2"

print(bcrypt.checkpw(plain, hashed))  # should print True