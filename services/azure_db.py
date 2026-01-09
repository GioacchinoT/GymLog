import threading
import requests

# URL DEL TUO SERVER LOCALE (Azure Functions)
# Quando andrai online su Azure, cambierai solo questa riga!
API_URL = "https://gymlog-backend-gchnc4f6b6c5grc7.northeurope-01.azurewebsites.net/api"

# --- 1. GESTIONE SCHEDE ---

def get_schede(user_email):
    """Chiede la lista schede al Server"""
    try:
        # Chiama l'endpoint GET /get_schede
        response = requests.get(f"{API_URL}/get_schede", params={"user_email": user_email})
        
        if response.status_code == 200:
            return response.json() # Restituisce la lista pulita
        else:
            print(f"⚠️ Errore API Server: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Errore connessione API (Backend spento?): {e}")
        return []

def save_scheda(workout_data):
    """Invia i dati della scheda al Server per il salvataggio"""
    def _req():
        try:
            requests.post(f"{API_URL}/save_scheda", json=workout_data)
            print("✅ Scheda inviata al backend con successo!")
        except Exception as e:
            print(f"❌ Errore invio scheda: {e}")
    threading.Thread(target=_req).start()

def delete_scheda(workout_id, user_email):
    """Ordina al Server di eliminare una scheda"""
    try:
        payload = {"id": workout_id, "user_email": user_email}
        response = requests.post(f"{API_URL}/delete_scheda", json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Errore richiesta eliminazione: {e}")
        return False

# --- 2. GESTIONE ESERCIZI ---

def get_exercise(user_email):
    """Chiede il catalogo esercizi al Server"""
    try:
        response = requests.get(f"{API_URL}/get_exercises", params={"user_email": user_email})
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"❌ Errore recupero esercizi: {e}")
        return []
    
def get_all_exercises_full(user_email):
    """Recupera lista completa esercizi (con ID) per la pagina di gestione"""
    try:
        response = requests.get(f"{API_URL}/get_exercises_full", params={"user_email": user_email})
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"❌ Errore full exercises: {e}")
        return []

def add_custom_exercise(nome_esercizio, user_email):
    """Invia un nuovo esercizio al Server"""
    def _req():
        try:
            # Inviamo un nome utente generico o recuperato dalla sessione
            payload = {"exercise_name": nome_esercizio, "user_email": user_email} 
            requests.post(f"{API_URL}/add_exercise", json=payload)
            print(f"✅ Richiesta aggiunta esercizio '{nome_esercizio}' inviata. ---------------- user_email: ", user_email)
        except Exception as e:
            print(f"❌ Errore aggiunta esercizio: {e}")
    threading.Thread(target=_req).start()


# Aggiorna questa funzione per accettare e inviare ex_name
def delete_exercise_api(ex_id, user_email, ex_name):
    """Elimina un esercizio dal catalogo"""
    def _req():
        try:
            # Aggiungiamo exercise_name al payload
            payload = {
                "id": ex_id, 
                "user_email": user_email, 
                "exercise_name": ex_name
            }
            response = requests.post(f"{API_URL}/delete_exercise", json=payload)
            
            if response.status_code == 200:
                print(f"✅ Esercizio {ex_name} eliminato con successo.")
            else:
                print(f"❌ ERRORE Backend ({response.status_code}): {response.text}")

        except Exception as e:
            print(f"❌ Errore richiesta eliminazione: {e}")
            
    t = threading.Thread(target=_req)
    t.start()
    t.join() 
    return True


# --- 4. AI OCR ---

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

def generate_workout_ai(user_prompt, user_email):
    """
    Invia il prompt dell'utente all'Azure Function e riceve la scheda JSON.
    """
    try:
        print(f"------> Chiedo all'AI: {user_prompt}")
        payload = {"prompt": user_prompt, "user_email": user_email}
        
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


def save_new_user(user_data):
    """Invia i dati dell utente al Server per il salvataggio"""
    def _req():
        try:
            requests.post(f"{API_URL}/save_new_user", json=user_data)
            print("✅ User_data inviata al backend con successo!")
        except Exception as e:
            print(f"❌ Errore invio dati utente: {e}")
    threading.Thread(target=_req).start()


def update_user(user_biometrics):
    """Invia i dati dell utente al Server per il salvataggio"""
    def _req():
        try:
            response = requests.post(f"{API_URL}/update_user", json=user_biometrics)
            
            if response.status_code == 200:
                print("✅ User_biometrics aggiornati con successo!")
            else:
                # Questo ti aiuterà a capire cosa non va se succede di nuovo
                print(f"⚠️ Errore aggiornamento ({response.status_code}): {response.text}")
                
        except Exception as e:
            print(f"❌ Errore connessione update_user: {e}")
            
    threading.Thread(target=_req).start()

def get_user_data(oid):
    """
    Recupera i dati completi dell'utente (peso, altezza, età) dato l'OID.
    Ritorna un dizionario o None se fallisce.
    """
    try:
        # Nota: usiamo params=... perché è una richiesta GET
        response = requests.get(f"{API_URL}/get_user_data", params={"oid": oid})
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Dati utente recuperati: Peso={data.get('peso')}, Altezza={data.get('altezza')}")
            return data
        else:
            print(f"⚠️ Impossibile recuperare dati utente ({response.status_code}): {response.text}")
            return None
    except Exception as e:
        print(f"❌ Errore connessione get_user_data: {e}")
        return None
    
########### GESTIONE ALLENAMENTO ###############

# --- 6. GESTIONE LOG ALLENAMENTO ---

# AGGIUNGI QUESTA FUNZIONE SPECIFICA PER IL SALVATAGGIO SINCRONO
def save_workout_log_blocking(log_data):
    """
    Salva un allenamento e ATTENDE la risposta del server.
    Restituisce True se salvato, False se errore.
    """
    try:
        print("⏳ Attendo salvataggio allenamento...")
        response = requests.post(f"{API_URL}/save_workout_log", json=log_data)
        
        if response.status_code == 200:
            print("✅ Allenamento salvato e confermato dal server!")
            return True
        else:
            print(f"⚠️ Errore API: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Errore salvataggio bloccante: {e}")
        return False


def get_workout_logs(user_email):
    """Recupera lo storico allenamenti"""
    try:
        response = requests.get(f"{API_URL}/get_workout_logs", params={"user_email": user_email})
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"❌ Errore storico: {e}")
        return []