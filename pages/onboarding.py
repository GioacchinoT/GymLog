import flet as ft
from services.auth_service import login_microsoft
from services.azure_db import save_new_user
import threading

def onboarding_view(page: ft.Page):
    
    # --- ELEMENTI UI (Stile Originale) ---
    
    # Bottone Blu Principale
    btn_text = ft.Text("Accedi con Microsoft", color="white", weight="bold", size=16)
    loading_ring_main = ft.ProgressRing(width=20, height=20, stroke_width=2, color="white", visible=False)
    btn_icon = ft.Icon(ft.Icons.WINDOW_SHARP, color="white", size=20)
    error_txt = ft.Text("", color="red", size=14)

    # --- SEZIONE CODICE ---
    lbl_istruzioni = ft.Text("Copia il codice e inseriscilo nel link:", color="#94a3b8", visible=False, size=13)
    
    # Testo Codice
    lbl_codice = ft.Text("", size=30, weight="bold", color=ft.Colors.CYAN_400, selectable=True, font_family="monospace")
    
    # Tastino Copia
    btn_copy = ft.IconButton(
        icon=ft.Icons.CONTENT_COPY,
        icon_color=ft.Colors.CYAN_400,
        tooltip="Copia Codice",
        on_click=lambda e: copy_code(e)
    )

    # Riga Codice + Tasto
    row_codice = ft.Row(
        [lbl_codice, btn_copy],
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        visible=False
    )
    
    # Bottone Arancione Link
    btn_apri_link = ft.Container(
        content=ft.Text("APRI PAGINA MICROSOFT", color="white", weight="bold"),
        bgcolor=ft.Colors.ORANGE_600,
        padding=15,
        border_radius=8,
        width=300,
        alignment=ft.alignment.center,
        on_click=lambda e: None, # Assegnato dinamicamente
        visible=False
    )

    # --- NUOVA ROTELLA (Sotto il tasto arancione) ---
    # Questa appare SOLO quando clicchi "Apri Pagina Microsoft"
    loading_wait = ft.ProgressRing(width=20, height=20, stroke_width=2, color="white", visible=False)
    lbl_wait = ft.Text("In attesa del login...", color="grey", size=12, italic=True, visible=False)
    
    col_wait = ft.Column([
        loading_wait,
        lbl_wait
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5, visible=False)


    # --- FUNZIONI ---

    def copy_code(e):
        page.set_clipboard(lbl_codice.value)
        page.open(ft.SnackBar(ft.Text("Codice copiato negli appunti!"), bgcolor="green"))

    def on_link_clicked(e, url):
        """Gestisce il click sul tasto arancione"""
        # Apre il browser
        page.launch_url(url)
        
        # Mostra la rotella di attesa sotto
        col_wait.visible = True
        loading_wait.visible = True
        lbl_wait.visible = True
        page.update()

    def mostra_codice_ui(user_code, verification_uri):
        # Nasconde bottone blu
        btn_login_container.visible = False
        
        # Mostra sezione codice
        lbl_istruzioni.visible = True
        lbl_codice.value = user_code
        row_codice.visible = True
        
        # Configura e mostra tasto arancione
        btn_apri_link.visible = True
        # Qui colleghiamo la nuova funzione che mostra la rotella
        btn_apri_link.on_click = lambda e: on_link_clicked(e, verification_uri)
        
        page.update()

    def process_login():
        user_data = login_microsoft(ui_callback=mostra_codice_ui)
        
        if user_data:
            page.client_storage.set("user_email", user_data["email"])
            page.client_storage.set("user_name", user_data["name"])
            page.client_storage.set("oid", user_data["oid"])
            save_new_user(user_data)
            page.go("/")
        else:
            reset_ui_state()
            error_txt.value = "Tempo scaduto o errore. Riprova."
            page.update()

    def start_login_click(e):
        btn_icon.visible = False
        btn_text.value = "Connessione in corso..."
        loading_ring_main.visible = True
        btn_login_container.disabled = True
        btn_login_container.opacity = 0.8
        error_txt.value = ""
        page.update()
        
        threading.Thread(target=process_login, daemon=True).start()

    def reset_ui_state():
        # Ripristina tutto lo stato iniziale
        btn_icon.visible = True
        btn_text.value = "Accedi con Microsoft"
        loading_ring_main.visible = False
        btn_login_container.visible = True
        btn_login_container.disabled = False
        btn_login_container.opacity = 1.0
        
        lbl_istruzioni.visible = False
        row_codice.visible = False
        btn_apri_link.visible = False
        
        # Nascondi anche la nuova rotella di attesa
        col_wait.visible = False

    # Container del bottone principale (Stile quadrato originale)
    btn_login_container = ft.Container(
        content=ft.Row([
            btn_icon,
            btn_text,
            loading_ring_main
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
        bgcolor="#0078D4",
        padding=15,
        border_radius=8,
        width=300,
        on_click=start_login_click,
        animate=ft.Animation(200, "easeOut")
    )

    return ft.View(
        "/welcome",
        padding=ft.padding.only(top=60, left=20, right=20, bottom=20), 
        controls=[
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.FITNESS_CENTER, size=80, color=ft.Colors.BLUE_600),
                    ft.Text("GymLog", size=40, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Text("Login Microsoft Account", color="#94a3b8"),
                    
                    ft.Container(height=60),
                    
                    btn_login_container, # Bottone blu
                    
                    # Area Codice (appare dopo)
                    ft.Container(height=20),
                    lbl_istruzioni,
                    row_codice,          # Codice + Tasto Copia
                    ft.Container(height=10),
                    btn_apri_link,       # Bottone arancione
                    
                    ft.Container(height=15),
                    col_wait,            # <--- NUOVA ROTELLA DI ATTESA QUI
                    
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