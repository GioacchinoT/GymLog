import flet as ft
from pages.home import home_view
from pages.onboarding import onboarding_view
from pages.schede import schede_view          # <--- NUOVO IMPORT (Dashboard)
from pages.crea_scheda import create_routine_view # <--- VECCHIO IMPORT (Form)

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
        
        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    username = page.client_storage.get("username")
    if username:
        page.go("/")
    else:
        page.go("/welcome")

if __name__ == "__main__":
    ft.app(target=main)