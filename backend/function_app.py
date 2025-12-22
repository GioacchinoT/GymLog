import azure.functions as func
import logging
import os
import json
import uuid
from datetime import datetime
from azure.cosmos import CosmosClient
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient 


app = func.FunctionApp()


# URL DEL VAULT PER LE CHIAVI
KEY_VAULT_URL = os.environ.get("KEY_VAULT_URL")

def get_secret(secret_name, fallback_env_var=None):
    """
    Tenta di leggere dal Key Vault. Se fallisce
    """
    if KEY_VAULT_URL:
        try:
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=KEY_VAULT_URL, credential=credential)
            return client.get_secret(secret_name).value
        except Exception as e:
            logging.warning(f"Impossibile leggere '{secret_name}' da Key Vault: {e}")
    
    # Fallback: se Key Vault non va o non è configurato, usa le vecchie env vars
    if fallback_env_var:
        return os.environ.get(fallback_env_var)
    return None

# --- CONFIGURAZIONE ---
# Recupera le chiavi dalle variabili d'ambiente (Azure key vault)

COSMOS_ENDPOINT = get_secret("COSMOS-ENDPOINT")
COSMOS_KEY = get_secret("COSMOS-KEY")
DB_NAME = get_secret("DATABASE-NAME")
DOC_INTEL_ENDPOINT = get_secret("DOC-INTEL-ENDPOINT")
DOC_INTEL_KEY = get_secret("DOC-INTEL-KEY")
OPENAI_KEY = get_secret("OPENAI-API-KEY")
OPENAI_ENDPOINT = get_secret("OPENAI-ENDPOINT")
OPENAI_DEPLOYMENT = get_secret("OPENAI-DEPLOYMENT")





# --- INIZIALIZZAZIONE CLIENT (Eseguita una volta all'avvio) ---
try:
    cosmos_client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    database = cosmos_client.get_database_client(DB_NAME)
    container_workout = database.get_container_client("Workout") 
    #container_water = database.get_container_client("Water")
except Exception as e:
    logging.error(f"Errore critico inizializzazione DB: {e}")

# ==================================================================================
# 1. GESTIONE ACQUA (Replica la logica di _log_water_impl)
# ==================================================================================

"""@app.route(route="save_water", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def save_water(req: func.HttpRequest) -> func.HttpResponse:
    try:
        data = req.get_json()
        user_name = data.get("username")
        amount = data.get("amount")

        # Replico la tua struttura esatta del documento
        item = {
            "id": str(uuid.uuid4()),
            "username": user_name,
            "type": "water_log",
            "amount_ml": amount,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": datetime.now().isoformat()
        }
        
        container_water.create_item(body=item)
        return func.HttpResponse("Acqua salvata", status_code=200)
    except Exception as e:
        logging.error(f"Errore save_water: {e}")
        return func.HttpResponse(f"Errore: {str(e)}", status_code=500)
"""
# ==================================================================================
# 2. GESTIONE SCHEDE (Replica _save_workout_impl, get_workouts, delete_workout)
# ==================================================================================

