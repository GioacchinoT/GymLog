import uuid
from datetime import datetime

def parse_azure_result_to_json(azure_result, user_name):
    """
    Analizza il risultato JSON ricevuto dalla Azure Function.
    Adattato per lavorare con dizionari invece che oggetti SDK.
    """
    if not azure_result: return None

    esercizi_estratti = []
    
    # --- RECUPERO DATI DAL JSON (Dizionario) ---
    # Usiamo .get() perché ora sono dizionari, non oggetti
    tables = azure_result.get("tables", [])
    pages = azure_result.get("pages", [])

    # --- STRATEGIA 1: Cerca Tabelle ---
    if tables:
        # Prendiamo la prima tabella (è un dizionario)
        table = tables[0]
        cells = table.get("cells", []) # Lista di celle (dizionari)
        
        print(f"📊 Trovata tabella JSON con {len(cells)} celle!")
        
        # Raggruppiamo le celle per RIGA
        rows = {}
        for cell in cells:
            # Nota: qui usiamo ["key"] invece di .key
            r = cell.get("row_index")
            c = cell.get("column_index")
            content = cell.get("content", "")
            
            if r not in rows: rows[r] = {}
            rows[r][c] = content

        # Iteriamo sulle righe ricostruite
        for r_idx, cols in rows.items():
            col_nome = cols.get(0, "").strip()
            col_info = cols.get(1, "").strip()
            
            # FILTRO: Ignoriamo le intestazioni o righe vuote
            if not col_nome or "Esercizio" in col_nome or "Nome" in col_nome:
                continue

            # Pulizia del testo
            nome_pulito = col_nome.replace("\n", " ").replace(" :unselected:", "")
            info_pulita = col_info.replace("\n", " ").replace(" :unselected:", "")

            esercizi_estratti.append({
                "id": str(uuid.uuid4())[:8],
                "name": nome_pulito, 
                "serie": info_pulita, 
                "ripetizioni": "",
                "is_custom": True,
                "note_ai": "Tabella AI"
            })

    # --- STRATEGIA 2: Fallback Linea per Linea ---
    if not esercizi_estratti:
        print("⚠️ Nessuna tabella trovata, uso metodo righe JSON.")
        extracted_lines = []
        
        # Estraiamo le linee dal JSON strutturato
        for page in pages:
            lines_list = page.get("lines", [])
            for line_obj in lines_list:
                # line_obj è un dict {"content": "..."}
                extracted_lines.append(line_obj.get("content", ""))
        
        # Parsing semplice
        for line in extracted_lines:
            clean = line.strip()
            if len(clean) > 3:
                esercizi_estratti.append({
                    "id": str(uuid.uuid4())[:8],
                    "name": clean,
                    "serie": "?",
                    "ripetizioni": "?",
                    "is_custom": True,
                    "note_ai": "Riga AI"
                })

    # Se ancora vuoto, errore
    if not esercizi_estratti:
        return None

    # --- COSTRUZIONE OGGETTO SCHEDA ---
    titolo = "Scheda Scannerizzata"
    
    # Cerchiamo il titolo nella prima riga della prima pagina
    if pages:
        first_page_lines = pages[0].get("lines", [])
        if first_page_lines:
            first_line_content = first_page_lines[0].get("content", "")
            if len(first_line_content) > 3 and ("Scheda" in first_line_content or "Workout" in first_line_content):
                titolo = first_line_content

    scheda_json = {
        "id": str(uuid.uuid4()),
        "username": user_name,
        "type": "scheda",
        "nome_scheda": titolo,
        "split_type": "Smart Scan",
        "created_at": datetime.now().strftime("%Y-%m-%d"),
        "esercizi": esercizi_estratti,
        "ai_generated": True
    }
    
    return scheda_json