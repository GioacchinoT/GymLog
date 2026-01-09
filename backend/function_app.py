import azure.functions as func
import logging
import os
import json
import uuid
from datetime import datetime
from azure.cosmos import CosmosClient, exceptions
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
    container_schede = database.get_container_client("Schede")
    container_esercizi = database.get_container_client("Esercizi")
    container_user = database.get_container_client("User")
    container_logs = database.get_container_client("Allenamenti") 
except Exception as e:
    logging.error(f"Errore critico inizializzazione DB: {e}")


# ==================================================================================
# 1. AUTENTICAZIONE 
# ==================================================================================

# Aggiungi questo import se manca
# from function_app import get_secret

@app.route(route="get_auth_config", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
def get_auth_config(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Recupera l'ID dal Key Vault usando la tua funzione helper esistente
        client_id = get_secret("CLIENT-ID-APP-AUTH")
        
        if not client_id:
            return func.HttpResponse("Configurazione server mancante (Key Vault)", status_code=500)

        config = {
            "client_id": client_id,
            "authority": "https://login.microsoftonline.com/common",
            "scopes": ["User.Read"]
        }
        
        return func.HttpResponse(json.dumps(config), status_code=200, mimetype="application/json")
    except Exception as e:
        return func.HttpResponse(f"Errore config: {str(e)}", status_code=500)


# ==================================================================================
# 2. GESTIONE SCHEDE (Replica _save_workout_impl, get_schede, delete_workout)
# ==================================================================================

@app.route(route="save_scheda", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def save_scheda(req: func.HttpRequest) -> func.HttpResponse:
    try:
        workout_data = req.get_json()
        
        # Logica originale: se manca ID lo genero, aggiorno timestamp
        if "id" not in workout_data:
            workout_data["id"] = str(uuid.uuid4())
        
        workout_data["last_updated"] = datetime.now().isoformat()
        
        # Logica originale: Upsert
        container_schede.upsert_item(body=workout_data)
        
        return func.HttpResponse(json.dumps({"message": "Salvato", "id": workout_data["id"]}), status_code=200)
    except Exception as e:
        return func.HttpResponse(f"Errore: {str(e)}", status_code=500)

@app.route(route="get_schede", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
def get_schede(req: func.HttpRequest) -> func.HttpResponse:
    user_email = req.params.get('user_email')
    try:
        # Logica originale: Query specifica
        query = "SELECT * FROM c WHERE c.user_email = @user AND c.type = 'scheda'"
        parameters = [{"name": "@user", "value": user_email}]
        
        items = list(container_schede.query_items(
            query=query, 
            parameters=parameters, 
            enable_cross_partition_query=True
        ))
        
        return func.HttpResponse(json.dumps(items), status_code=200, mimetype="application/json")
    except Exception as e:
        return func.HttpResponse(f"Errore: {str(e)}", status_code=500)

@app.route(route="delete_scheda", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def delete_scheda(req: func.HttpRequest) -> func.HttpResponse:
    try:
        data = req.get_json()
        w_id = data.get('id')
        user = data.get('user_email')
        
        # Logica originale: Delete con partition key
        container_schede.delete_item(item=w_id, partition_key=user)
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
        user_email = req.params.get('user_email')
    
        query = """
            SELECT c.exercise_name 
            FROM c 
            WHERE c.type = 'esercizio_catalogo' 
            AND (c.user_email = 'system' OR c.user_email = @user) 
            ORDER BY c.exercise_name ASC
        """
        parameters = [{"name": "@user", "value": user_email}]
        
        items = list(container_esercizi.query_items(
            query=query, 
            parameters=parameters, 
            enable_cross_partition_query=True
        ))
        
        # Restituisco la lista semplice di nomi come faceva la tua funzione locale
        names = [item['exercise_name'] for item in items]
        return func.HttpResponse(json.dumps(names), status_code=200, mimetype="application/json")
    except Exception as e:
        return func.HttpResponse(f"Errore: {str(e)}", status_code=500)
    

@app.route(route="get_exercises_full", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
def get_exercises_full(req: func.HttpRequest) -> func.HttpResponse:
    """Restituisce gli esercizi completi (ID e Nome) per la gestione"""
    try:
        user_email = req.params.get('user_email')
        
        # Prendiamo sia quelli di sistema che quelli dell'utente
        query = """
            SELECT *
            FROM c 
            WHERE c.type = 'esercizio_catalogo' 
            AND (c.user_email = 'system' OR c.user_email = @user) 
            ORDER BY c.exercise_name ASC
        """
        parameters = [{"name": "@user", "value": user_email}]
        
        items = list(container_esercizi.query_items(
            query=query, 
            parameters=parameters, 
            enable_cross_partition_query=True
        ))
        
        return func.HttpResponse(json.dumps(items), status_code=200, mimetype="application/json")
    except Exception as e:
        return func.HttpResponse(f"Errore: {str(e)}", status_code=500)

@app.route(route="add_exercise", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def add_exercise(req: func.HttpRequest) -> func.HttpResponse:
    try:
        data = req.get_json()
        # Logica originale di creazione esercizio custom
        item = {
            "id": str(uuid.uuid4()),
            "user_email": data.get("user_email", "system"), 
            "exercise_name": data.get("exercise_name"),
            "type": "esercizio_catalogo",
            "creato_il": datetime.now().isoformat()
        }
        container_esercizi.create_item(body=item)
        return func.HttpResponse("Aggiunto", status_code=200)
    except Exception as e:
        return func.HttpResponse(f"Errore: {str(e)}", status_code=500)
    

@app.route(route="delete_exercise", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def delete_exercise(req: func.HttpRequest) -> func.HttpResponse:
    try:
        data = req.get_json()
        ex_id = data.get('id')
        # Recuperiamo il nome, fondamentale perché è la Partition Key
        ex_name = data.get('exercise_name') 
        
        logging.info(f"Tentativo eliminazione ID: {ex_id} - Nome: {ex_name}")

        # TENTATIVO DIRETTO: Chiave partizione = exercise_name (Configurazione Utente)
        try:
            container_esercizi.delete_item(item=ex_id, partition_key=ex_name)
            return func.HttpResponse("Eliminato (Key: Name)", status_code=200)
        except exceptions.CosmosResourceNotFoundError:
            # Fallback (giusto per sicurezza)
            logging.warning("Non trovato con PK=name. Provo altre chiavi...")
            try:
                # Tentativo disperato con ID (se mai cambiasse configurazione)
                container_esercizi.delete_item(item=ex_id, partition_key=ex_id)
                return func.HttpResponse("Eliminato (Key: ID)", status_code=200)
            except:
                return func.HttpResponse("Impossibile trovare l'item.", status_code=404)

    except Exception as e:
        logging.error(f"Errore delete: {str(e)}")
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
        user_email = req_body.get('user_email', 'User')

        if not user_prompt:
            return func.HttpResponse("Prompt mancante", status_code=400)

        # Configurazione Client (Gestisce sia Azure che Standard)
        if "azure" in str(OPENAI_ENDPOINT).lower():
            client = AzureOpenAI(
                azure_endpoint=OPENAI_ENDPOINT, 
                api_key=OPENAI_KEY, 
                api_version="2023-05-15"
            )

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
                    "exercise_name": "Nome Esercizio",
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
                {"role": "user", "content": f"Utente: {user_email}. Richiesta: {user_prompt}"}
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
        workout_json["user_email"] = user_email
        workout_json["type"] = "scheda"
        workout_json["created_at"] = datetime.now().strftime("%Y-%m-%d")
        workout_json["ai_generated"] = True # Flag importante

        return func.HttpResponse(json.dumps(workout_json), status_code=200, mimetype="application/json")

    except Exception as e:
        logging.error(f"GenAI Error: {e}")
        return func.HttpResponse(f"Errore generazione: {str(e)}", status_code=500)
    

# ==================================================================================
# 5. GESTIONE DATI UTENTE
# ==================================================================================

@app.route(route="save_new_user", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def save_new_user(req: func.HttpRequest) -> func.HttpResponse:
    try:
        user_data = req.get_json()
        
        # 1. Estraiamo l'OID (il codice fiscale digitale Microsoft)
        oid = user_data.get("oid")
        email = user_data.get("email")
        name = user_data.get("name")

        if not oid:
            return func.HttpResponse("OID mancante: impossibile identificare utente.", status_code=400)

        # 2. CONTROLLO DI UNICITÀ
        # Cerchiamo nel DB se c'è già un utente con questo OID
        query = "SELECT * FROM c WHERE c.oid = @oid"
        parameters = [{"name": "@oid", "value": oid}]
        
        items = list(container_user.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))

        # 3. LOGICA DI SALVATAGGIO
        if len(items) > 0:
            # CASO A: L'utente esiste già.
            # (Opzionale) Potresti aggiornare un campo "last_login" qui se volessi
            logging.info(f"Utente {email} già presente nel DB. Salto il salvataggio.")
            return func.HttpResponse("Utente già registrato", status_code=200)
        
        else:
            # CASO B: È la prima volta che entra. 
            new_user = {
                "id": oid,          # Usiamo l'OID anche come ID del documento per efficienza
                "oid": oid,         # Salviamolo anche esplicitamente
                "user_name": name,
                "user_email": email,
                "peso": "inserisci dati",
                "altezza": "inserisci dati",
                "età": "inserisci dati", 
                "created_at": datetime.now().isoformat(),
            }
            
            container_user.create_item(body=new_user)
            logging.info(f"Benvenuto! Nuovo utente registrato: {email}")
            return func.HttpResponse("Nuovo utente creato", status_code=201)

    except Exception as e:
        logging.error(f"Errore save_user: {e}")
        return func.HttpResponse(f"Errore: {str(e)}", status_code=500)
@app.route(route="update_user", auth_level=func.AuthLevel.ANONYMOUS)
def update_user(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('--- UPDATE USER START ---')

    try:
        req_body = req.get_json()
        
        # Dati in arrivo
        oid = req_body.get('oid')
        peso = req_body.get('peso')
        altezza = req_body.get('altezza')
        eta = req_body.get('età')

        print("oid peso altezza eta -----------> ", oid, peso, altezza, eta)

        if not oid:
            return func.HttpResponse("Errore: OID mancante.", status_code=400)

        logging.info(f"Cercando utente con OID: {oid}")

        # 1. CERCHIAMO L'UTENTE TRAMITE QUERY
        # Questo aggira il problema della Partition Key errata
        query = "SELECT * FROM c WHERE c.oid = @oid"
        parameters = [{"name": "@oid", "value": oid}]
        
        items = list(container_user.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))

        if not items:
            logging.warning(f"Nessun utente trovato con OID: {oid}")
            return func.HttpResponse("Utente non trovato nel database.", status_code=404)

        # 2. RECUPERIAMO IL DOCUMENTO REALE
        user_item = items[0]
        logging.info(f"Utente trovato: {user_item.get('user_email')}")
        print("utente trovato--->", user_item)

        # 3. AGGIORNIAMO I CAMPI (Solo se l'utente ha scritto qualcosa)
        # Convertiamo in stringa o numero a seconda di come vuoi salvarli, 
        # qui li salvo come stringhe per sicurezza, ma puoi fare int() se preferisci.
        if peso: 
            user_item['peso'] = str(peso)
        if altezza: 
            user_item['altezza'] = str(altezza)
        if eta: 
            user_item['età'] = str(eta)
        

        # 4. SALVIAMO (UPSERT)
        # Cosmos DB è intelligente: leggendo user_item, sa già qual è la partition key corretta (l'email)
        # che si trova dentro l'oggetto stesso.
        container_user.upsert_item(body=user_item)

        logging.info("Dati aggiornati e salvati correttamente.")
        return func.HttpResponse(
            f"Dati aggiornati correttamente.",
            status_code=200
        )

    except Exception as e:
        logging.error(f"CRITICAL ERROR in update_user: {str(e)}")
        return func.HttpResponse(f"Errore interno: {str(e)}", status_code=500)
    
@app.route(route="get_user_data", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
def get_user_data(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('--- GET USER DATA START ---')

    try:
        # Recuperiamo l'oid dai parametri dell'URL (es: ?oid=123...)
        oid = req.params.get('oid')

        if not oid:
            return func.HttpResponse("Errore: parametro 'oid' mancante.", status_code=400)

        # Usiamo la Query (metodo sicuro)
        query = "SELECT * FROM c WHERE c.oid = @oid"
        parameters = [{"name": "@oid", "value": oid}]
        
        items = list(container_user.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))

        if not items:
            logging.warning(f"Nessun utente trovato con OID: {oid}")
            return func.HttpResponse("Utente non trovato.", status_code=404)

        # Prendiamo il primo risultato
        user_data = items[0]

        # Rimuoviamo campi interni di Cosmos DB che non servono al frontend (opzionale ma pulito)
        # user_data.pop('_rid', None)
        # user_data.pop('_self', None)
        # user_data.pop('_etag', None)
        # user_data.pop('_attachments', None)
        # user_data.pop('_ts', None)

        return func.HttpResponse(
            json.dumps(user_data),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Errore in get_user_data: {str(e)}")
        return func.HttpResponse(f"Errore interno: {str(e)}", status_code=500)
    

# ==================================================================================
# 6. GESTIONE LOG ALLENAMENTO (STORICO)
# ==================================================================================

@app.route(route="save_workout_log", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def save_workout_log(req: func.HttpRequest) -> func.HttpResponse:
    try:
        log_data = req.get_json()
        log_data["id"] = str(uuid.uuid4())
        log_data["type"] = "workout_log"
        log_data["completed_at"] = datetime.now().isoformat()
        
        container_logs.create_item(body=log_data)
        return func.HttpResponse("Allenamento salvato", status_code=200)
    except Exception as e:
        return func.HttpResponse(f"Errore: {str(e)}", status_code=500)

@app.route(route="get_workout_logs", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
def get_workout_logs(req: func.HttpRequest) -> func.HttpResponse:
    user_email = req.params.get('user_email')
    try:
        # Ordiniamo per data decrescente (dal più recente)
        query = "SELECT * FROM c WHERE c.user_email = @user AND c.type = 'workout_log' ORDER BY c.completed_at DESC"
        parameters = [{"name": "@user", "value": user_email}]
        
        items = list(container_logs.query_items(
            query=query, parameters=parameters, enable_cross_partition_query=True
        ))
        print(items)
        return func.HttpResponse(json.dumps(items), status_code=200, mimetype="application/json")
    except Exception as e:
        return func.HttpResponse(f"Errore: {str(e)}", status_code=500)