import uuid
from datetime import datetime

def parse_azure_result_to_json(azure_result, user_email):
    
    # analizza il risultato JSON ricevuto dalla Azure function

    if not azure_result: return None

    esercizi_estratti = []
    
    #  RECUPERO DATI DAL JSON
    tables = azure_result.get("tables", [])
    pages = azure_result.get("pages", [])

    # RICERCA TABELLE
    if tables:

        table = tables[0]
        cells = table.get("cells", []) 
        
        print(f"--> Trovata tabella JSON con {len(cells)} celle!")
        
        # raggruppamento celle per riga
        rows = {}
        for cell in cells:
            r = cell.get("row_index")
            c = cell.get("column_index")
            content = cell.get("content", "")
            
            if r not in rows: rows[r] = {}
            rows[r][c] = content

        for r_idx, cols in rows.items():
            col_nome = cols.get(0, "").strip()
            col_info = cols.get(1, "").strip()
            
            # filtraggio valori vuoti
            if not col_nome or "Esercizio" in col_nome or "Nome" in col_nome:
                continue

            # pulizia del testo
            nome_pulito = col_nome.replace("\n", " ").replace(" :unselected:", "")
            info_pulita = col_info.replace("\n", " ").replace(" :unselected:", "")

            esercizi_estratti.append({
                "id": str(uuid.uuid4())[:8],
                "exercise_name": nome_pulito, 
                "serie": info_pulita, 
                "ripetizioni": "",
                "is_custom": True,
                "note_ai": "Scanner AI"
            })

    # utilizzo di righe se non viene trovata la tabella
    if not esercizi_estratti:
        print("--> Nessuna tabella trovata, uso metodo righe JSON.")
        extracted_lines = []
        
        # estrazione linee JSON
        for page in pages:
            lines_list = page.get("lines", [])
            for line_obj in lines_list:
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

    # se è ancora vuoto, allora errore
    if not esercizi_estratti:
        return None

    # costruzione oggetto scheda
    titolo = "Scheda Scannerizzata"
    
    # ricerca titolo nella prima riga della prima pagina
    if pages:
        first_page_lines = pages[0].get("lines", [])
        if first_page_lines:
            first_line_content = first_page_lines[0].get("content", "")
            if len(first_line_content) > 3 and ("Scheda" in first_line_content or "Workout" in first_line_content):
                titolo = first_line_content

    scheda_json = {
        "id": str(uuid.uuid4()),
        "user_email": user_email,
        "type": "scheda",
        "nome_scheda": titolo,
        "split_type": "Smart Scan",
        "created_at": datetime.now().strftime("%Y-%m-%d"),
        "esercizi": esercizi_estratti,
        "ai_generated": True
    }
    
    return scheda_json