from fastapi import FastAPI
from app.routers import roles,permissions,role_permissions,auth,admin


# App is an object of fast API I have mentioned the title,description and version which shows on swagger
app = FastAPI(
    title= "E-commerce Hub API",
    description="E-commerce REST API",
    version= "1.0.0"
)

@app.get("/")
def home():
    return{
         "message": "Welcome to E-commerce Hub API",
         "status": "Success"
    }
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(roles.router)
app.include_router(permissions.router)
app.include_router(role_permissions.router)        
