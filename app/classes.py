from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional
from datetime import datetime

AllowedRoles = Literal["admin", "gerant"]

class UserValidation(BaseModel):
    email: str = Field(description="Email adresse")
    username: str = Field(description="Pseudo")
    first_name: str = Field(description="First name")
    last_name: str = Field(description="Family name")
    password: str = Field(description="Password")
    role: AllowedRoles = Field(description="Role Of The User")
    
    @field_validator("role", mode="before")
    @classmethod
    def lower_case_role(cls, val: str) -> str:
        return val.lower()
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@gmail.com",
                "username": "thechampion",
                "first_name": "Alex",
                "last_name": "koffi",
                "password": "adminkoffi1224",
                "role": "admin"
            }
        }
    }

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenRefresh(BaseModel):
    refresh_token: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool
    role: str
    created_at: datetime
    
    model_config = {
        "from_attributes": True
    }

    