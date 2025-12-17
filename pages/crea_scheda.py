"""import flet as ft
import uuid
from datetime import datetime
# Assicurati che l'import punti alla cartella corretta (es. "database" o "azure")
from services.azure_db import save_workout_async

# --- SIMULAZIONE DATABASE ESERCIZI ---
ESERCIZI_DB = [
    "Panca Piana", "Squat", "Stacchi da Terra", 
    "Military Press", "Trazioni alla sbarra", "Rematore Bilanciere",
    "Curl Bicipiti", "Push Down Tricipiti", "Leg Extension"
]

def create_routine_view(page: ft.Page):
    current_user = page.client_storage.get("username") or "Utente"
    
    # --- STATO DELLA PAGINA ---
    exercises_buffer = [] 

    # --- COMPONENTI UI RIUTILIZZABILI ---
    def styled_textfield(label, hint_text):
        return ft.Column([
            ft.Text(label.upper(), size=12, weight=ft.FontWeight.BOLD, color="#94a3b8"),
            ft.TextField(
                hint_text=hint_text,
                border_radius=12,
                bgcolor="#1e293b",
                border_color="#334155",
                text_style=ft.TextStyle(color="white"),
                hint_style=ft.TextStyle(color="#64748b"),
                content_padding=15,
                cursor_color=ft.Colors.BLUE_400
            )
        ], spacing=5)

    # Input Principali
    txt_nome = styled_textfield("Nome Scheda", "Es. Ipertrofia Petto/Spalle")
    txt_split = styled_textfield("Tipo Split", "Es. Push, Pull, A, B...")
    
    # Label Contatore Esercizi
    lbl_esercizi_count = ft.Text("ESERCIZI (0)", size=12, weight=ft.FontWeight.BOLD, color="#94a3b8")
    
    # Contenitore della lista esercizi
    exercises_column = ft.Column(spacing=10)

    # --- LOGICA AGGIUNTA ESERCIZIO (DIALOG) ---
    dd_exist = ft.Dropdown(
        label="Seleziona Esistente",
        options=[ft.dropdown.Option(ex) for ex in ESERCIZI_DB],
        bgcolor="#1e293b", border_color="#334155", color="white",
        width=250
    )
    txt_new_custom = ft.TextField(label="Oppure nome nuovo...", bgcolor="#1e293b", border_color="#334155", color="white", visible=False, width=250)
    sw_custom = ft.Switch(label="Nuovo Esercizio Personalizzato", value=False, active_color=ft.Colors.BLUE_400)
    
    txt_sets = ft.TextField(label="Serie", width=100, bgcolor="#1e293b", border_color="#334155", color="white", value="3")
    txt_reps = ft.TextField(label="Reps", width=100, bgcolor="#1e293b", border_color="#334155", color="white", value="10")

    def toggle_custom_exercise(e):
        is_custom = sw_custom.value
        dd_exist.visible = not is_custom
        txt_new_custom.visible = is_custom
        dialog_add.update()

    def confirm_add_exercise(e):
        ex_name = txt_new_custom.value if sw_custom.value else dd_exist.value
        
        if not ex_name:
            page.open(ft.SnackBar(ft.Text("Inserisci o seleziona un nome!"), bgcolor="red"))
            return

        new_ex = {
            "id": str(uuid.uuid4())[:8],
            "nome": ex_name,
            "serie": txt_sets.value,
            "ripetizioni": txt_reps.value,
            "is_custom": sw_custom.value
        }
        
        exercises_buffer.append(new_ex)
        update_exercises_list()
        
        page.close(dialog_add)
        txt_new_custom.value = ""
        dd_exist.value = None
        sw_custom.value = False
        toggle_custom_exercise(None)

    dialog_add = ft.AlertDialog(
        modal=True,
        title=ft.Text("Aggiungi Esercizio"),
        bgcolor="#0f172a",
        content=ft.Column([
            sw_custom, dd_exist, txt_new_custom,
            ft.Row([txt_sets, txt_reps])
        ], height=200, tight=True),
        actions=[
            ft.TextButton("Annulla", on_click=lambda e: page.close(dialog_add)),
            ft.ElevatedButton("Aggiungi", on_click=confirm_add_exercise, bgcolor=ft.Colors.BLUE_600, color="white")
        ],
        on_dismiss=lambda e: toggle_custom_exercise(None)
    )
    sw_custom.on_change = toggle_custom_exercise

    # --- AGGIORNAMENTO LISTA ---
    def remove_exercise(ex_id):
        exercises_buffer[:] = [x for x in exercises_buffer if x['id'] != ex_id]
        update_exercises_list()

    def update_exercises_list():
        exercises_column.controls.clear()
        for ex in exercises_buffer:
            card = ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(ex['nome'], weight="bold", color="white", size=16),
                        ft.Text(f"{ex['serie']} x {ex['ripetizioni']}", color="#94a3b8", size=14)
                    ], expand=True),
                    ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color="red", on_click=lambda e, x=ex['id']: remove_exercise(x))
                ]),
                bgcolor="#1e293b",
                border_radius=10,
                padding=15,
                border=ft.border.all(1, "#334155")
            )
            exercises_column.controls.append(card)
        
        lbl_esercizi_count.value = f"ESERCIZI ({len(exercises_buffer)})"
        page.update()

    # --- SALVATAGGIO ---
    def save_scheda(e):
        title = txt_nome.controls[1].value
        split = txt_split.controls[1].value
        
        if not title:
            page.open(ft.SnackBar(ft.Text("Inserisci il nome della scheda!"), bgcolor="red"))
            return
            
        payload = {
            "id": str(uuid.uuid4()),
            "username": current_user,
            "type": "scheda",
            "nome_scheda": title,
            "split_type": split,
            "created_at": datetime.now().strftime("%Y-%m-%d"),
            "esercizi": exercises_buffer
        }
        
        save_workout_async(payload)
        page.open(ft.SnackBar(ft.Text("Scheda Salvata!"), bgcolor="green"))
        page.go("/schede")

    # --- NAVIGAZIONE ---
    def nav_change(e):
        idx = e.control.selected_index
        if idx == 0: page.go("/")
        elif idx == 1: page.go("/schede")
        elif idx == 2: page.go("/profilo")

    # Layout Bottone
    btn_add_big = ft.Container(
        content=ft.Row(
            [ft.Icon(ft.Icons.ADD, color=ft.Colors.BLUE_400), ft.Text("Aggiungi Esercizio", color=ft.Colors.BLUE_400, weight="bold")],
            alignment=ft.MainAxisAlignment.CENTER
        ),
        padding=15,
        border=ft.border.all(1, ft.Colors.BLUE_900),
        border_radius=12,
        on_click=lambda e: page.open(dialog_add)
    )

    # --- LAYOUT FINALE CON SCROLL ---
    return ft.View(
        "/crea_scheda",
        bgcolor="#0f172a",
        padding=20,
        controls=[
            # 1. HEADER FISSO (Resta sempre in alto)
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK_IOS, icon_color="white", on_click=lambda e: page.go("/schede"), icon_size=18),
                ft.Text("Nuova Scheda", size=20, weight="bold", color="white"),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Salva", 
                    bgcolor=ft.Colors.BLUE_500, 
                    color="white",
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=save_scheda
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            ft.Divider(color="transparent", height=10),
            
            # 2. AREA SCROLLABILE (Contiene tutto il resto e scrolla)
            ft.Column(
                controls=[
                    txt_nome,
                    ft.Container(height=10),
                    txt_split,
                    ft.Divider(color="transparent", height=20),
                    lbl_esercizi_count,
                    ft.Container(height=5),
                    exercises_column, # Lista dinamica
                    ft.Container(height=10),
                    btn_add_big,
                    ft.Container(height=20) # Spazio extra in fondo per comodità
                ],
                scroll=ft.ScrollMode.AUTO, # <--- ABILITA LO SCROLL
                expand=True                # <--- RIEMPI LO SPAZIO RIMANENTE
            )
        ],
        navigation_bar=ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Home"),
                ft.NavigationBarDestination(icon=ft.Icons.FITNESS_CENTER, label="Schede"),
                ft.NavigationBarDestination(icon=ft.Icons.PERSON, label="Profilo"),
            ],
            bgcolor="#1e293b",
            indicator_color=ft.Colors.BLUE_600,
            selected_index=1,
            on_change=nav_change
        )
    )"""


