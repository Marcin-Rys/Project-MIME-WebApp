import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

load_dotenv("../.env")

app = FastAPI()

#configuring middleware to take management of session to save logged in user
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET_KEY"))

#configuring static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

#configuring oauth client
oauth = OAuth()
oauth.register(
    name='discord',
    client_id=os.getenv("DISCORD_CLIENT_ID"),
    client_secret=os.getenv("DISCORD_CLIENT_SECRET"),
    authorize_url="https://discord.com/api/oauth2/authorize",
    access_token_url="https://discord.com/api/oauth2/token",
    user_info_endpoint="https://discord.com/api/users/@me",
    client_kwargs={'scope':'identify guilds'},
)

#ENDPOINTS
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    #Main site, shows up client data when logged in
    user = request.session.get('user')
    return  templates.TemplateResponse(
        "index.html", 
        {"request":request, "user":user} #sending client data to template
    )

@app.get("/login/discord")
async def login_via_discord(request: Request):
    #Redirects user to discord logging site
    redirect_uri = request.url_for('auth_discord_callback')
    return await oauth.discord.authorize_redirect(request, redirect_uri)

@app.get("/auth/discord/callback", name='auth_discord_callback')
async def auth_discord_calback(request: Request):
    # Endpoint to which discord sends back after logging in
    try:
        token = await oauth.discord.authorize_access_token(request)
        #downloading user data from discord
        resp = await oauth.discord.get(oauth.discord.user_info_endpoint, token=token)
        resp.raise_for_status()
        user_data=resp.json

        #saving user data in session
        request.session['user'] = user_data
    except Exception as e:
        print(f"WEBAPP | ERROR | Error while authentification with discord: {e}")
    return RedirectResponse(url='/')

@app.get("/logout")
async def logout(request: Request):
    #Logs out user, clearing session
    request.session.pop('user', None)
    return RedirectResponse(url='/')