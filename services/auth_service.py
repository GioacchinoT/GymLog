import msal
import requests
import json

# URL Backend
API_URL = "https://gymlog-backend-gchnc4f6b6c5grc7.northeurope-01.azurewebsites.net/api"

def get_remote_config():
    try:
        response = requests.get(f"{API_URL}/get_auth_config", timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Errore recupero config remota: {e}")
    return None

def login_microsoft(ui_callback=None):

    # 1. Configurazione
    config = get_remote_config()
    if not config: return None

    client_id = config["client_id"]
    authority = config["authority"]
    scopes = config["scopes"]

    app = msal.PublicClientApplication(client_id=client_id, authority=authority)
    
    # 2. Tentativo Silent (se c'è già un token in cache)
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(scopes, account=accounts[0])
        if result: return parse_user_data(result)

    # 3. Device Code Flow (Il metodo sicuro per Android)
    try:
        # Chiediamo a Microsoft un codice per il dispositivo
        flow = app.initiate_device_flow(scopes=scopes)
        
        if "user_code" not in flow:
            print("Errore: Nessun user_code nel flusso")
            return None

        # --- AGGIORNIAMO LA GRAFICA ---
        # Passiamo il codice e l'URL alla pagina Flet per mostrarli all'utente
        if ui_callback:
            ui_callback(flow["user_code"], flow["verification_uri"])
        
        # --- ATTESA ---
        # Questa funzione BLOCCA l'esecuzione finché l'utente non conferma sul browser
        print("In attesa che l'utente inserisca il codice nel browser...")
        result = app.acquire_token_by_device_flow(flow)
        
        if "access_token" in result:
            return parse_user_data(result)
        else:
            print(f"Errore token: {result.get('error_description')}")
            return None

    except Exception as e:
        print(f"Eccezione durante il login: {e}")
        return None

def parse_user_data(result):
    if "id_token_claims" in result:
        claims = result["id_token_claims"]
        return {
            "name": claims.get("name", "Utente"),
            "email": claims.get("preferred_username") or claims.get("email"),
            "oid": claims.get("oid")
        }
    return None