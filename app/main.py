from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base 
from app import models 
from app.routers import auth_router

#creation automatique des tables 
Base.metadata.create_all(bind=engine)
    
app = FastAPI(
    title="FastAPI Auth System",
    description="Système d'authentification avec tokens JWT",
    version="1.0.0"
)

#CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#inclure les routes 
app.include_router(auth_router.router)

#routes de base
@app.get("/")
async def root():
    return {
        "message": "FastAPI Authentication System",
        "version": "1.0.0",
        "endpoints": {
            "register": "/auth/register",
            "login": "/auth/login",
            "refresh": "/auth/refresh",
            "logout": "/auth/logout",
            "me": "/auth/me"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}