FROM python:3.10-slim

WORKDIR /app

# Installation des dependances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie de l ensemble du projet
COPY . .

# Droits d ecriture pour la persistance du stock et des commandes
RUN chmod -R 777 /app

# Port interne standard utilise par Hugging Face Spaces
EXPOSE 7860

# Commande de demarrage de l agent vendeur FastAPI
CMD ["uvicorn", "numero_3.serveur:app", "--host", "0.0.0.0", "--port", "7860"]
