import os
from pathlib import Path
from dotenv import load_dotenv

# chargement du fichier d environnement parent
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# identifiants de l api rodiumai pour le llm
RODIUMAI_API_KEY = os.getenv("RODIUMAI_API_KEY")
BASE_URL = os.getenv("BASE_URL", "https://api.rodiumai.io/v1")
MODELE_GEMINI = "google/gemini-3.8-flash"

# identifiants de green api pour whatsapp
GREEN_API_URL = os.getenv("GREEN_API_URL", "https://api.green-api.com")
GREEN_API_ID_INSTANCE = os.getenv("GREEN_API_ID_INSTANCE", "1101820000")
GREEN_API_TOKEN_INSTANCE = os.getenv("GREEN_API_TOKEN_INSTANCE", "mock_token_green_api")

# jeton d autorisation du webhook entrant
WEBHOOK_SECRET_TOKEN = os.getenv("WEBHOOK_SECRET_TOKEN", "secret_webhook_afi_2026")

# numero officiel whatsapp d afi pour les validations humaines
NUMERO_AFI_WHATSAPP = os.getenv("NUMERO_AFI_WHATSAPP", "22997000000@c.us")

# parametres de limitation budgetaire et de contexte
MAX_ETAPES_AGENT = 10
MAX_HISTORIQUE_MESSAGES = 12
PLAFOND_MESSAGES_HEURE = 30
TEMPERATURE_AGENT = 0.1
