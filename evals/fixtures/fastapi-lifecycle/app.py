from fastapi import FastAPI

class Resource:
    def __init__(self):
        self.opened = 0
        self.closed = 0
        self.active = 0

    async def acquire(self):
        self.opened += 1
        self.active += 1
        return self

    async def release(self):
        self.closed += 1
        self.active -= 1

resource = Resource()
app = FastAPI()

@app.get("/work")
async def work(fail: bool = False):
    return {"active": resource.active}
