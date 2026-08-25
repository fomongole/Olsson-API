import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database.connection import init_db
from app.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    ASGI Lifespan handler: runs database table creation on startup.
    """
    print(f"🚀 Starting {settings.APP_NAME} in {settings.APP_ENV} mode...")
    await init_db()
    print("✅ Database initialized successfully.")
    yield
    print(f"🛑 Shutting down {settings.APP_NAME}...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Personal Conversational AI API for Fred Omongole (Olsson Mobile App Backend)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Global Exception Handler to capture and print any unexpected errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"\n❌ [ERROR in {request.method} {request.url.path}]: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__},
    )

# Enable CORS for mobile apps, local testing, and web dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 Router
app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "message": "Welcome to Olsson API — Personal Conversational AI Assistant",
        "docs": "/docs",
        "version": "1.0.0",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
