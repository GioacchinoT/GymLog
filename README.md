# Progetto sviluppato per il corso di Cloud Computing dell’Università degli Studi di Salerno.

# GymLog

**GymLog** è un’app cross-platform (Android/iOS) sviluppata in Python (Flet) per digitalizzare, gestire e monitorare i propri allenamenti in palestra, sfruttando un'architettura interamente Serverless e funzionalità di Intelligenza Artificiale Generativa.

Le funzionalità principali dell'app includono:

* **Smart Scan (OCR AI):** Tramite la fotocamera è possibile scansionare schede cartacee esistenti. Il sistema utilizza l'AI per riconoscere la struttura tabellare (griglie, righe, colonne) e convertire la foto in una scheda digitale modificabile.
* **AI Coach:** Un personal trainer virtuale basato su LLM. L'utente può descrivere i propri obiettivi (es. "Voglio aumentare la forza su panca piana") e l'AI genererà automaticamente una scheda di allenamento strutturata e pronta all'uso.
* **Live Tracking:** Logging in tempo reale di serie, ripetizioni e carichi durante l'esecuzione degli esercizi, con salvataggio immediato sul cloud.
* **Gestione Utente & Dashboard:** Login sicuro tramite account Microsoft e dashboard per il monitoraggio dei dati biometrici (Peso, Altezza, BMI, BMR).

## Servizi Utilizzati

Il backend è interamente ospitato su Microsoft Azure:

* **Azure Function App** (Python V2 Model) con HTTP Trigger: funge da API Gateway e gestisce la logica di business.
* **Azure Cosmos DB (NoSQL):** utilizzato per la persistenza dei documenti JSON (Utenti, Schede, Log Allenamenti ed Esercizi)
* **Azure AI Document Intelligence:** utilizzato con il modello `prebuilt-layout` per l'estrazione strutturata di dati dalle immagini delle schede cartacee.
* **Azure AI Foundry:**  modello **GPT-4o Mini** con prompt ingegnerizzato per generare output JSON per le schede di allenamento.
* **Microsoft Entra ID:** gestisce l'autenticazione degli utenti tramite protocollo OAuth 2.0 (Device Code Flow) e libreria MSAL.
* **Azure Key Vault:** garantisce la sicurezza gestendo centralmente segreti, API Key ed Endpoint.
* **Azure Application Insights:** per il monitoraggio, logging distribuito e analisi delle performance.



## Guida all'utilizzo

### Backend Azure

### Prerequisiti
* Azure Subscription attiva
* Azure CLI (`az`)
* Python 3.10+
* Azure Functions Core Tools v4 (`func`)

### GymLog App (Client Flet)

L’app è stata sviluppata con il framework **Flet**  (v0.25.0 basato su Flutter) che permette di creare interfacce native partendo da codice Python. Può essere eseguita su Android, Web e Desktop.

#### Prerequisiti
* Python 3.10+
* Account Microsoft (per il login in-app)

#### Esecuzione
Per avviare l'applicazione tramite emulatore built-in di Flet basta eseguire il main.py
```bash
    python main.py
    ```

Per compilare l'APK Android Flet richiede l'installazione dell'SDK Flutter e l'uso del comando `flet build apk`.