@app.route(route="save_workout", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def save_workout(req: func.HttpRequest) -> func.HttpResponse:
    try:
        workout_data = req.get_json()
        
        # Logica originale: se manca ID lo genero, aggiorno timestamp
        if "id" not in workout_data:
            workout_data["id"] = str(uuid.uuid4())
        
        workout_data["last_updated"] = datetime.now().isoformat()
        
        # Logica originale: Upsert
        container_workout.upsert_item(body=workout_data)
        
        return func.HttpResponse(json.dumps({"message": "Salvato", "id": workout_data["id"]}), status_code=200)
    except Exception as e:
        return func.HttpResponse(f"Errore: {str(e)}", status_code=500)

@app.route(route="get_workouts", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
def get_workouts(req: func.HttpRequest) -> func.HttpResponse:
    username = req.params.get('username')
    try:
        # Logica originale: Query specifica
        query = "SELECT * FROM c WHERE c.username = @user AND c.type = 'scheda'"
        parameters = [{"name": "@user", "value": username}]
        
        items = list(container_workout.query_items(
            query=query, 
            parameters=parameters, 
            enable_cross_partition_query=False
        ))
        
        return func.HttpResponse(json.dumps(items), status_code=200, mimetype="application/json")
    except Exception as e:
        return func.HttpResponse(f"Errore: {str(e)}", status_code=500)

@app.route(route="delete_workout", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def delete_workout(req: func.HttpRequest) -> func.HttpResponse:
    try:
        data = req.get_json()
        w_id = data.get('id')
        user = data.get('username')
        
        # Logica originale: Delete con partition key
        container_workout.delete_item(item=w_id, partition_key=user)
        return func.HttpResponse("Eliminato", status_code=200)
    except Exception as e:
        return func.HttpResponse(f"Errore: {str(e)}", status_code=500)

# ==================================================================================
# 3. GESTIONE ESERCIZI (Replica get_all_exercises, add_custom_exercise_async)
# ==================================================================================

@app.route(route="get_exercises", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
def get_exercises(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Logica originale: Query specifica per 'esercizio_catalogo'
        # Nota: Ho corretto 'ORDER BY c.nome' in 'c.name' se il campo è name, 
        # ma lascio la tua query originale se nel DB usi 'nome'.
        # Basandomi sul tuo file: "SELECT c.name FROM c ... ORDER BY c.nome ASC"
        query = "SELECT c.name FROM c WHERE c.type = 'esercizio_catalogo' ORDER BY c.name ASC"
        
        items = list(container_workout.query_items(query=query, enable_cross_partition_query=True))
        
        # Restituisco la lista semplice di nomi come faceva la tua funzione locale
        names = [item['name'] for item in items]
        return func.HttpResponse(json.dumps(names), status_code=200, mimetype="application/json")
    except Exception as e:
        return func.HttpResponse(f"Errore: {str(e)}", status_code=500)

@app.route(route="add_exercise", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def add_exercise(req: func.HttpRequest) -> func.HttpResponse:
    try:
        data = req.get_json()
        # Logica originale di creazione esercizio custom
        item = {
            "id": str(uuid.uuid4()),
            "username": data.get("username", "system"), 
            "name": data.get("name"),
            "type": "esercizio_catalogo",
            "creato_il": datetime.now().isoformat()
        }
        container_workout.create_item(body=item)
        return func.HttpResponse("Aggiunto", status_code=200)
    except Exception as e:
        return func.HttpResponse(f"Errore: {str(e)}", status_code=500)

# ==================================================================================
# 4. AI ANALISI IMMAGINE (Replica analyze_workout_image)
# ==================================================================================

@app.route(route="analyze_image", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def analyze_image(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Recupero il file raw dalla richiesta
        file = req.files.get('file')
        if not file:
            return func.HttpResponse("Nessun file inviato", status_code=400)
            
        file_content = file.read()
        
        # Client AI inizializzato qui per usare le chiavi server-side
        doc_client = DocumentAnalysisClient(
            endpoint=DOC_INTEL_ENDPOINT, 
            credential=AzureKeyCredential(DOC_INTEL_KEY)
        )
        
        # Logica originale: "prebuilt-layout"
        poller = doc_client.begin_analyze_document("prebuilt-layout", document=file_content)
        result = poller.result()
        
        # SERIALIZZAZIONE:
        # Poiché non possiamo restituire l'oggetto Python 'result' direttamente via HTTP,
        # dobbiamo trasformarlo in un JSON che il tuo 'ai_utils.py' possa leggere.
        
        output = {"pages": [], "tables": []}
        
        # 1. Estrazione Linee (per il fallback riga per riga)
        for page in result.pages:
            lines_data = []
            for line in page.lines:
                lines_data.append({"content": line.content})
            output["pages"].append({"lines": lines_data})
            
        # 2. Estrazione Tabelle (per la logica avanzata celle)
        for table in result.tables:
            cells_data = []
            for cell in table.cells:
                cells_data.append({
                    "row_index": cell.row_index,
                    "column_index": cell.column_index,
                    "content": cell.content
                })
            output["tables"].append({"cells": cells_data})

        return func.HttpResponse(json.dumps(output), status_code=200, mimetype="application/json")

    except Exception as e:
        logging.error(f"AI Error: {e}")
        return func.HttpResponse(f"Errore analisi AI: {str(e)}", status_code=500)

# ==================================================================================
# 5. AI GENERATIVA (COACH)
# ==================================================================================

@app.route(route="generate_workout", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def generate_workout(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()
        user_prompt = req_body.get('prompt')
        user_name = req_body.get('username', 'User')

        if not user_prompt:
            return func.HttpResponse("Prompt mancante", status_code=400)

        # Configurazione Client (Gestisce sia Azure che Standard)
        if "azure" in str(OPENAI_ENDPOINT).lower():
            client = AzureOpenAI(
                azure_endpoint=OPENAI_ENDPOINT, 
                api_key=OPENAI_KEY, 
                api_version="2023-05-15"
            )
        else:
            client = OpenAI(api_key=OPENAI_KEY)

        # System Prompt: Istruiamo l'AI a rispondere SOLO con JSON valido
        system_msg = """
        Sei un Personal Trainer esperto. Il tuo compito è creare schede di allenamento basate sulle richieste dell'utente.
        DEVI rispondere ESCLUSIVAMENTE con un oggetto JSON valido, senza altro testo prima o dopo.
        
        La struttura del JSON deve essere ESATTAMENTE questa:
        {
            "nome_scheda": "Nome creativo della scheda",
            "split_type": "Es. Full Body, Push/Pull, etc.",
            "esercizi": [
                {
                    "name": "Nome Esercizio",
                    "serie": "Numero serie (es. 3)",
                    "ripetizioni": "Numero reps (es. 10-12)",
                    "note_ai": "Breve consiglio tecnico"
                }
            ]
        }
        """

        response = client.chat.completions.create(
            model=OPENAI_DEPLOYMENT, # Nome del deployment su Azure o modello (gpt-3.5-turbo)
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": f"Utente: {user_name}. Richiesta: {user_prompt}"}
            ],
            temperature=0.7
        )

        # Pulizia della risposta (a volte GPT mette ```json ... ```)
        content = response.choices[0].message.content
        content = content.replace("```json", "").replace("```", "").strip()
        
        # Validazione JSON
        workout_json = json.loads(content)
        
        # Aggiungiamo ID e timestamp per renderla pronta al salvataggio
        workout_json["id"] = str(uuid.uuid4())
        workout_json["username"] = user_name
        workout_json["type"] = "scheda"
        workout_json["created_at"] = datetime.now().strftime("%Y-%m-%d")
        workout_json["ai_generated"] = True # Flag importante

        return func.HttpResponse(json.dumps(workout_json), status_code=200, mimetype="application/json")

    except Exception as e:
        logging.error(f"GenAI Error: {e}")
        return func.HttpResponse(f"Errore generazione: {str(e)}", status_code=500)