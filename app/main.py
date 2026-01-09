from fastapi import FastAPI,HTTPException,Depends
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base, get_db
from app.routers import auth_router
from app.models import Users
from app.classes import UserValidation
from starlette import status
from sqlalchemy.orm import Session

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

# afficher tout les utilisateur 

@app.get("/users", status_code=status.HTTP_200_OK)
async def get_all_users(db: Session = Depends(get_db)):
    users = db.query(Users).all()
    return users

# modifier un utilisateur 

@app.put("/users/update/{email}", status_code=status.HTTP_204_NO_CONTENT)
async def update_user_by_email(email: str, user_body: UserValidation, db: Session = Depends(get_db)):
    is_changed = False
    users = db.query(Users).all()
    
    for user in users:
        if user.email == email:
            is_changed = True
            user.email = user_body.email
            user.username = user_body.username
            user.first_name = user_body.first_name
            user.last_name = user_body.last_name
            user.hashed_password = user_body.password 
            user.role = user_body.role
            db.commit()
            break
    
    if not is_changed:
        raise HTTPException(status_code=404, detail="Pas d'utilisateur trouvé")
    
    

@app.get("/health")
async def health_check():
    return {"status": "healthy"}