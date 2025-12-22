import flet as ft
from services.azure_db import generate_workout_ai, save_workout_async
import time

def generator_view(page: ft.Page):
    user_name = page.client_storage.get("username") or "Atleta"

    # --- INPUT USER ---
    txt_prompt = ft.TextField(
        label="Descrivi il tuo obiettivo",
        hint_text="Es. Voglio allenare le gambe per la forza, ho solo manubri, 3 giorni a settimana...",
        multiline=True,
        min_lines=3,
        max_lines=5,
        bgcolor="#1e293b",
        border_color="#334155",
        text_style=ft.TextStyle(color="white"),
        border_radius=12
    )

    # --- INDICATORE CARICAMENTO ---
    loading_anim = ft.Column([
        ft.ProgressRing(color=ft.Colors.PURPLE_400),
        ft.Text("Il Coach AI sta creando la tua scheda...", color=ft.Colors.PURPLE_200)
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, visible=False)

    # --- FUNZIONE GENERAZIONE ---
    def btn_generate_click(e):
        if not txt_prompt.value:
            txt_prompt.error_text = "Scrivi qualcosa!"
            page.update()
            return

        # 1. UI Loading
        btn_generate.disabled = True
        loading_anim.visible = True
        page.update()

        # 2. Chiamata Backend
        scheda_json = generate_workout_ai(txt_prompt.value, user_name)

        # 3. Gestione Risultato
        loading_anim.visible = False
        btn_generate.disabled = False
        
        if scheda_json:
            # Salviamo subito la scheda generata
            save_workout_async(scheda_json)
            
            page.open(ft.SnackBar(ft.Text("Scheda creata e salvata con successo!"), bgcolor="green"))
            time.sleep(1) # Un attimo per leggere
            page.go("/schede") # Torniamo alla lista
        else:
            page.open(ft.SnackBar(ft.Text("Errore nella generazione. Riprova."), bgcolor="red"))
        
        page.update()

    btn_generate = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.AUTO_AWESOME, color="white"),
            ft.Text("GENERA SCHEDA", weight="bold", color="white")
        ], alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=ft.Colors.PURPLE_600,
        padding=15,
        border_radius=12,
        on_click=btn_generate_click,
        shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.PURPLE_900)
    )

    # --- LAYOUT ---
    return ft.View(
        "/generatore",
        bgcolor="#0f172a",
        padding=20,
        controls=[
            # Header
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK_IOS, icon_color="white", on_click=lambda e: page.go("/schede")),
                ft.Text("AI Coach", size=24, weight="bold", color="white"),
            ]),
            
            ft.Container(height=20),
            
            # Card Input
            ft.Container(
                content=ft.Column([
                    ft.Text("Chiedi al Coach", size=18, weight="bold", color=ft.Colors.PURPLE_200),
                    ft.Text("Sii specifico su giorni, attrezzi e obiettivi.", size=12, color="grey"),
                    ft.Container(height=10),
                    txt_prompt,
                    ft.Container(height=20),
                    btn_generate,
                    ft.Container(height=20),
                    loading_anim
                ]),
                bgcolor="#1e293b",
                padding=20,
                border_radius=15,
                border=ft.border.all(1, ft.Colors.PURPLE_900)
            ),
            
            # Suggerimenti
            ft.Container(height=30),
            ft.Text("Esempi di prompt:", color="grey", weight="bold"),
            ft.Column([
                ft.Text("• Scheda Full Body 2 giorni a settimana solo corpo libero.", color="#64748b", italic=True),
                ft.Text("• Allenamento forza petto e tricipiti, livello avanzato.", color="#64748b", italic=True),
                ft.Text("• Scheda per mal di schiena, esercizi posturali.", color="#64748b", italic=True),
            ])
        ]
    )