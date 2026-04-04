"""FastAPI application entry point for Aqina Backend."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import api_router

# Create FastAPI app
app = FastAPI(
    title="Aqina Backend API",
    description="Backend API for Aqina 滴鸡精 E-commerce Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(api_router)


@app.get("/")
async def root():
    """Root health check endpoint."""
    return {
        "status": "healthy",
        "service": "Aqina Backend API",
        "version": "1.0.0",
        "environment": settings.environment,
    }


@app.get("/health")
async def health():
    """Health check endpoint for Cloud Run."""
    return {"status": "healthy"}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Favicon endpoint to avoid 404 logs."""
    from fastapi.responses import Response
    return Response(content=b"", media_type="image/x-icon")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
