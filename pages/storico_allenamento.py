import flet as ft
import threading
from services.azure_db import get_schede, get_workout_logs

def workout_view(page: ft.Page):
    user_email = page.client_storage.get("user_email")
    
    # --- 1. SETUP LISTA STORICO ---
    # Usiamo ListView per garantire lo scroll fluido
    # Padding bottom alto per evitare che l'ultimo elemento finisca sotto il tasto "INIZIA"
    history_column = ft.ListView(
        spacing=10, 
        expand=True, 
        padding=ft.padding.only(left=0, top=0, right=10, bottom=100)
    )
    
    loading_history = ft.ProgressRing(color=ft.Colors.CYAN_400)
    
    # --- 2. FUNZIONE NAVIGAZIONE DETTAGLIO (Nuova Logica) ---
    def open_detail_page(e, log_data):
        # Salviamo i dati e andiamo alla pagina di dettaglio
        page.client_storage.set("allenamento_selezionato", log_data)
        page.go("/dettaglio_allenamento")

    # --- 3. CARICAMENTO DATI STORICO (Background) ---
    def load_history():
        logs = get_workout_logs(user_email)
        history_column.controls.clear()
        
        if not logs:
            history_column.controls.append(
                ft.Container(
                    content=ft.Text("Nessun allenamento completato.", color="grey", italic=True),
                    alignment=ft.alignment.center,
                    padding=20
                )
            )
        else:
            for log in logs:
                # Dati per la card
                nome = log.get("nome_scheda", "Allenamento")
                data = log.get("data", "Senza data")
                durata = log.get("durata", "--")
                
                # Card Cliccabile
                card = ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(nome, weight="bold", color="white", size=16),
                            ft.Row([
                                ft.Icon(ft.Icons.CALENDAR_TODAY, size=12, color="grey"),
                                ft.Text(data, color="grey", size=12)
                            ], spacing=5)
                        ], expand=True),
                        
                        ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.TIMER, size=12, color="grey"), 
                                ft.Text(durata, color="grey", size=12)
                            ]),
                            ft.Text("Vedi dettagli >", color=ft.Colors.CYAN_400, size=11, weight="bold")
                        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.END)
                    ]),
                    bgcolor="#1e293b",
                    padding=15,
                    border_radius=10,
                    border=ft.border.all(1, "#334155"),
                    # AL CLICK: Apre la pagina di dettaglio
                    on_click=lambda e, x=log: open_detail_page(e, x),
                    ink=True
                )
                history_column.controls.append(card)
        
        loading_history.visible = False
        page.update()

    threading.Thread(target=load_history, daemon=True).start()

    # --- 4. LOGICA TASTO "INIZIA" (Vecchio Codice) ---
    def start_workout(scheda):
        page.client_storage.set("workout_active_scheda", scheda)
        page.close(bs_schede)
        page.go("/live_workout")

    bs_schede_content = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=10)
    
    bs_schede = ft.BottomSheet(
        ft.Container(
            content=bs_schede_content,
            padding=20,
            bgcolor="#1e293b",
            border_radius=ft.border_radius.only(top_left=20, top_right=20),
            height=500 
        )
    )

    def open_start_dialog(e):
        # Carichiamo le schede disponibili al volo
        schede = get_schede(user_email)
        bs_schede_content.controls.clear()
        
        bs_schede_content.controls.append(
            ft.Container(
                content=ft.Text("Scegli la scheda", size=20, weight="bold", color="white"),
                padding=ft.padding.only(bottom=10)
            )
        )
        
        if not schede:
            bs_schede_content.controls.append(ft.Text("Nessuna scheda trovata. Creane una prima!", color="red"))
        else:
            for s in schede:
                tile = ft.ListTile(
                    leading=ft.Icon(ft.Icons.FITNESS_CENTER, color=ft.Colors.CYAN_400),
                    title=ft.Text(s.get("nome_scheda"), color="white", weight="bold"),
                    subtitle=ft.Text(f"{len(s.get('esercizi', []))} Esercizi", color="grey"),
                    on_click=lambda e, x=s: start_workout(x),
                    bgcolor="#0f172a",
                    shape=ft.RoundedRectangleBorder(radius=10),
                )
                bs_schede_content.controls.append(tile)
        
        page.open(bs_schede)
        page.update()

    # --- 5. NAVIGAZIONE ---
    def nav_change(e):
        index = e.control.selected_index
        if index == 0: page.go("/schede")
        elif index == 1: page.go("/")
        elif index == 2: pass 

    # --- 6. VIEW FINALE ---
    return ft.View(
        "/workout",
        bgcolor="#0f172a",
        padding=ft.padding.only(top=60, left=0, right=0, bottom=0), 
        controls=[
            ft.Container(
                padding=20,
                expand=True,
                content=ft.Column([
                    ft.Text("Storico Allenamenti", size=28, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Divider(color="transparent", height=10),
                    
                    # Area caricamento
                    ft.Row([loading_history], alignment=ft.MainAxisAlignment.CENTER),
                    
                    # Lista Storico
                    history_column
                ], expand=True) 
            )
        ],
        # IL TASTO FLUTTUANTE "INIZIA"
        floating_action_button=ft.FloatingActionButton(
            icon=ft.Icons.PLAY_ARROW,
            text="INIZIA",
            bgcolor=ft.Colors.CYAN_600,
            content=ft.Row([ft.Icon(ft.Icons.PLAY_ARROW), ft.Text("INIZIA", weight="bold")], alignment=ft.MainAxisAlignment.CENTER),
            width=120,
            on_click=open_start_dialog
        ),
        floating_action_button_location=ft.FloatingActionButtonLocation.CENTER_FLOAT,
        navigation_bar=ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.FOLDER_COPY, label="Schede"),
                ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Home"),
                ft.NavigationBarDestination(icon=ft.Icons.SPORTS_GYMNASTICS, label="Allenamento"),
            ],
            bgcolor="#1e293b",
            indicator_color=ft.Colors.BLUE_600,
            selected_index=2,
            on_change=nav_change
        )
    )