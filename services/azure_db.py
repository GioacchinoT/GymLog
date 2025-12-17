import threading
import uuid
from datetime import datetime
from azure.cosmos import CosmosClient
from config import settings, CURRENT_USER



    # Controllo sicurezza: se le chiavi mancano o sono quelle di default
if not settings.COSMOS_ENDPOINT or "tuo-account" in settings.COSMOS_ENDPOINT:
    print("⚠️ Configurazione Azure mancante. I dati non verranno salvati sul cloud.")
try:
    client = CosmosClient(settings.COSMOS_ENDPOINT, settings.COSMOS_KEY)
    database = client.get_database_client(settings.DATABASE_NAME)
except Exception as e:
    print(f"❌ Errore Connessione Cosmos: {e}")


# --- SALVATAGGIO ACQUA ---
def _log_water_impl(user_name, amount):
    """Logica interna per salvare l'acqua"""
    container = database.get_container_client("Water") ############# MODIFICA CONTAINER
    if not container: return

    try:
        # Documento JSON per Cosmos DB
        item = {
            "id": str(uuid.uuid4()),      # ID univoco obbligatorio
            "username": user_name,        # Partition Key obbligatoria
            "type": "water_log",          # Per filtrare i dati in futuro
            "amount_ml": amount,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": datetime.now().isoformat()
        }
        
        container.create_item(body=item)
        print(f"✅ CosmosDB: {amount}ml salvati per {user_name}")
        
    except Exception as e:
        print(f"❌ Errore Salvataggio Acqua: {e}")

def save_water_async(user_name, amount):
    """Lancia il salvataggio in un thread separato (non blocca la grafica)"""
    threading.Thread(target=_log_water_impl, args=(user_name, amount)).start()




# --- GESTIONE SCHEDE (WORKOUTS) ---

def _save_workout_impl(workout_data):
    """Logica interna per salvare le schede complete"""
    container = database.get_container_client("Workout")
    if not container: return

    try:
        # Assicuriamoci che i campi di sistema ci siano
        if "id" not in workout_data:
            workout_data["id"] = str(uuid.uuid4())
        
        # Aggiungiamo timestamp se manca
        workout_data["timestamp"] = datetime.now().isoformat()
        
        container.create_item(body=workout_data)
        print(f"✅ CosmosDB: Scheda '{workout_data.get('nome_scheda')}' salvata!")
        
    except Exception as e:
        print(f"❌ Errore Salvataggio Workout: {e}")

def save_workout_async(workout_data):
    """Lancia il salvataggio del dizionario scheda in background"""
    threading.Thread(target=_save_workout_impl, args=(workout_data,)).start()

def get_workouts(user_name):
    """Recupera tutte le schede di un utente specifico"""
    container = database.get_container_client("Workout")
    if not container: return []

    try:
        # Query SQL: Seleziona documenti dove username corrisponde e il tipo è 'scheda'
        query = "SELECT * FROM c WHERE c.username = @user AND c.type = 'scheda'"
        parameters = [{"name": "@user", "value": user_name}]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=False
        ))
        return items
    except Exception as e:
        print(f"❌ Errore Recupero Schede: {e}")
        return []
    

# --------------- GESTIONE ESERCIZI

def get_all_exercises():
    """Scarica la lista di tutti gli esercizi disponibili dal DB"""
    container = database.get_container_client("Workout")
    if not container: return []

    try:
        # Selezioniamo solo il nome per riempire il menu a tendina
        # Ordiniamo per nome (c.nome) in ordine alfabetico (ASC)
        query = "SELECT c.name FROM c WHERE c.type = 'esercizio_catalogo' ORDER BY c.nome ASC"
        
        items = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        return [item['name'] for item in items]
    except Exception as e:
        print(f"❌ Errore Recupero Esercizi: {e}")
        return []


def add_custom_exercise_async(nome_esercizio):
    """Salva un nuovo esercizio nel database esercizi se non esiste"""
    def _impl():
        container = database.get_container_client("Workout")
        if not container: return

        try:
            # Controllo base per evitare duplicati (opzionale ma consigliato)
            # Nota: In produzione sarebbe meglio fare una query per controllare se esiste
            item = {
                "username": CURRENT_USER,
                "id": str(uuid.uuid4()),
                "name": nome_esercizio, # Partition Key (se impostata come /nome) o campo dati
                "type": "esercizio_catalogo",
                "creato_il": datetime.now().isoformat()
            }
            container.create_item(body=item)
            print(f"✅ Nuovo esercizio '{nome_esercizio}' aggiunto al catalogo!")
        except Exception as e:
            print(f"⚠️ Esercizio forse già esistente o errore: {e}")

    threading.Thread(target=_impl).start()