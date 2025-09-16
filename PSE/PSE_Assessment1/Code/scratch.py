from sql_repo import repo
r = repo()
print("users columns:", sorted(r._schema.get("users", set())))
row = r.select_one("users", where={"email__eq": "<test-email>@example.com"})
print(row)
