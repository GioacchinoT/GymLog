import flet as ft
import uuid
from datetime import datetime
from services.azure_db import save_workout_async, get_all_exercises, add_custom_exercise_async

def create_routine_view(page: ft.Page):
    current_user = page.client_storage.get("username") or "Utente"
    
    # --- 1. CONTROLLO MODIFICA ---
    # Vediamo se c'è una scheda in "memoria" da modificare
    scheda_da_modificare = page.client_storage.get("scheda_edit")
    
    # Se stiamo modificando, usiamo i suoi dati, altrimenti buffer vuoto
    is_editing = scheda_da_modificare is not None
    exercises_buffer = scheda_da_modificare.get("esercizi", []) if is_editing else []
    
    # Caricamento catalogo esercizi
    lista_esercizi_db = get_all_exercises()
    if not lista_esercizi_db: lista_esercizi_db = ["Esercizio Generico"]

    # --- UI COMPONENTS ---
    def styled_textfield(label, hint_text, initial_value=""):
        return ft.Column([
            ft.Text(label.upper(), size=12, weight=ft.FontWeight.BOLD, color="#94a3b8"),
            ft.TextField(
                value=initial_value, 
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

    # 2. PRE-COMPILAZIONE CAMPI
    init_nome = scheda_da_modificare.get("nome_scheda", "") if is_editing else ""
    init_split = scheda_da_modificare.get("split_type", "") if is_editing else ""

    txt_nome = styled_textfield("Nome Scheda", "Es. Giorno 1", init_nome)
    txt_split = styled_textfield("Tipo Split", "Es. Push, Pull, A, B...", init_split)
    
    lbl_esercizi_count = ft.Text(f"ESERCIZI ({len(exercises_buffer)})", size=12, weight="bold", color="#94a3b8")
    exercises_column = ft.Column(spacing=10)

    # ... (DIALOG E LOGICA AGGIUNTA ESERCIZIO ) ...
    dd_exist = ft.Dropdown(
        label="Seleziona Esistente",
        options=[ft.dropdown.Option(ex) for ex in lista_esercizi_db],
        bgcolor="#1e293b", border_color="#334155", color="white", width=250
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
            page.open(ft.SnackBar(ft.Text("Inserisci un nome!"), bgcolor="red"))
            return

        if sw_custom.value:
            add_custom_exercise_async(ex_name)
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

    dialog_add = ft.AlertDialog(
        modal=True, title=ft.Text("Aggiungi Esercizio"), bgcolor="#0f172a",
        content=ft.Column([sw_custom, dd_exist, txt_new_custom, ft.Row([txt_sets, txt_reps])], height=200, tight=True),
        actions=[ft.TextButton("Annulla", on_click=lambda e: page.close(dialog_add)), ft.ElevatedButton("Aggiungi", on_click=confirm_add_exercise, bgcolor=ft.Colors.BLUE_600, color="white")],
        on_dismiss=lambda e: toggle_custom_exercise(None)
    )
    sw_custom.on_change = toggle_custom_exercise

    def remove_exercise(ex_id):
        exercises_buffer[:] = [x for x in exercises_buffer if x.get('id') != ex_id]
        update_exercises_list()

    def update_exercises_list():
        exercises_column.controls.clear()
        for ex in exercises_buffer:
            nome = ex.get('name', ex.get('nome', '???'))
            card = ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(nome, weight="bold", color="white", size=16),
                        ft.Text(f"{ex.get('serie','?')} x {ex.get('ripetizioni','?')}", color="#94a3b8", size=14)
                    ], expand=True),
                    ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color="red", on_click=lambda e, x=ex.get('id'): remove_exercise(x))
                ]),
                bgcolor="#1e293b", border_radius=10, padding=15, border=ft.border.all(1, "#334155")
            )
            exercises_column.controls.append(card)
        lbl_esercizi_count.value = f"ESERCIZI ({len(exercises_buffer)})"
        page.update()

    # --- 3. SALVATAGGIO LOGICO (Insert o Update) ---
    def save_scheda(e):
        title = txt_nome.controls[1].value
        split = txt_split.controls[1].value
        if not title:
            page.open(ft.SnackBar(ft.Text("Inserisci il nome!"), bgcolor="red"))
            return
            
        payload = {
            # Se editiamo, manteniamo l'ID vecchio. Se nuova, ID nuovo.
            "id": scheda_da_modificare['id'] if is_editing else str(uuid.uuid4()),
            "username": current_user,
            "type": "scheda",
            "nome_scheda": title,
            "split_type": split,
            "created_at": scheda_da_modificare['created_at'] if is_editing else datetime.now().strftime("%Y-%m-%d"),
            "esercizi": exercises_buffer
        }
        
        save_workout_async(payload)
        
        # Pulizia della memoria di edit
        page.client_storage.remove("scheda_edit")
        
        page.open(ft.SnackBar(ft.Text("Scheda Salvata/Aggiornata!"), bgcolor="green"))
        page.go("/schede")

    # Funzione per tornare indietro
    def go_back(e):
        # Importante: pulire la memoria se l'utente annulla la modifica
        page.client_storage.remove("scheda_edit")
        page.go("/schede")

    # --- INIZIALIZZAZIONE ---
    # Se stiamo editando, popoliamo la lista esercizi visiva subito
    if is_editing: update_exercises_list()

    btn_add_big = ft.Container(
        content=ft.Row([ft.Icon(ft.Icons.ADD, color=ft.Colors.BLUE_400), ft.Text("Aggiungi Esercizio", color=ft.Colors.BLUE_400, weight="bold")], alignment=ft.MainAxisAlignment.CENTER),
        padding=15, border=ft.border.all(1, ft.Colors.BLUE_900), border_radius=12,
        on_click=lambda e: page.open(dialog_add)
    )

    page_title_text = "Modifica Scheda" if is_editing else "Nuova Scheda"

    return ft.View(
        "/crea_scheda",
        bgcolor="#0f172a", padding=20,
        controls=[
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK_IOS, icon_color="white", on_click=go_back, icon_size=18),
                ft.Text(page_title_text, size=20, weight="bold", color="white"),
                ft.Container(expand=True),
                ft.ElevatedButton("Salva", bgcolor=ft.Colors.BLUE_500, color="white", on_click=save_scheda)
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
        # ... Navigation bar ...
        navigation_bar=ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Home"),
                ft.NavigationBarDestination(icon=ft.Icons.FITNESS_CENTER, label="Schede"),
                ft.NavigationBarDestination(icon=ft.Icons.PERSON, label="Profilo"),
            ],
            bgcolor="#1e293b", indicator_color=ft.Colors.BLUE_600, selected_index=1,
            on_change=lambda e: [page.client_storage.remove("scheda_edit"), page.go("/") if e.control.selected_index==0 else None]
        )
    )