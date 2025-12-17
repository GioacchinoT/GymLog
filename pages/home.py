import flet as ft
# Assicurati che questo file esista, altrimenti commenta l'import e la riga save_water_async
from services.azure_db import save_water_async 

def home_view(page: ft.Page):
    # Recuperiamo il nome salvato
    user_name = page.client_storage.get("username") or "Ospite"
    
    # Variabile di stato per il contatore
    water_counter = ft.Text(value="0", size=40, weight=ft.FontWeight.BOLD, color="white")

    # --- LOGICA ACQUA ---
    def add_water(e):
        current = int(water_counter.value)
        new_val = current + 250
        water_counter.value = str(new_val)
        page.update()
        # Se non hai ancora il file azure_db configurato, commenta la riga sotto
        save_water_async(user_name, new_val) 
    
    def logout(e):
        page.client_storage.remove("username")
        page.go("/welcome")

    # --- LOGICA NAVIGAZIONE ---
    def nav_change(e):
        index = e.control.selected_index
        if index == 0:
            page.go("/")
        elif index == 1:
            page.go("/schede") # <--- ORA FUNZIONA
        elif index == 2:
            page.go("/profilo") 

    # --- Helper Card ---
    def stat_card(title, val, sub, icon, col):
        return ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(icon, color=col, size=20), ft.Text(title, color=col, weight=ft.FontWeight.BOLD)]),
                ft.Text(val, size=24, weight=ft.FontWeight.BOLD, color="white"),
                ft.Text(sub, size=12, color="#94a3b8")
            ]),
            bgcolor="#1e293b", border_radius=15, padding=20, expand=True
        )

    return ft.View(
        "/",
        controls=[
            # Header
            ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(f"Ciao, {user_name} 👋", size=28, weight=ft.FontWeight.BOLD, color="white"),
                        ft.Text("Pronto a superare i tuoi limiti?", color="#94a3b8"),
                    ]),
                    ft.IconButton(ft.Icons.LOGOUT, icon_color="red", on_click=logout, tooltip="Logout")
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), 
                padding=ft.padding.only(20, 50, 20, 20)
            ),
            
            # Griglia Statistiche
            ft.Container(
                content=ft.Row([
                    stat_card("BMI", "24.5", "Normopeso", ft.Icons.MONITOR_WEIGHT, ft.Colors.BLUE_400),
                    ft.Container(width=10),
                    stat_card("BMR", "1700", "Kcal/giorno", ft.Icons.LOCAL_FIRE_DEPARTMENT, ft.Colors.ORANGE_400),
                ]), padding=ft.padding.symmetric(horizontal=20)
            ),

            # Card Idratazione
            ft.Container(
                content=ft.Column([
                    ft.Row([ft.Icon(ft.Icons.WATER_DROP, color=ft.Colors.BLUE_400), ft.Text("Idratazione", size=18, weight=ft.FontWeight.BOLD, color="white")]),
                    ft.Row([water_counter, ft.Text(" ml", size=18, color="#94a3b8", offset=ft.Offset(0, 0.2))]),
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "+ Aggiungi Bicchiere (250ml)", 
                        on_click=add_water, 
                        width=1000, 
                        style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_600, color="white", shape=ft.RoundedRectangleBorder(radius=10), padding=15)
                    )
                ]),
                bgcolor="#172554", border=ft.border.all(1, ft.Colors.BLUE_900),
                border_radius=20, padding=25, margin=20
            ),
        ],
        bgcolor="#0f172a",
        padding=0,
        
        # Navigation Bar Collegata
        navigation_bar=ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Home"),
                ft.NavigationBarDestination(icon=ft.Icons.FITNESS_CENTER, label="Schede"),
                ft.NavigationBarDestination(icon=ft.Icons.PERSON, label="Profilo"),
            ],
            bgcolor="#1e293b",
            indicator_color=ft.Colors.BLUE_600,
            selected_index=0, # Home è selezionata
            on_change=nav_change # <--- EVENTO DI NAVIGAZIONE
        )
    )