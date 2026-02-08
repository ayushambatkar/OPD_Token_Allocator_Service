import fastapi
from app import schemas, settings  # noqa: F401 to ensure models are registered
from app.routers import allocation

server = fastapi.FastAPI(version=settings.settings.version)

server.include_router(allocation.router)


@server.get("/")
async def read_root():
    return {"status": 200, "message": "OPD API is running successfully"}


@server.get("/health")
async def health_check():
    return {"status": 200, "message": "Healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(server, port=8000)
