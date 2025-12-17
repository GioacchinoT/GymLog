import flet as ft

def onboarding_view(page: ft.Page):
    # Campo di testo per il nome
    name_field = ft.TextField(
        label="Come ti chiami?",
        border_color=ft.Colors.BLUE_600,
        text_align=ft.TextAlign.CENTER,
        text_style=ft.TextStyle(color="white"),
        width=300,
        bgcolor="#1e293b" # Slate 800
    )

    def save_and_start(e):
        if not name_field.value:
            name_field.error_text = "Inserisci un nome per continuare!"
            page.update()
            return
        
        # --- PUNTO CHIAVE ---
        # Salviamo il nome in modo persistente nel dispositivo
        page.client_storage.set("username", name_field.value)
        
        # Reindirizziamo l'utente alla Home
        page.go("/")

    return ft.View(
        "/welcome",
        controls=[
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.FITNESS_CENTER, size=80, color=ft.Colors.BLUE_600),
                    ft.Text("Benvenuto in AzureGym", size=30, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Text("La tua palestra connessa al cloud.", color="#94a3b8", size=16),
                    ft.Container(height=40),
                    name_field,
                    ft.Container(height=20),
                    ft.ElevatedButton(
                        "Inizia Subito",
                        on_click=save_and_start,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.BLUE_600, 
                            color="white", 
                            padding=20,
                            shape=ft.RoundedRectangleBorder(radius=10)
                        ),
                        width=300
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                expand=True
            )
        ],
        bgcolor="#0f172a", # Slate 900 Background
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )