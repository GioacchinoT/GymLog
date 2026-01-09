import uuid
import time
from azure.cosmos import CosmosClient

# --- 1. INCOLLA QUI LE TUE CHIAVI (Prendile da local.settings.json) ---
# Copiale senza le virgolette esterne extra, solo la stringa
COSMOS_ENDPOINT = "https://gymlog-cosmos-db.documents.azure.com:443/" 
COSMOS_KEY = "hrexsEjbIkbKYYpEnKUvoM6K2NNLoZRyUA6mQVxWOUOXykzcLjbhjPkqEhMIiSnX5uOfkVwvyxHgACDb0JRpcg===="
DB_NAME = "GymLogDB" # O come l'hai chiamato

# --- 2. CONFIGURAZIONE BASE ---
print("🔌 Mi connetto a Cosmos DB...")
try:
    client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    database = client.get_database_client(DB_NAME)
    
    # Assicurati che il contenitore "Esercizi" esista, altrimenti crealo a mano su Azure
    container = database.get_container_client("Esercizi") 
    print("✅ Connesso al Container 'Esercizi'!")
except Exception as e:
    print(f"❌ Errore connessione: {e}")
    exit()

# --- 3. LISTA ESERCIZI DA INSERIRE ---
# Puoi allungare questa lista quanto vuoi
lista_esercizi = [
    "Panca Piana",
    "Panca Inclinata Manubri",
    "Croci ai Cavi",
    "Squat Libero",
    "Leg Press",
    "Leg Extension",
    "Stacchi da Terra",
    "Lat Machine",
    "Pulley Basso",
    "Rematore Manubrio",
    "Military Press",
    "Alzate Laterali",
    "Curl Bilanciere",
    "Curl Manubri",
    "Push Down Tricipiti",
    "French Press",
    "Crunch Addominali",
    "Plank"
]

# --- 4. INSERIMENTO DATI ---
print(f"🚀 Inizio inserimento di {len(lista_esercizi)} esercizi...")

count = 0
for nome in lista_esercizi:
    try:
        # Creiamo l'oggetto JSON
        nuovo_esercizio = {
            "id": str(uuid.uuid4()),      # ID univoco
            "exercise_name": nome,                 # Nome esercizio
            "type": "esercizio_catalogo", # Tipo dato (fondamentale per i filtri)
            "user_email": "system"        # Utente 'sistema' (visibile a tutti)
        }
        
        container.create_item(body=nuovo_esercizio)
        print(f"   [OK] Inserito: {nome}")
        count += 1
        time.sleep(0.1) # Piccola pausa per non intasare
    except Exception as e:
        print(f"   [ERRORE] {nome}: {e}")

print(f"\n🎉 Finito! Inseriti {count} esercizi.")