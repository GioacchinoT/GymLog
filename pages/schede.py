import flet as ft
from services.azure_db import get_workouts, delete_workout, analyze_workout_image, save_workout_async
from services.ai_utils import parse_azure_result_to_json
import time

def schede_view(page: ft.Page):
    user_name = page.client_storage.get("username") or "Ospite"
    schede_db = get_workouts(user_name)
    
    # --- 1. SETUP AI & FILE PICKER (Invisibile ma necessario) ---
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

#--- funzione per caricamento scheda da foto

    def on_file_picked(e: ft.FilePickerResultEvent):
        if not e.files: return 
        page.dialog = loading_dialog
        loading_dialog.open = True
        page.update()
        
        try:
            with open(e.files[0].path, "rb") as f:
                res = analyze_workout_image(f.read())
            
            json_data = parse_azure_result_to_json(res, user_name)
            
            if json_data and json_data.get('esercizi'):
                save_workout_async(json_data)
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
        """Apre la pagina di dettaglio salvando i dati in memoria"""
        page.client_storage.set("scheda_selezionata", scheda_data)
        page.go("/dettaglio")

    def delete_click(e, w_id, card_ref):
        """Elimina la scheda e nasconde la card"""
        e.control.disabled = True # Evita doppi click accidentali
        page.update()
        
        success = delete_workout(w_id, user_name)
        if success:
            card_ref.visible = False
            page.update()
            page.open(ft.SnackBar(ft.Text("Scheda eliminata correttamente!"), bgcolor="green"))
        else:
            e.control.disabled = False # Riabilita se fallisce
            page.update()
            page.open(ft.SnackBar(ft.Text("Errore: Impossibile eliminare la scheda."), bgcolor="red"))

    # --- 3. NAVIGAZIONE ---
    def go_create(e): page.go("/crea_scheda") 
    def nav_change(e):
        index = e.control.selected_index
        if index == 0: page.go("/")
        elif index == 1: pass 
        elif index == 2: page.go("/profilo")

    # --- 4. ELEMENTI GRAFICI (DESIGN ORIGINALE RIPRISTINATO) ---
    
    # Bottone Nuova Scheda (CON GLOW AZZURRO E ANIMAZIONE)
    btn_nuova = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.ADD, size=40, color=ft.Colors.WHITE),
            ft.Text("Nuova Scheda", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        width=160,
        height=120,
        bgcolor=ft.Colors.CYAN_600,
        border_radius=15,
        # IL GLOW ORIGINALE:
        shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.CYAN_900, offset=ft.Offset(0,0)), 
        on_click=go_create, 
        animate=ft.Animation(300, "easeOut")
    )

    # Bottone AI (CON BORDO VIOLA E SFONDO SCURO)
    btn_ai = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.CAMERA_ALT, size=30, color=ft.Colors.PURPLE_300),
            ft.Text("Da Foto (AI)", weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_200)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        width=160,
        height=120,
        bgcolor="#1e293b", 
        border=ft.border.all(1, ft.Colors.PURPLE_900), # IL BORDO ORIGINALE
        border_radius=15,
        # AL CLICK APRE IL FILE PICKER
        on_click=lambda e: file_picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE),
    )

    # BOTTONE: GENERATORE AI
    btn_coach = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.AUTO_AWESOME, size=30, color=ft.Colors.PURPLE_300), # Icona scintille
            ft.Text("Coach AI", weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_200)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        width=160,
        height=120,
        bgcolor="#1e293b", 
        border=ft.border.all(1, ft.Colors.PURPLE_900), # Bordo Rosa
        border_radius=15,
        on_click=lambda e: page.go("/generatore"), # Vai alla nuova pagina
    )

    # Generazione Lista Card
    cards_widgets = []
    
    if not schede_db:
        cards_widgets.append(
            ft.Container(content=ft.Text("Non hai ancora schede salvate.", color="grey", italic=True), padding=ft.padding.only(bottom=20))
        )
    else:
        for scheda in schede_db: # Iteriamo direttamente sui dati DB
            # Calcoli dati
            esercizi_txt = []
            for ex in scheda.get("esercizi", []):
                nome_es = ex.get('name', ex.get('nome', 'Esercizio'))
                esercizi_txt.append(nome_es)

            descrizione = ", ".join(esercizi_txt) if esercizi_txt else "Nessun esercizio"
            count_str = f"{len(esercizi_txt)} Esercizi"
            w_id = scheda.get("id")
            
            # Stile Tag (Viola se AI, Blu se Manuale)
            is_ai = scheda.get("ai_generated", False)
            tag_text = "AI Scan/AI Generated" if is_ai else "Personalizzata"
            tag_color = ft.Colors.PURPLE_200 if is_ai else ft.Colors.BLUE_200

            # --- LA CARD (Container Cliccabile) ---
            card = ft.Container(
                bgcolor="#1e293b", # Slate 800
                border_radius=15,
                padding=20,
                margin=ft.margin.only(bottom=10),
                # RENDIAMO CLICCABILE TUTTA LA CARD PER APRIRE I DETTAGLI
                on_click=lambda e, s=scheda: open_detail(e, s),
                animate=ft.Animation(200, "easeOut") # Piccolo effetto visivo
            )

            # Contenuto Card
            card.content = ft.Column([
                # Riga Titolo e Cestino
                ft.Row([
                    ft.Text(scheda.get("nome_scheda", "Senza Nome"), size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    
                    # Tasto Elimina (Blocchiamo la propagazione gestendo l'evento qui)
                    ft.IconButton(
                        ft.Icons.DELETE_OUTLINE, 
                        icon_color=ft.Colors.RED_400, 
                        tooltip="Elimina Scheda",
                        on_click=lambda e, x=w_id, y=card: delete_click(e, x, y)
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                # Riga Tag e Contatore
                ft.Row([
                    ft.Container(
                        content=ft.Text(tag_text, size=12, color=tag_color),
                        bgcolor="#334155", padding=5, border_radius=5
                    ),
                    ft.Text(count_str, size=12, color=ft.Colors.GREY_500)
                ]),
                
                ft.Container(height=10),
                # Descrizione esercizi
                ft.Text(descrizione, size=14, color=ft.Colors.BLUE_GREY_200, no_wrap=False, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS)
            ])
            
            cards_widgets.append(card)

    # --- 5. LAYOUT FINALE (STRUTTURA FISSA + SCROLL) ---
    return ft.View(
        "/schede",
        bgcolor="#0f172a", 
        padding=20, 
        controls=[
            # HEADER FISSO
            ft.Container(
                content=ft.Text("Le tue Schede", size=30, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                margin=ft.margin.only(bottom=10) 
            ),
            
            # AREA SCROLLABILE
            ft.Column(
                controls=[
                    *cards_widgets,
                    
                    ft.Container(height=20),

                    ft.Row([
                        btn_nuova,
                        ft.Container(width=10), 
                        btn_ai,
                        ft.Container(width=10),
                        btn_coach # <--- Aggiunto qui
                    ], alignment=ft.MainAxisAlignment.START, scroll=ft.ScrollMode.AUTO), # Scroll se non entrano
                    
                    
                    ft.Container(height=20) 
                ],
                scroll=ft.ScrollMode.AUTO, 
                expand=True                
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