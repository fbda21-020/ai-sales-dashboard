import bcrypt

users = [
    ("analyst1", "password1", "analyst"),
    ("marketer1", "password2", "marketer")
]

for username, password, role in users:
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    print(f"{username},{hashed},{role}")
