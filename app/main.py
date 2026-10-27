from fastapi import FastAPI
# App is an object of fast API I have mentioned the title,description and version which shows on swagger
app = FastAPI(
    title= "E-commerce Hub API",
    description="E-commerce REST API",
    version= "1.0.0"
)

@app.get("/")
def home():
    return{
         "message": "Welcome to E-commerce Hub API"
    }
