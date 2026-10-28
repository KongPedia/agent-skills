from fastapi import FastAPI

app = FastAPI()
USERS = {1: {"id": 1, "name": "Ada", "password_hash": "secret", "token": "private"}}

@app.get("/users/{user_id}")
def get_user(user_id: int):
    return USERS.get(user_id)
