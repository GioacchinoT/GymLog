import flet as ft
from services.azure_db import get_schede, delete_scheda, analyze_workout_image, save_scheda
from services.ai_utils import parse_azure_result_to_json
import time
import threading 

def schede_view(page: ft.Page):
    user_email = page.client_storage.get("user_email") 
    
    # --- CONTENITORI DATI ---
    cards_column = ft.Column(spacing=0) 
    
    loading_widget = ft.Row([
        ft.ProgressRing(color=ft.Colors.CYAN_400),
    ], alignment=ft.MainAxisAlignment.CENTER, visible=True)

    # --- 1. SETUP AI & FILE PICKER ---
    file_picker = ft.FilePicker()
    page.overlay.append(file_picker) 
    
    loading_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Elaborazione AI in corso..."),
        content=ft.Column([
            ft.ProgressRing(),
            ft.Text("Sto analizzando la foto con Azure, un attimo di pazienza."),
        ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER, height=100),
    )

    def on_file_picked(e: ft.FilePickerResultEvent):
        if not e.files: return 
        page.dialog = loading_dialog
        loading_dialog.open = True
        page.update()
        
        try:
            with open(e.files[0].path, "rb") as f:
                res = analyze_workout_image(f.read())
            
            json_data = parse_azure_result_to_json(res, user_email)
            
            if json_data and json_data.get('esercizi'):
                save_scheda(json_data)
                time.sleep(1.5) 
                loading_dialog.open = False
                page.open(ft.SnackBar(ft.Text("Scheda digitalizzata con successo!"), bgcolor="green"))
                page.go("/") 
                page.go("/schede")
            else:
                raise Exception("Non sono riuscito a leggere dati utili dalla foto.")
                
        except Exception as ex:
            loading_dialog.open = False
            page.open(ft.SnackBar(ft.Text(f"Errore: {str(ex)}"), bgcolor="red"))
            page.update()

    file_picker.on_result = on_file_picked

    # --- 2. FUNZIONI DI AZIONE ---
    def open_detail(e, scheda_data):
        page.client_storage.set("scheda_selezionata", scheda_data)
        page.go("/dettaglio")

    def delete_click(e, w_id, card_ref):
        e.control.disabled = True 
        page.update()
        
        success = delete_scheda(w_id, user_email)
        if success:
            card_ref.visible = False
            page.update()
            page.open(ft.SnackBar(ft.Text("Scheda eliminata correttamente!"), bgcolor="green"))
        else:
            e.control.disabled = False 
            page.update()
            page.open(ft.SnackBar(ft.Text("Errore: Impossibile eliminare la scheda."), bgcolor="red"))

    # --- 3. NAVIGAZIONE ---
    def go_create(e): page.go("/crea_scheda") 

    # --- 4. ELEMENTI GRAFICI (PULSANTI ORIGINALI) ---
    # Ripristinati esattamente come nel tuo file originale e nello screenshot
    
    btn_nuova = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.ADD, size=40, color=ft.Colors.WHITE),
            ft.Text("Nuova Scheda", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        width=160, height=120, 
        bgcolor=ft.Colors.CYAN_600, 
        border_radius=15,
        shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.CYAN_900, offset=ft.Offset(0,0)), 
        on_click=go_create, 
        animate=ft.Animation(300, "easeOut")
    )

    btn_ai = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.CAMERA_ALT, size=30, color=ft.Colors.PURPLE_300),
            ft.Text("Da Foto (AI)", weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_200)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        width=160, height=120, 
        bgcolor="#1e293b", 
        border=ft.border.all(1, ft.Colors.PURPLE_900), 
        border_radius=15,
        on_click=lambda e: file_picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE),
    )

    btn_coach = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.AUTO_AWESOME, size=30, color=ft.Colors.PURPLE_300),
            ft.Text("Coach AI", weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_200)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        width=160, height=120, 
        bgcolor="#1e293b", 
        border=ft.border.all(1, ft.Colors.PURPLE_900),
        border_radius=15,
        on_click=lambda e: page.go("/generatore"),
    )

    # --- NUOVO BOTTONE GESTISCI ESERCIZI ---
    btn_gestisci = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.LIST_ALT, size=30, color=ft.Colors.CYAN_600),
            ft.Text("Gestisci", weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_600),
            ft.Text("Esercizi", weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_600)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
        width=160, height=120, 
        bgcolor="#1e293b", 
        border=ft.border.all(1, ft.Colors.CYAN_900),
        border_radius=15,
        on_click=lambda e: page.go("/esercizi"),
    )

    # Container dei pulsanti (FISSO IN ALTO)
    # ScrollMode.HIDDEN o AUTO permette di scrollare orizzontalmente su schermi piccoli
    # ma mantiene le dimensioni fisse dei bottoni.
    actions_row = ft.Row(
        [
            btn_nuova,
            ft.Container(width=10), # Spaziatore manuale come nell'originale
            btn_ai,
            ft.Container(width=10),
            btn_coach,
            ft.Container(width=10),
            btn_gestisci 
        ], 
        alignment=ft.MainAxisAlignment.START, 
        scroll=ft.ScrollMode.AUTO 
    )

    # --- LOGICA GENERAZIONE CARD IN BACKGROUND ---
    def background_loader():
        schede_db = get_schede(user_email)
        new_controls = []
        
        if not schede_db:
            new_controls.append(
                ft.Container(content=ft.Text("Non hai ancora schede salvate.", color="grey", italic=True), padding=ft.padding.only(bottom=20))
            )
        else:
            for scheda in schede_db:
                esercizi_txt = []
                for ex in scheda.get("esercizi", []):
                    nome_es = ex.get('exercise_name', ex.get('nome', 'Esercizio'))
                    esercizi_txt.append(nome_es)

                descrizione = ", ".join(esercizi_txt) if esercizi_txt else "Nessun esercizio"
                count_str = f"{len(esercizi_txt)} Esercizi"
                w_id = scheda.get("id")
                
                is_ai = scheda.get("ai_generated", False)
                tag_text = "AI Scan/AI Generated" if is_ai else "Personalizzata"
                tag_color = ft.Colors.PURPLE_200 if is_ai else ft.Colors.BLUE_200

                card = ft.Container(
                    bgcolor="#1e293b", 
                    border_radius=15,
                    padding=20,
                    margin=ft.margin.only(bottom=10),
                    on_click=lambda e, s=scheda: open_detail(e, s),
                    animate=ft.Animation(200, "easeOut")
                )

                card.content = ft.Column([
                    ft.Row([
                        ft.Text(scheda.get("nome_scheda", "Senza Nome"), size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.IconButton(
                            ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED_400, tooltip="Elimina Scheda",
                            on_click=lambda e, x=w_id, y=card: delete_click(e, x, y)
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([
                        ft.Container(content=ft.Text(tag_text, size=12, color=tag_color), bgcolor="#334155", padding=5, border_radius=5),
                        ft.Text(count_str, size=12, color=ft.Colors.GREY_500)
                    ]),
                    ft.Container(height=10),
                    ft.Text(descrizione, size=14, color=ft.Colors.BLUE_GREY_200, no_wrap=False, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS)
                ])
                new_controls.append(card)

        cards_column.controls.extend(new_controls) 
        loading_widget.visible = False 
        page.update()

    threading.Thread(target=background_loader, daemon=True).start()

    # --- NAVIGAZIONE ---
    def nav_change(e):
        index = e.control.selected_index
        if index == 0: pass
        elif index == 1: page.go("/")
        elif index == 2: page.go("/workout")

    # --- 5. LAYOUT FINALE ---
    return ft.View(
        "/schede",
        bgcolor="#0f172a", 
        padding=ft.padding.only(top=60, left=20, right=20, bottom=20), 
        controls=[
            # 1. HEADER FISSO (Titolo + Pulsanti)
            # Questo Container NON ha expand, quindi occupa solo lo spazio che gli serve e resta in alto
            ft.Column([
                ft.Container(
                    content=ft.Text("Le tue Schede", size=30, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    margin=ft.margin.only(bottom=20) 
                ),
                actions_row, # I pulsanti sono qui, fissi
                ft.Divider(color="transparent", height=20),
            ], spacing=0),
            
            # 2. LISTA SCORREVOLE
            # Questo Container ha expand=True, quindi riempie tutto il resto dello schermo
            # e abilita lo scroll al suo interno.
            ft.Container(
                content=ft.Column(
                    controls=[
                        loading_widget,
                        cards_column, # Le schede verranno caricate qui
                        ft.Container(height=50) # Spazio extra in fondo per scroll comodo
                    ],
                    scroll=ft.ScrollMode.AUTO, # SCROLL ATTIVO SOLO QUI
                ),
                expand=True # FONDAMENTALE: spinge la lista a occupare lo spazio rimanente
            )
        ],
        navigation_bar=ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.FOLDER_COPY, label="Schede"),
                ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Home"),
                ft.NavigationBarDestination(icon=ft.Icons.SPORTS_GYMNASTICS, label="Allenamento"),
            ],
            bgcolor="#1e293b",
            indicator_color=ft.Colors.BLUE_600,
            selected_index=0,
            on_change=nav_change
        )
    )