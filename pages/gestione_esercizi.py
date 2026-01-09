import flet as ft
import time
import threading
# Assicurati che in azure_db.py tu abbia aggiornato delete_exercise_api per accettare 3 argomenti
from services.azure_db import get_all_exercises_full, add_custom_exercise, delete_exercise_api

def gestione_esercizi_view(page: ft.Page):
    user_email = page.client_storage.get("user_email")
    
    # Lista scrollabile che conterrà le card
    exercises_column = ft.Column(spacing=10)
    loading = ft.ProgressRing(color=ft.Colors.CYAN_400, visible=True)

    # --- FUNZIONI ---
    
    def load_data():
        exercises_column.controls.clear()
        loading.visible = True
        page.update()
        
        # Recupera dati dal backend
        # Nota: questa funzione deve restituire la lista di oggetti dict dal DB
        items = get_all_exercises_full(user_email)
        
        loading.visible = False
        
        if not items:
            exercises_column.controls.append(ft.Text("Nessun esercizio trovato.", color="grey"))
        else:
            for item in items:
                # --- FIX ROBUSTEZZA: Gestiamo sia Stringhe che Oggetti ---
                if isinstance(item, str):
                    # Se arriva una stringa (vecchio backend), non abbiamo l'ID
                    ex_name = item
                    ex_id = None 
                    owner = "system" # Assumiamo system se non sappiamo
                    is_mine = False 
                else:
                    # Se arriva un dizionario (nuovo backend), prendiamo tutto
                    ex_name = item.get("exercise_name", "???")
                    ex_id = item.get("id")
                    owner = item.get("user_email")
                    
                    # Posso cancellare solo se:
                    # 1. L'email proprietaria coincide con la mia
                    # 2. Ho un ID valido
                    is_mine = (owner == user_email) and (ex_id is not None)
                
                # Card Esercizio
                card = ft.Container(
                    content=ft.Row([
                        ft.Row([
                            ft.Icon(ft.Icons.FITNESS_CENTER, color="grey", size=16),
                            ft.Text(ex_name, color="white", size=16, weight="bold"),
                        ]),
                        
                        # Mostra cestino solo se è mio ED ho l'ID
                        ft.IconButton(
                            ft.Icons.DELETE_OUTLINE, 
                            icon_color="red", 
                            visible=is_mine,
                            tooltip="Elimina esercizio personale",
                            # FONDAMENTALE: Passiamo ID, Email proprietario e NOME (Partition Key)
                            on_click=lambda e, x=ex_id, y=owner, z=ex_name: delete_click(x, y, z)
                        ) if is_mine else ft.Icon(ft.Icons.LOCK, color="#334155", size=16, tooltip="Sistema / Non modificabile")
                        
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    bgcolor="#1e293b",
                    padding=15,
                    border_radius=10,
                    border=ft.border.all(1, "#334155")
                )
                exercises_column.controls.append(card)
        page.update()

    def delete_click(ex_id, owner_email, ex_name):
        if not ex_id: return
        
        # Chiama la funzione API passando tutti e 3 i parametri necessari per Cosmos DB
        # (ID per trovare l'item, Nome per la Partition Key)
        delete_exercise_api(ex_id, owner_email, ex_name) 
        
        page.open(ft.SnackBar(ft.Text("Richiesta eliminazione inviata..."), bgcolor="orange"))
        
        # Piccolo delay per dare tempo al server di processare e poi ricarichiamo
        time.sleep(0.5) 
        load_data()

    # --- DIALOG AGGIUNTA ---
    txt_new_name = ft.TextField(
        label="Nome Esercizio", 
        bgcolor="#1e293b", 
        border_color="#334155", 
        color="white"
    )

    def confirm_add(e):
        if not txt_new_name.value: return
        add_custom_exercise(txt_new_name.value, user_email)
        txt_new_name.value = ""
        page.close(dlg_add)
        page.open(ft.SnackBar(ft.Text("Esercizio aggiunto! Ricarica in corso..."), bgcolor="green"))
        
        time.sleep(1) 
        load_data()

    dlg_add = ft.AlertDialog(
        title=ft.Text("Nuovo Esercizio"),
        content=txt_new_name,
        actions=[
            ft.TextButton("Annulla", on_click=lambda e: page.close(dlg_add)),
            ft.ElevatedButton("Salva", on_click=confirm_add, bgcolor=ft.Colors.CYAN_600, color="white")
        ]
    )

    # --- UI LAYOUT ---
    view = ft.View(
        "/esercizi",
        bgcolor="#0f172a",
        padding=20,
        controls=[
            # Header
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK_IOS, icon_color="white", on_click=lambda e: page.go("/schede")),
                ft.Text("Gestione Esercizi", size=24, weight="bold", color="white")
            ]),
            
            ft.Divider(color="transparent", height=20),
            
            # Pulsante Aggiungi Grande
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.ADD_CIRCLE, color="white"),
                    ft.Text("Crea Nuovo Esercizio", color="white", weight="bold")
                ], alignment=ft.MainAxisAlignment.CENTER),
                bgcolor=ft.Colors.CYAN_700,
                padding=15,
                border_radius=10,
                on_click=lambda e: page.open(dlg_add)
            ),
            
            ft.Divider(color="transparent", height=20),
            loading,
            
            # Lista Esercizi
            ft.Container(
                content=exercises_column,
                expand=True, # Occupa tutto lo spazio rimanente
                # IMPORTANTE: scroll deve essere gestito qui o dentro la Column
            )
        ],
        scroll=ft.ScrollMode.AUTO
    )
    
    # Carica i dati appena la vista viene creata
    threading.Thread(target=load_data, daemon=True).start()
    
    return view