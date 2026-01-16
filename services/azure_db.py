import threading
import requests

# URL FUNCTION 
API_URL = "https://gymlog-backend-gchnc4f6b6c5grc7.northeurope-01.azurewebsites.net/api"


# ---- GESTIONE SCHEDE ---- 

def get_schede(user_email):
    
    try:
        response = requests.get(f"{API_URL}/get_schede", params={"user_email": user_email})
        
        if response.status_code == 200:
            return response.json() 
        else:
            print(f"XXX --- Errore API Server: {response.text}")
            return []
    except Exception as e:
        print(f"XXX --- Errore connessione API (Backend spento?): {e}")
        return []

def save_scheda(workout_data):

    def _req():
        try:
            requests.post(f"{API_URL}/save_scheda", json=workout_data)
            print("---->  Scheda inviata al backend con successo!")
        except Exception as e:
            print(f"XXX --- Errore invio scheda: {e}")
    threading.Thread(target=_req).start()

def delete_scheda(workout_id, user_email):
    
    try:
        payload = {"id": workout_id, "user_email": user_email}
        response = requests.post(f"{API_URL}/delete_scheda", json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"XXX --- Errore richiesta eliminazione: {e}")
        return False

#  GESTIONE ESERCIZI 

def get_exercise(user_email):
    
    try:
        response = requests.get(f"{API_URL}/get_exercises", params={"user_email": user_email})
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"XXX --- Errore recupero esercizi: {e}")
        return []
    
def get_all_exercises_full(user_email):
    
    try:
        response = requests.get(f"{API_URL}/get_exercises_full", params={"user_email": user_email})
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"XXX --- Errore full exercises: {e}")
        return []

def add_custom_exercise(nome_esercizio, user_email):
    
    def _req():
        try:
            payload = {"exercise_name": nome_esercizio, "user_email": user_email} 
            requests.post(f"{API_URL}/add_exercise", json=payload)
            print(f"---> Richiesta aggiunta esercizio '{nome_esercizio}' inviata. ---------------- user_email: ", user_email)
        except Exception as e:
            print(f"XXX --- Errore aggiunta esercizio: {e}")
    threading.Thread(target=_req).start()


def delete_exercise_api(ex_id, user_email, ex_name):

    def _req():
        try:
            payload = {
                "id": ex_id, 
                "user_email": user_email, 
                "exercise_name": ex_name
            }
            response = requests.post(f"{API_URL}/delete_exercise", json=payload)
            
            if response.status_code == 200:
                print(f"--> Esercizio {ex_name} eliminato con successo.")
            else:
                print(f"XXX --- ERRORE Backend ({response.status_code}): {response.text}")

        except Exception as e:
            print(f"XXX --- Errore richiesta eliminazione: {e}")
            
    t = threading.Thread(target=_req)
    t.start()
    t.join() 
    return True


# SCANSIONE AI

def analyze_workout_image(image_bytes):

    try:
        print("... Invio immagine al server backend...")
        files = {'file': ('image.jpg', image_bytes, 'image/jpeg')}
        
        response = requests.post(f"{API_URL}/analyze_image", files=files)
        
        if response.status_code == 200:
            print("--->  Analisi ricevuta dal server!")
            return response.json() 
        else:
            print(f"XXX --- Errore Server AI: {response.text}")
            return None
    except Exception as e:
        print(f"XXX --- Errore chiamata AI: {e}")
        return None
    

# AI GENERATIVA - COACH AI

def generate_workout_ai(user_prompt, user_email):

    try:
        print(f"------> Chiedo all'AI: {user_prompt}")
        payload = {"prompt": user_prompt, "user_email": user_email}
        
        # timeout alto
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

    def _req():
        try:
            requests.post(f"{API_URL}/save_new_user", json=user_data)
            print("--->  User_data inviata al backend con successo!")
        except Exception as e:
            print(f"XXX --- Errore invio dati utente: {e}")
    threading.Thread(target=_req).start()


def update_user(user_biometrics):
    
    def _req():
        try:
            response = requests.post(f"{API_URL}/update_user", json=user_biometrics)
            
            if response.status_code == 200:
                print("---> User_biometrics aggiornati con successo!")
            else:
                print(f"XXX --- Errore aggiornamento ({response.status_code}): {response.text}")
                
        except Exception as e:
            print(f"XXX --- Errore connessione update_user: {e}")
            
    threading.Thread(target=_req).start()

def get_user_data(oid):

    try:
        response = requests.get(f"{API_URL}/get_user_data", params={"oid": oid})
        
        if response.status_code == 200:
            data = response.json()
            print(f"---> Dati utente recuperati: Peso={data.get('peso')}, Altezza={data.get('altezza')}")
            return data
        else:
            print(f"XXX --- Impossibile recuperare dati utente ({response.status_code}): {response.text}")
            return None
    except Exception as e:
        print(f"XXX --- Errore connessione get_user_data: {e}")
        return None
    

#  GESTIONE LOG ALLENAMENTO 

def save_workout_log_blocking(log_data):

    try:
        print("... Attendo salvataggio allenamento...")
        response = requests.post(f"{API_URL}/save_workout_log", json=log_data)
        
        if response.status_code == 200:
            print("---> Allenamento salvato e confermato dal server!")
            return True
        else:
            print(f"XXX --- Errore API: {response.text}")
            return False
    except Exception as e:
        print(f"XXX --- Errore salvataggio bloccante: {e}")
        return False


def get_workout_logs(user_email):

    try:
        response = requests.get(f"{API_URL}/get_workout_logs", params={"user_email": user_email})
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"XXX --- Errore storico: {e}")
        return []