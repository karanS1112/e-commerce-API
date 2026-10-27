from pydantic_settings import BaseSettings,SettingsConfigDict

class Settings(BaseSettings):
    # here postgres sql connection setting which read from env. file 
    DB_HOST:str #here i will give default values but  i will not give any default value it read from env file bcz DB_HOST name  is same env file so it will read this. fist then get the value from that
    DB_PORT:int 
    DB_NAME:str 
    DB_USER:str 
    DB_PASSWORD:str

   # SettingsConfigDict helps to read the env file
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

# centeralise settings
settings = Settings()