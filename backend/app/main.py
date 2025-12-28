from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import puzzles, runs

app = FastAPI(
    title="Spark Playground API",
    description="Backend API for the Spark Playground learning platform",
    version="1.0.0"
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(puzzles.router, prefix="/api", tags=["puzzles"])
app.include_router(runs.router, prefix="/api", tags=["runs"])

@app.get("/")
async def root():
    return {
        "message": "Spark Playground API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}
