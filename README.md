# Progetto sviluppato per il corso di Cloud Computing dell’Università degli Studi di Salerno.

# GymLog

**GymLog** è un’app cross-platform (Android/iOS) sviluppata in Python (Flet) per digitalizzare, gestire e monitorare i propri allenamenti in palestra, sfruttando un'architettura interamente Serverless e funzionalità di Intelligenza Artificiale Generativa.

Le funzionalità principali dell'app includono:

* **Smart Scan (OCR AI):** Tramite la fotocamera è possibile scansionare schede cartacee esistenti. Il sistema utilizza l'AI per riconoscere la struttura tabellare (griglie, righe, colonne) e convertire la foto in una scheda digitale modificabile.
* **AI Coach:** Un personal trainer virtuale basato su LLM. L'utente può descrivere i propri obiettivi (es. "Voglio aumentare la forza su panca piana") e l'AI genererà automaticamente una scheda di allenamento strutturata e pronta all'uso.
* **Live Tracking:** Logging in tempo reale di serie, ripetizioni e carichi durante l'esecuzione degli esercizi, con salvataggio immediato sul cloud.
* **Gestione Utente & Dashboard:** Login sicuro tramite account Microsoft e dashboard per il monitoraggio dei dati biometrici (Peso, Altezza, BMI, BMR).

## Servizi Utilizzati

Il backend e l'intelligenza dell'applicazione sono ospitati su Microsoft Azure:

* **Azure Function App** (Python V2 Model) con HTTP Trigger: funge da API Gateway e gestisce la logica di business.
* **Azure Cosmos DB (NoSQL):** utilizzato per la persistenza dei documenti JSON (Utenti, Schede, Log Allenamenti ed Esercizi) garantendo bassa latenza.
* **Azure AI Document Intelligence:** utilizzato con il modello `prebuilt-layout` per l'estrazione strutturata di dati dalle immagini delle schede cartacee.
* **Azure OpenAI:** utilizzato tramite **Microsoft Foundry** per orchestrare il modello **GPT-4o Mini**, ingegnerizzato per generare output JSON per le schede di allenamento.
* **Microsoft Entra ID:** gestisce l'autenticazione degli utenti tramite protocollo OAuth 2.0 (Device Code Flow) e libreria MSAL.
* **Azure Key Vault:** garantisce la sicurezza gestendo centralmente segreti e API Key (Zero secrets in code).
* **Azure Application Insights:** per il monitoraggio proattivo, logging distribuito e analisi delle performance.

## Architettura

L'applicazione segue un'architettura **Cloud-Native Serverless**. Il client Flet comunica esclusivamente tramite HTTPS con le Azure Functions, le quali interagiscono con i servizi gestiti (Database, AI, Vault) tramite Managed Identity.

---

## Guida all'utilizzo

### Backend Azure

#### Prerequisiti
* Una Azure Subscription attiva
* Azure CLI (`az`)
* Python 3.10+
* Azure Functions Core Tools v4 (`func`)

#### Setup e Avvio Locale
1.  Clonare il repository e spostarsi nella cartella `backend`.
    ```bash
    cd backend
    ```
2.  Creare un ambiente virtuale e installare le dipendenze.
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # Su Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    ```
3.  Configurare il file `local.settings.json` con l'URL del Key Vault (o le stringhe di connessione per test locale).
4.  Avviare il runtime delle funzioni.
    ```bash
    func start
    ```

### GymLog App (Client Flet)

L’app è stata sviluppata con il framework **Flet** (basato su Flutter) che permette di creare interfacce native partendo da codice Python. Può essere eseguita su Android, iOS, Web e Desktop.

#### Prerequisiti
* Python 3.10+
* Account Microsoft (per il login in-app)

#### Step

1.  Spostarsi nella cartella del client (root o `frontend` a seconda della struttura).
    ```bash
    cd frontend
    ```
2.  Installare le dipendenze del client.
    ```bash
    pip install flet requests msal
    ```
3.  Avviare l'applicazione in modalità desktop (per sviluppo rapido).
    ```bash
    flet run main.py
    ```
    *Oppure per avviare la versione web:*
    ```bash
    flet run main.py --web
    ```

#### Note per Android/iOS
Per compilare l'APK Android o il bundle iOS, Flet richiede l'installazione dell'SDK Flutter e l'uso del comando `flet build apk`. In fase di sviluppo è consigliato utilizzare l'app "Flet" disponibile sugli store scansionando il QR Code generato dalla CLI, oppure il test via desktop.
