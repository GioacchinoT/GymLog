import uuid
import time
from azure.cosmos import CosmosClient


COSMOS_ENDPOINT = "https://gymlog-cosmos-db.documents.azure.com:443/" 
COSMOS_KEY = "hrexsEjbIkbKYYpEnKUvoM6K2NNLoZRyUA6mQVxWOUOXykzcLjbhjPkqEhMIiSnX5uOfkVwvyxHgACDb0JRpcg===="
DB_NAME = "GymLogDB" 

# CONFIGURAZIONE BASE 
print("... Mi connetto a Cosmos DB...")
try:
    client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    database = client.get_database_client(DB_NAME)
    
    
    container = database.get_container_client("Esercizi") 
    print("--->  Connesso al Container 'Esercizi'!")
except Exception as e:
    print(f"XXX --- Errore connessione: {e}")
    exit()

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

print(f"... Inizio inserimento di {len(lista_esercizi)} esercizi...")

count = 0
for nome in lista_esercizi:
    try:
        nuovo_esercizio = {
            "id": str(uuid.uuid4()),      
            "exercise_name": nome,        
            "type": "esercizio_catalogo", 
            "user_email": "system"        
        }
        
        container.create_item(body=nuovo_esercizio)
        print(f"   [OK] Inserito: {nome}")
        count += 1
        time.sleep(0.1) 
    except Exception as e:
        print(f"   [ERRORE] {nome}: {e}")

print(f"\n Inseriti {count} esercizi.")