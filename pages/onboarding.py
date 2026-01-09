import flet as ft
from services.auth_service import login_microsoft
from services.azure_db import save_new_user

def onboarding_view(page: ft.Page):
    
    error_txt = ft.Text("", color="red", size=14)

    def login_click(e):
        # Feedback visivo: disabilita il bottone e mostra la rotellina
        btn_login.disabled = True
        btn_text.value = "Connessione in corso..."
        progress_ring.visible = True
        page.update()

        # --- CHIAMATA AL SERVIZIO REALE ---
        user_data = login_microsoft()
        print("user_data in onboarding page:\n\n", user_data)
        
        if user_data:
            # SUCCESSO: Salviamo i dati
            # Salviamo l'email come identificativo univoco per il database
            page.client_storage.set("user_email", user_data["email"])
            # Salviamo il nome per mostrarlo nell'interfaccia ("Ciao Mario")
            page.client_storage.set("user_name", user_data["name"])
            page.client_storage.set("oid", user_data["oid"])
            
            save_new_user(user_data)
            
            print(f"Login successo: {user_data['email']}")
            page.go("/")
        else:
            # ERRORE
            btn_login.disabled = False
            btn_text.value = "Accedi con Microsoft"
            progress_ring.visible = False
            error_txt.value = "Login fallito o annullato."
            page.update()

    # Componenti Grafici
    progress_ring = ft.ProgressRing(width=20, height=20, color="white", visible=False)
    btn_text = ft.Text("Accedi con Microsoft", color="white", weight="bold")
    
    btn_login = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.WINDOW_SHARP, color="white"), # Icona stile Windows/Microsoft
            btn_text,
            progress_ring
        ], alignment=ft.MainAxisAlignment.CENTER),
        bgcolor="#0078D4", # Blu Microsoft
        padding=15,
        border_radius=8,
        on_click=login_click,
        width=300
    )

    return ft.View(
        "/welcome",
        controls=[
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.FITNESS_CENTER, size=80, color=ft.Colors.BLUE_600),
                    ft.Text("GymLog", size=40, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Text("Login Istituzionale & Personale", color="#94a3b8"),
                    ft.Container(height=40),
                    btn_login,
                    ft.Container(height=10),
                    error_txt,
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                expand=True
            )
        ],
        bgcolor="#0f172a",
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )