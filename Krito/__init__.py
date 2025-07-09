import os, logging, re, time
from pyrogram import Client
from .txt import Txt

id_pattern = re.compile(r'^.\d+$')

logging.basicConfig(level=logging.INFO, filename='error.log')
LOGS = logging.getLogger("Bot by @YUITOAKASH")
LOGS.setLevel(level=logging.INFO)

# -------------------------------USER----------------------------------------
SESSION_STRING = os.environ.get("SESSION_STRING", "None")

# -------------------------------VARS-----------------------------------------
API_ID = int(os.environ.get("API_ID", 14712540))
API_HASH = os.environ.get("API_HASH", "e61b996dc037d969a4f8cf6411bb6165")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "6202042878:AAHNkvyD6YbZtQu_-O95mFXHFI96P0FEK2E")
BOT_NAME = os.environ.get("BOT_NAME", "ya_typobot")
BOT_UPTIME = time.time()
USER_CHAT = int(os.environ.get("USER_CHAT", -1001799776296))

# -------------------------------PERMISSIONS---------------------------------
ADMIN = [int(admin) if id_pattern.search(admin) else admin for admin in os.environ.get('ADMIN', '2009088107').split()]
FORCE_SUB = [int(force_sub) if id_pattern.search(force_sub) else force_sub for force_sub in os.environ.get("FORCE_SUB", '-1001582946609 -1001432409719 -1001919989943').split()]

# -------------------------------DATABASE------------------------------------
DB_NAME = os.environ.get("DB_NAME", "Refun")
DB_URL = os.environ.get("DB_URL", "mongodb+srv://RENAME2:RENAME2@cluster0.grqnvbb.mongodb.net/?retryWrites=true&w=majority")

# -------------------------------OPERATIONAL CONFIGURATION------------------
SP_USERS = [int(sp_users) if id_pattern.search(sp_users) else sp_users for sp_users in os.environ.get('SP_USERS', '2009088107').split()]
MAX_SPACE = int(os.environ.get("MAX_SPACE", 104857600))
TOKEN_TIMEOUT = os.environ.get("TOKEN_TIMEOUT", "None")
MAX_PAGE = int(os.environ.get("MAX_PAGE", 4))

# -------------------------------URLS AND SHORTENER------------------------
TUTORIAL_URL = os.environ.get("TUTORIAL_URL", "")
SHORT_URL = os.environ.get("SHORT_URL", "")
SHORTEN_KEY = os.environ.get("SHORTEN_KEY", "atglinks.com ea08e13411f489f3e84f9bdac81c7e2024f01a82")

# -------------------------------LOGGING AND WEBHOOK----------------------
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", -1001682783965))
WEBHOOK = bool(os.environ.get("WEBHOOK", True))

#--------------------------------Text1-------------------------
Text = Txt.TEXT
Text1 = Txt.TEXT_MESSAGE1
Text2 = Txt.TEXT_MESSAGE2
Text3 = Txt.TEXT_MESSAGE3

# -------------------------------DEFAULT---------------------------------------
plugins = dict(root="plugins")

# -------------------------------CLIENT SETUP-------------------------
pbot = Client(
    "Renamer",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH,
    plugins=plugins,
    max_concurrent_transmissions=200,
    workers=50
)

ubot = None
if SESSION_STRING != "None":
    ubot = Client(
        "Chizuru",
        session_string=SESSION_STRING,
        api_id=API_ID,
        api_hash=API_HASH,
        plugins=plugins,
        max_concurrent_transmissions=10,
        workers=50
    )
