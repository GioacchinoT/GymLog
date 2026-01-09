import msal
import requests
import json

# --- NON ABBIAMO PIU COSTANTI HARDCODATE QUI ---
# URL della tua Function App (assicurati che sia corretto, es. localhost o azure)
API_URL = "https://gymlog-backend-gchnc4f6b6c5grc7.northeurope-01.azurewebsites.net/api" # O il link di produzione

def get_remote_config():
    """Scarica la configurazione di login dal Backend (che la legge dal Key Vault)"""
    try:
        response = requests.get(f"{API_URL}/get_auth_config")
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Errore recupero config remota: {e}")
    return None

def login_microsoft():
    # 1. SCARICHIAMO LA CONFIGURAZIONE DINAMICA
    config = get_remote_config()
    
    if not config:
        print("Impossibile recuperare il Client ID dal server.")
        return None

    client_id = config["client_id"]
    authority = config["authority"]
    scopes = config["scopes"]

    # 2. Procediamo con il login normale usando i dati scaricati
    app = msal.PublicClientApplication(client_id=client_id, authority=authority)
    
    # Tentativo 1: Login silenzioso
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(scopes, account=accounts[0])
        if result:
            return parse_user_data(result)

    # Tentativo 2: Login interattivo
    print("Avvio login interattivo Microsoft...")
    result = app.acquire_token_interactive(scopes=scopes)
    
    if "error" in result:
        print(f"Errore Login: {result.get('error_description')}")
        return None
    
    return parse_user_data(result)

def parse_user_data(result):
    """Estrae i dati utili dal token"""
    if "id_token_claims" in result:
        claims = result["id_token_claims"]
        return {
            "name": claims.get("name", "Utente"),
            "email": claims.get("preferred_username") or claims.get("email"),
            "oid": claims.get("oid")
        }
    return None

def logout_microsoft():
    # Anche per il logout serve l'ID, quindi lo richiediamo (o potresti salvarlo in una variabile globale)
    config = get_remote_config()
    if config:
        app = msal.PublicClientApplication(client_id=config["client_id"], authority=config["authority"])
        accounts = app.get_accounts()
        if accounts:
            app.remove_account(accounts[0])