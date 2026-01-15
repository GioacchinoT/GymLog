import flet as ft

def dettaglio_view(page: ft.Page):
    # Recuperiamo i dati della scheda salvati nella memoria temporanea
    scheda = page.client_storage.get("scheda_selezionata")
    
    # Se per qualche motivo non ci sono dati, torniamo indietro
    if not scheda:
        page.go("/schede")
        return ft.View("/dettaglio", controls=[])

    # Estraiamo i dati principali
    titolo = scheda.get("nome_scheda", "Senza Titolo")
    split = scheda.get("split_type", "Nessun split specificato")
    data_creazione = scheda.get("created_at", "Sconosciuta")
    lista_esercizi = scheda.get("esercizi", [])
    
    # --- COSTRUZIONE LISTA ESERCIZI ---
    esercizi_controls = []
    
    if not lista_esercizi:
        esercizi_controls.append(ft.Text("Nessun esercizio in questa scheda.", color="grey", italic=True))
    else:
        for i, ex in enumerate(lista_esercizi):
            # Gestione nome (name vs nome)
            nome_ex = ex.get("exercise_name", ex.get("nome", "Esercizio"))
            serie = ex.get("serie", "?")
            reps = ex.get("ripetizioni", "?")
            note = ex.get("note_ai", "") # Eventuali note dell'AI
            
            # Riga esercizio
            row = ft.Container(
                content=ft.Row([
                    # Numero progressivo
                    ft.Container(
                        content=ft.Text(str(i+1), color="black", weight="bold"),
                        bgcolor=ft.Colors.BLUE_400, width=30, height=30, border_radius=15,
                        alignment=ft.alignment.center
                    ),
                    ft.Container(width=10),
                    # Dettagli
                    ft.Column([
                        ft.Text(nome_ex, size=16, weight="bold", color="white"),
                        ft.Text(f"{serie} Serie  x  {reps} Reps", color="#94a3b8", size=14),
                        # Se c'è una nota AI (es. "Riconosciuto da foto"), mostriamola piccola
                        ft.Text(f"Note: {note}", size=12, color="orange") if note else ft.Container()
                    ], expand=True),
                ]),
                padding=15,
                bgcolor="#1e293b", # Slate 800
                border_radius=12,
                border=ft.border.all(1, "#334155")
            )
            esercizi_controls.append(row)

    def go_edit(e):
        # Salviamo la scheda corrente nella "slot" di modifica
        page.client_storage.set("scheda_edit", scheda)
        page.go("/crea_scheda")

    # --- LAYOUT PAGINA ---
    return ft.View(
        "/dettaglio",
        bgcolor="#0f172a", # Slate 900
        padding=ft.padding.only(top=60, left=20, right=20, bottom=20),
        controls=[
            # Header con pulsante Indietro
            ft.Row([
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK_IOS, icon_color="white", on_click=lambda e: page.go("/schede")),
                ft.Text("Dettagli Scheda", size=20, weight="bold", color="white"),
            ]),
            
            # --- NUOVO BOTTONE MODIFICA ---
            ft.IconButton(
                ft.Icons.EDIT, 
                icon_color=ft.Colors.CYAN_400, 
                tooltip="Modifica Scheda",
                on_click=go_edit
            )
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            ft.Divider(color="transparent", height=10),
            
            # Card Intestazione (Titolo e Info)
            ft.Container(
                content=ft.Column([
                    ft.Text(titolo, size=24, weight="bold", color=ft.Colors.CYAN_400),
                    ft.Row([
                        ft.Icon(ft.Icons.CALENDAR_MONTH, size=16, color="grey"),
                        ft.Text(f"Creata il: {data_creazione}", color="grey", size=12),
                    ]),
                    ft.Row([
                        ft.Icon(ft.Icons.STYLE, size=16, color="grey"),
                        ft.Text(f"Tipo: {split}", color="grey", size=12),
                    ]),
                ]),
                padding=20,
                bgcolor="#1e293b",
                border_radius=15,
                border=ft.border.only(left=ft.border.BorderSide(5, ft.Colors.CYAN_400)) # Bordo colorato a sinistra
            ),
            
            ft.Divider(color="transparent", height=20),
            ft.Text(f"ESERCIZI ({len(lista_esercizi)})", size=14, weight="bold", color="#94a3b8"),
            ft.Container(height=10),
            
            # Lista scrollabile degli esercizi
            ft.Column(
                controls=esercizi_controls,
                scroll=ft.ScrollMode.AUTO,
                expand=True
            )
        ]
    )