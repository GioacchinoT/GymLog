# init_db.py
from services.azure_db import database
from config import CURRENT_USER
import uuid

# Lista iniziale
ESERCIZI_BASE = [
    "Panca Piana", "Squat", "Stacchi da Terra", 
    "Military Press", "Trazioni alla sbarra", "Rematore Bilanciere",
    "Curl Bicipiti", "Push Down Tricipiti", "Leg Extension",
    "Leg Press", "Affondi", "Crunch Addominali"
]

def popola_esercizi():
    container = database.get_container_client("Workout")
    print(" Inizio caricamento esercizi...")
    
    for nome in ESERCIZI_BASE:
        item = {
            "username": CURRENT_USER,
            "id": str(uuid.uuid4()),
            "name": nome,
            "type": "esercizio_catalogo"
        }
        try:
            container.create_item(body=item)
            print(f"✅ Inserito: {nome}")
        except Exception as e:
            print(f"❌ Errore {nome}: {e}")

    print(" Finito! Ora puoi cancellare questo file.")

if __name__ == "__main__":
    popola_esercizi()