from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
import uuid
from datetime import datetime
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import databases
import sqlalchemy
from sqlalchemy.ext.asyncio import create_async_engine

# --- Basic Setup ---
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# --- Database Setup ---
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

# Define the table for contact submissions
contact_submissions = sqlalchemy.Table(
    "contact_submissions",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String),
    sqlalchemy.Column("email", sqlalchemy.String),
    sqlalchemy.Column("company", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("phone", sqlalchemy.String, nullable=True),
    sqlalchemy.Column("message", sqlalchemy.String),
    sqlalchemy.Column("timestamp", sqlalchemy.DateTime),
)


# --- FastAPI App Initialization ---
app = FastAPI()
api_router = APIRouter(prefix="/api")


# --- Pydantic Models ---
class ContactForm(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None
    phone: Optional[str] = None
    message: str


# --- Core Logic ---
async def save_contact_submission(contact_data: ContactForm):
    """Saves contact form data to the database and logs an email-like message."""
    try:
        # Prepare data for insertion
        query = contact_submissions.insert().values(
            id=str(uuid.uuid4()),
            name=contact_data.name,
            email=contact_data.email,
            company=contact_data.company,
            phone=contact_data.phone,
            message=contact_data.message,
            timestamp=datetime.utcnow()
        )
        await database.execute(query)

        # The email sending logic is kept as a logging mechanism as in the original code
        body = f"""
        New contact request via website:

        Name: {contact_data.name}
        E-Mail: {contact_data.email}
        Company: {contact_data.company or 'Not specified'}
        Phone: {contact_data.phone or 'Not specified'}

        Message:
        {contact_data.message}

        ---
        Sent on: {datetime.now().strftime('%d.%m.%Y at %H:%M:%S')}
        """
        logger.info(f"Contact form submission logged: {body}")

        return {"status": "success", "message": "Message sent successfully"}

    except Exception as e:
        logger.error(f"Failed to save contact submission: {str(e)}")
        raise HTTPException(status_code=500, detail="Error sending message")


# --- API Routes ---
@api_router.get("/")
async def root():
    return {"message": "Hello World"}


@api_router.post("/contact")
async def submit_contact_form(contact_data: ContactForm):
    """Handle contact form submission"""
    try:
        result = await save_contact_submission(contact_data)
        return result
    except HTTPException as e:
        # Re-raise HTTPException to let FastAPI handle it
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in contact form: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

# Include the router in the main app
app.include_router(api_router)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Startup and Shutdown Events ---
@app.on_event("startup")
async def startup():
    # Create tables if they don't exist
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
