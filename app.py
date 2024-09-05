import uvicorn

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from routers.router import router
from utils.environment import hp

app = FastAPI(
    title = "AI server template",
    version = "v1.0.0",
    description = """
        여기에 서버의 설명을 작성한다.
    """
)

@app.get("/")
async def root():
    return JSONResponse({"checkout": True, "message": "AI server."})

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("app:app", host=hp.server_host, port=hp.server_port, reload=False)

