from dotenv import load_dotenv
import os

load_dotenv()

class Settings:

    AMAZON_CLIENT_ID = os.getenv("AMAZON_CLIENT_ID")
    AMAZON_CLIENT_SECRET = os.getenv("AMAZON_CLIENT_SECRET")
    AMAZON_REFRESH_TOKEN = os.getenv("AMAZON_REFRESH_TOKEN")

    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

settings = Settings()