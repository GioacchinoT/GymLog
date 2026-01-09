#import flet as ft
from pages.home import home_view
from pages.onboarding import onboarding_view
from pages.schede import schede_view          # <--- NUOVO IMPORT (Dashboard)
from pages.crea_scheda import create_routine_view # <--- VECCHIO IMPORT (Form)
from pages.dettaglio_scheda import dettaglio_view
from pages.generatore_schede_ai import generator_view
from pages.storico_allenamento import workout_view
from pages.start_allenamento import active_workout_view
from pages.gestione_esercizi import gestione_esercizi_view

def main(page: ft.Page):
    page.title = "GymLog"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    
    def route_change(route):
        page.views.clear()
        
        # --- GESTIONE ROTTE ---
        if page.route == "/":
            page.views.append(home_view(page))
        elif page.route == "/welcome":
            page.views.append(onboarding_view(page))
        
        # Rotta Dashboard Schede (Quella visuale)
        elif page.route == "/schede":
            page.views.append(schede_view(page))
            
        # Rotta Form Creazione (Quella funzionale)
        elif page.route == "/crea_scheda":
            page.views.append(create_routine_view(page))

        # Rotta dettaglio scheda (Quella funzionale)
        elif page.route == "/dettaglio":
            page.views.append(dettaglio_view(page))

        # Rotta generatore scheda AI
        elif page.route == "/generatore":
            page.views.append(generator_view(page))
        
# --- NUOVA ROTTA ALLENAMENTO ---
        elif page.route == "/workout":
            page.views.append(workout_view(page))

        elif page.route == "/live_workout":
            page.views.append(active_workout_view(page))

        elif page.route == "/esercizi":
            page.views.append(gestione_esercizi_view(page))
        
        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    user_email = page.client_storage.get("user_email")
    
    if user_email:
        page.go("/")
    else:
        page.go("/welcome")

if __name__ == "__main__":
    """ft.app(
        target=main, 
        view=ft.WEB_BROWSER, 
        port=8080, 
        host="0.0.0.0"  # <--- Questo è il comando magico
    )"""
    ft.app(target=main)