import flet as ft
import uuid
from datetime import datetime
# Importiamo le nuove funzioni
from services.azure_db import save_workout_async, get_all_exercises, add_custom_exercise_async

def create_routine_view(page: ft.Page):
    current_user = page.client_storage.get("username") or "Utente"
    
    # --- CARICAMENTO DATI DAL CLOUD ---
    # Carichiamo la lista reale all'avvio della pagina
    # Nota: get_all_exercises è bloccante qui, per ora va bene. 
    # In futuro potremmo usare un caricamento asincrono con spinner.
    lista_esercizi_db = get_all_exercises()
    
    # Se il DB è vuoto o offline, usiamo una lista di fallback per non rompere l'app
    if not lista_esercizi_db:
        lista_esercizi_db = ["LISTA ESERCIZI VUOTA"]

    exercises_buffer = [] 

    # --- COMPONENTI UI RIUTILIZZABILI ---
    def styled_textfield(label, hint_text):
        return ft.Column([
            ft.Text(label.upper(), size=12, weight=ft.FontWeight.BOLD, color="#94a3b8"),
            ft.TextField(
                hint_text=hint_text,
                border_radius=12,
                bgcolor="#1e293b",
                border_color="#334155",
                text_style=ft.TextStyle(color="white"),
                hint_style=ft.TextStyle(color="#64748b"),
                content_padding=15,
                cursor_color=ft.Colors.BLUE_400
            )
        ], spacing=5)

    txt_nome = styled_textfield("Nome Scheda", "Es. Ipertrofia Petto/Spalle")
    txt_split = styled_textfield("Tipo Split", "Es. Push, Pull, A, B...")
    lbl_esercizi_count = ft.Text("ESERCIZI (0)", size=12, weight=ft.FontWeight.BOLD, color="#94a3b8")
    exercises_column = ft.Column(spacing=10)

    # --- LOGICA AGGIUNTA ESERCIZIO ---
    
    # Dropdown popolato con la variabile caricata da Azure
    dd_exist = ft.Dropdown(
        label="Seleziona Esistente",
        options=[ft.dropdown.Option(ex) for ex in lista_esercizi_db], # <--- QUI USIAMO I DATI DI AZURE
        bgcolor="#1e293b", border_color="#334155", color="white",
        width=250
    )
    
    txt_new_custom = ft.TextField(label="Oppure nome nuovo...", bgcolor="#1e293b", border_color="#334155", color="white", visible=False, width=250)
    sw_custom = ft.Switch(label="Nuovo Esercizio Personalizzato", value=False, active_color=ft.Colors.BLUE_400)
    
    txt_sets = ft.TextField(label="Serie", width=100, bgcolor="#1e293b", border_color="#334155", color="white", value="3")
    txt_reps = ft.TextField(label="Reps", width=100, bgcolor="#1e293b", border_color="#334155", color="white", value="10")

    def toggle_custom_exercise(e):
        is_custom = sw_custom.value
        dd_exist.visible = not is_custom
        txt_new_custom.visible = is_custom
        dialog_add.update()

    def confirm_add_exercise(e):
        ex_name = txt_new_custom.value if sw_custom.value else dd_exist.value
        
        if not ex_name:
            page.open(ft.SnackBar(ft.Text("Inserisci o seleziona un nome!"), bgcolor="red"))
            return

        # SE È UN NUOVO ESERCIZIO CUSTOM -> SALVALO ANCHE NEL DB "WORKOUT"
        if sw_custom.value:
            add_custom_exercise_async(ex_name)
            # Opzionale: Aggiungiamolo subito alla lista locale del dropdown per non dover ricaricare
            dd_exist.options.append(ft.dropdown.Option(ex_name))

        new_ex = {
            "id": str(uuid.uuid4())[:8],
            "name": ex_name,
            "serie": txt_sets.value,
            "ripetizioni": txt_reps.value,
            "is_custom": sw_custom.value
        }
        
        exercises_buffer.append(new_ex)
        update_exercises_list()
        
        page.close(dialog_add)
        txt_new_custom.value = ""
        dd_exist.value = None
        sw_custom.value = False
        toggle_custom_exercise(None)

    # ... (Il resto del codice: dialog_add, update_exercises_list, save_scheda, layout UI rimane identico a prima) ...
    # Assicurati solo di copiare tutto il resto del file precedente per mantenere la UI.
    
    # (Inserisci qui il resto del codice UI che ti ho mandato nel messaggio precedente:
    # dialog_add definition, update_exercises_list, save_scheda, nav_change, return ft.View...)
    
    # PER COMPLETEZZA, ecco il blocco finale del return per assicurarci che tu abbia il file integro:
    dialog_add = ft.AlertDialog(
        modal=True,
        title=ft.Text("Aggiungi Esercizio"),
        bgcolor="#0f172a",
        content=ft.Column([
            sw_custom, dd_exist, txt_new_custom,
            ft.Row([txt_sets, txt_reps])
        ], height=200, tight=True),
        actions=[
            ft.TextButton("Annulla", on_click=lambda e: page.close(dialog_add)),
            ft.ElevatedButton("Aggiungi", on_click=confirm_add_exercise, bgcolor=ft.Colors.BLUE_600, color="white")
        ],
        on_dismiss=lambda e: toggle_custom_exercise(None)
    )
    sw_custom.on_change = toggle_custom_exercise

    def remove_exercise(ex_id):
        exercises_buffer[:] = [x for x in exercises_buffer if x['id'] != ex_id]
        update_exercises_list()

    def update_exercises_list():
        exercises_column.controls.clear()
        for ex in exercises_buffer:
            card = ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(ex['name'], weight="bold", color="white", size=16),
                        ft.Text(f"{ex['serie']} x {ex['ripetizioni']}", color="#94a3b8", size=14)
                    ], expand=True),
                    ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color="red", on_click=lambda e, x=ex['id']: remove_exercise(x))
                ]),
                bgcolor="#1e293b",
                border_radius=10,
                padding=15,
                border=ft.border.all(1, "#334155")
            )
            exercises_column.controls.append(card)
        lbl_esercizi_count.value = f"ESERCIZI ({len(exercises_buffer)})"
        page.update()

    def save_scheda(e):
        title = txt_nome.controls[1].value
        split = txt_split.controls[1].value
        if not title:
            page.open(ft.SnackBar(ft.Text("Inserisci il nome della scheda!"), bgcolor="red"))
            return
        payload = {
            "id": str(uuid.uuid4()),
            "username": current_user,
            "type": "scheda",
            "nome_scheda": title,
            "split_type": split,
            "created_at": datetime.now().strftime("%Y-%m-%d"),
            "esercizi": exercises_buffer
        }
        save_workout_async(payload)
        page.open(ft.SnackBar(ft.Text("Scheda Salvata!"), bgcolor="green"))
        page.go("/schede")

    def nav_change(e):
        idx = e.control.selected_index
        if idx == 0: page.go("/")
        elif idx == 1: page.go("/schede")
        elif idx == 2: page.go("/profilo")

    btn_add_big = ft.Container(
        content=ft.Row(
            [ft.Icon(ft.Icons.ADD, color=ft.Colors.BLUE_400), ft.Text("Aggiungi Esercizio", color=ft.Colors.BLUE_400, weight="bold")],
            alignment=ft.MainAxisAlignment.CENTER
        ),
        padding=15,
        border=ft.border.all(1, ft.Colors.BLUE_900),
        border_radius=12,
        on_click=lambda e: page.open(dialog_add)
    )

    return ft.View(
        "/crea_scheda",
        bgcolor="#0f172a",
        padding=20,
        controls=[
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK_IOS, icon_color="white", on_click=lambda e: page.go("/schede"), icon_size=18),
                ft.Text("Nuova Scheda", size=20, weight="bold", color="white"),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Salva", 
                    bgcolor=ft.Colors.BLUE_500, 
                    color="white",
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=save_scheda
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(color="transparent", height=10),
            ft.Column(
                controls=[
                    txt_nome, ft.Container(height=10),
                    txt_split, ft.Divider(color="transparent", height=20),
                    lbl_esercizi_count, ft.Container(height=5),
                    exercises_column, ft.Container(height=10),
                    btn_add_big, ft.Container(height=20)
                ],
                scroll=ft.ScrollMode.AUTO, expand=True
            )
        ],
        navigation_bar=ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Home"),
                ft.NavigationBarDestination(icon=ft.Icons.FITNESS_CENTER, label="Schede"),
                ft.NavigationBarDestination(icon=ft.Icons.PERSON, label="Profilo"),
            ],
            bgcolor="#1e293b",
            indicator_color=ft.Colors.BLUE_600,
            selected_index=1,
            on_change=nav_change
        )
    )