from fastapi import FastAPI

class Resource:
    def __init__(self):
        self.opened = self.closed = self.active = 0
    async def acquire(self):
        self.opened += 1
        self.active += 1
        return self
    async def release(self):
        self.closed += 1
        self.active -= 1

class Service:
    async def lookup(self, job_id):
        if job_id == "missing":
            raise LookupError(job_id)
        if job_id == "broken":
            raise RuntimeError("backend failed")
        return {"id": job_id, "active": resource.active}

resource = Resource()
service = Service()
app = FastAPI()

@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    await resource.acquire()
    result = await service.lookup(job_id)
    await resource.release()
    return result
