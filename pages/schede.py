import flet as ft
# Assicurati che l'import corrisponda alla tua cartella (database o azure)
from services.azure_db import get_workouts 

def schede_view(page: ft.Page):
    user_name = page.client_storage.get("username") or "Ospite"

    # --- 1. RECUPERO DATI (Logica Backend) ---
    schede_db = get_workouts(user_name)
    
    # Trasformiamo i dati grezzi del DB in oggetti per la grafica
    schede_esistenti = []
    if schede_db:
        for s in schede_db:
            esercizi_txt = [ex['name'] for ex in s.get("esercizi", [])]
            # Anteprima testo (es. "Squat, Panca...")
            descrizione = ", ".join(esercizi_txt) if esercizi_txt else "Nessun esercizio"
            count_str = f"{len(esercizi_txt)} Esercizi"

            schede_esistenti.append({
                "titolo": s.get("nome_scheda", "Senza Nome"),
                "tag": "Personalizzata",
                "count": count_str,
                "descrizione": descrizione
            })

    # --- 2. FUNZIONI NAVIGAZIONE ---
    def go_create(e):
        page.go("/crea_scheda") 

    def nav_change(e):
        index = e.control.selected_index
        if index == 0:
            page.go("/")
        elif index == 1:
            pass 
        elif index == 2:
            page.go("/profilo")

    # --- 3. ELEMENTI GRAFICI ---
    
    # Bottone Nuova Scheda (Tuo stile originale con GLOW)
    btn_nuova = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.ADD, size=40, color=ft.Colors.WHITE),
            ft.Text("Nuova Scheda", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        width=160,
        height=120,
        bgcolor=ft.Colors.CYAN_600,
        border_radius=15,
        shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.CYAN_900, offset=ft.Offset(0,0)), 
        on_click=go_create, 
        animate=ft.Animation(300, "easeOut")
    )

    # Bottone AI (Tuo stile originale)
    btn_ai = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.CAMERA_ALT, size=30, color=ft.Colors.PURPLE_300),
            ft.Text("Da Foto (AI)", weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_200)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        width=160,
        height=120,
        bgcolor="#1e293b", 
        border=ft.border.all(1, ft.Colors.PURPLE_900),
        border_radius=15,
        on_click=lambda e: page.open(ft.SnackBar(ft.Text("Funzione AI in arrivo!"))),
    )

    # Generazione Lista Card
    cards_widgets = []
    
    if not schede_esistenti:
        # Messaggio se vuoto
        cards_widgets.append(
            ft.Container(
                content=ft.Text("Non hai ancora schede salvate.", color="grey", italic=True),
                padding=ft.padding.only(bottom=20)
            )
        )
    else:
        for scheda in schede_esistenti:
            card = ft.Container(
                content=ft.Column([
                    # Riga Titolo e Cestino
                    ft.Row([
                        ft.Text(scheda["titolo"], size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.GREY_500, tooltip="Elimina")
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    
                    # Riga Tag
                    ft.Row([
                        ft.Container(
                            content=ft.Text(scheda["tag"], size=12, color=ft.Colors.BLUE_200),
                            bgcolor="#334155", padding=5, border_radius=5
                        ),
                        ft.Text(scheda["count"], size=12, color=ft.Colors.GREY_500)
                    ]),
                    
                    ft.Container(height=10),
                    # Lista esercizi (max 2 righe)
                    ft.Text(scheda["descrizione"], size=14, color=ft.Colors.BLUE_GREY_200, no_wrap=False, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS)
                ]),
                bgcolor="#1e293b", 
                border_radius=15,
                padding=20,
                margin=ft.margin.only(bottom=10)
            )
            cards_widgets.append(card)

    # --- 4. LAYOUT FINALE (HEADER FISSO + SCROLL) ---
    return ft.View(
        "/schede",
        bgcolor="#0f172a",
        padding=20, # Padding generale della pagina
        controls=[
            # A) HEADER FISSO
            ft.Container(
                content=ft.Text("Le tue Schede", size=30, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                margin=ft.margin.only(bottom=10) # Spazio sotto il titolo
            ),
            
            # B) AREA SCROLLABILE (Contiene lista + bottoni)
            ft.Column(
                controls=[
                    # Lista Cards (Spacchettata con *)
                    *cards_widgets,
                    
                    ft.Container(height=20),
                    
                    # Bottoni Azione (Scorrono insieme alle schede)
                    ft.Row([
                        btn_nuova,
                        ft.Container(width=10), 
                        btn_ai
                    ], alignment=ft.MainAxisAlignment.START),
                    
                    ft.Container(height=20) # Spazio extra in fondo per non tagliare l'ultimo elemento
                ],
                scroll=ft.ScrollMode.AUTO, # Abilita lo scroll solo per questa colonna
                expand=True                # Occupa tutto lo spazio rimanente sotto il titolo
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