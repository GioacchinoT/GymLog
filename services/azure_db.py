import threading
import requests

# URL DEL TUO SERVER LOCALE (Azure Functions)
# Quando andrai online su Azure, cambierai solo questa riga!
API_URL = "http://localhost:7071/api"

# --- 1. GESTIONE SCHEDE ---

def get_workouts(user_name):
    """Chiede la lista schede al Server"""
    try:
        # Chiama l'endpoint GET /get_workouts
        response = requests.get(f"{API_URL}/get_workouts", params={"username": user_name})
        
        if response.status_code == 200:
            return response.json() # Restituisce la lista pulita
        else:
            print(f"⚠️ Errore API Server: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Errore connessione API (Backend spento?): {e}")
        return []

def save_workout_async(workout_data):
    """Invia i dati della scheda al Server per il salvataggio"""
    def _req():
        try:
            requests.post(f"{API_URL}/save_workout", json=workout_data)
            print("✅ Scheda inviata al backend con successo!")
        except Exception as e:
            print(f"❌ Errore invio scheda: {e}")
    threading.Thread(target=_req).start()

def delete_workout(workout_id, user_name):
    """Ordina al Server di eliminare una scheda"""
    try:
        payload = {"id": workout_id, "username": user_name}
        response = requests.post(f"{API_URL}/delete_workout", json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Errore richiesta eliminazione: {e}")
        return False

# --- 2. GESTIONE ESERCIZI ---

def get_all_exercises():
    """Chiede il catalogo esercizi al Server"""
    try:
        response = requests.get(f"{API_URL}/get_exercises")
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"❌ Errore recupero esercizi: {e}")
        return []

def add_custom_exercise_async(nome_esercizio):
    """Invia un nuovo esercizio al Server"""
    def _req():
        try:
            # Inviamo un nome utente generico o recuperato dalla sessione
            payload = {"name": nome_esercizio, "username": "app_user"} 
            requests.post(f"{API_URL}/add_exercise", json=payload)
            print(f"✅ Richiesta aggiunta esercizio '{nome_esercizio}' inviata.")
        except Exception as e:
            print(f"❌ Errore aggiunta esercizio: {e}")
    threading.Thread(target=_req).start()

# --- 3. GESTIONE ACQUA ---

def save_water_async(user_name, amount):
    """Invia il log dell'acqua al Server"""
    def _req():
        try:
            payload = {"username": user_name, "amount": amount}
            requests.post(f"{API_URL}/save_water", json=payload)
        except Exception as e:
            print(f"❌ Errore invio acqua: {e}")
    threading.Thread(target=_req).start()

# --- 4. AI (PROXY) ---

def analyze_workout_image(image_bytes):
    """
    Invia la foto grezza al Server. 
    Il Client NON ha più le chiavi di Azure AI!
    """
    try:
        print("⏳ Invio immagine al server backend...")
        # Inviamo il file come multipart
        files = {'file': ('image.jpg', image_bytes, 'image/jpeg')}
        
        response = requests.post(f"{API_URL}/analyze_image", files=files)
        
        if response.status_code == 200:
            print("✅ Analisi ricevuta dal server!")
            return response.json() 
        else:
            print(f"❌ Errore Server AI: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Errore chiamata AI: {e}")
        return None
    

# --- 5. AI GENERATIVA (COACH) ---

def generate_workout_ai(user_prompt, user_name):
    """
    Invia il prompt dell'utente all'Azure Function e riceve la scheda JSON.
    """
    try:
        print(f"------> Chiedo all'AI: {user_prompt}")
        payload = {"prompt": user_prompt, "username": user_name}
        
        # Timeout alto (30s) perché l'AI ci mette un po' a pensare
        response = requests.post(f"{API_URL}/generate_workout", json=payload, timeout=30)
        
        if response.status_code == 200:
            print("--------> Scheda generata dall'AI!")
            return response.json()
        else:
            print(f"XXXXXXXXX Errore AI: {response.text}")
            return None
    except Exception as e:
        print(f"XXXXXXX Errore connessione AI: {e}")
        return None

    