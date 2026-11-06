from fastapi import FastAPI
from app.routers import (roles,permissions,role_permissions,auth,admin,user_permission,product,cart,checkout,orders)

from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi

# App is an object of fast API I have mentioned the title,description and version which shows on swagger
app = FastAPI(
    title= "E-commerce Hub API",
    description="E-commerce REST API",
    version= "1.0.0",
)
app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)

@app.get("/")
def home():
    return{
         "message": "Welcome to E-commerce Hub API",
         "status": "Success"
    }
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(product.router)     
app.include_router(cart.router)
app.include_router(checkout.router)
app.include_router(orders.router)
app.include_router(roles.router)
app.include_router(permissions.router)
# app.include_router(role_permissions.router)   
app.include_router(user_permission.router)     

# Customize the OpenAPI schema to display multiple image uploads as file inputs in Swagger.
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    schema["openapi"] = "3.0.3"

    # Fix multiple image upload for CREATE product
    create_body = schema["components"]["schemas"].get(
        "Body_create_product_products__post"
    )

    if create_body:
        create_body["properties"]["images"] = {
            "type": "array",
            "items": {
                "type": "string",
                "format": "binary"
            }
        }

    # Fix multiple image upload for UPDATE product
    update_body = schema["components"]["schemas"].get(
        "Body_update_product_products__product_id__put"
    )

    if update_body:
        update_body["properties"]["images"] = {
            "type": "array",
            "items": {
                "type": "string",
                "format": "binary"
            }
        }

    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi
