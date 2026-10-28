from fastapi import FastAPI

app = FastAPI()
CUSTOMERS = {
    2: {"id": 2, "name": "Grace", "token": "secret2", "contact": {"city": "Seoul", "email": "private2"}},
    1: {"id": 1, "name": "Ada", "token": "secret1", "contact": {"city": "Busan", "email": "private1"}},
}

@app.get("/customers")
def list_customers(offset: int = 0, limit: int = 20):
    return {"items": list(CUSTOMERS.values())[offset:offset+limit], "total": len(CUSTOMERS)}

@app.get("/customers/{customer_id}")
def get_customer(customer_id: int):
    return CUSTOMERS.get(customer_id)
