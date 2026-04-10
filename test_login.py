import asyncio
from backend.api.auth import get_password_hash, verify_password, create_access_token

h = get_password_hash("test")
print("Verified:", verify_password("test", h))
t = create_access_token({"sub": "test@example.com"})
print("Token:", t)
