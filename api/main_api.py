from fastapi import FastAPI
from api.routers import ai_router, system_router  # Import the FastAPI routers

app = FastAPI(
    title="Max Assistant API",
    description="A central hub for various AI and System functionalities.",
    version="1.0.0",
)

app.include_router(ai_router.router)
app.include_router(system_router.router)


@app.get("/")
async def root():
    return {
        "message": "Welcome to Max Assistant API! Visit /docs for API documentation."
    }
