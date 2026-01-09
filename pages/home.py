import flet as ft
import threading
from services.azure_db import get_schede, update_user, get_user_data

def home_view(page: ft.Page):
    # --- 1. RECUPERO DATI UTENTE ---
    user_email = page.client_storage.get("user_email")
    user_name = page.client_storage.get("user_name") 
    user_oid = page.client_storage.get("oid")
    
    if not user_name:
        user_name = user_email or "Atleta"

 
    cached_weight = page.client_storage.get("user_weight")
    cached_height = page.client_storage.get("user_height")
    cached_age = page.client_storage.get("user_age")

    # Variabili che useremo nella pagina
    user_weight = cached_weight
    user_height = cached_height
    user_age = cached_age

    # B. Se la cache è vuota (es. primo accesso su questo PC), scarichiamo dal server
    # Verifichiamo se manca anche solo un dato importante
    if not user_weight or not user_height or not user_age:
        print("⏳ Cache vuota o incompleta. Scarico dati dal server...")
        server_data = get_user_data(user_oid)

        if server_data:
            # Prendiamo i dati dal server
            user_weight = server_data.get("peso", "inserisci dati")
            user_height = server_data.get("altezza", "inserisci dati")
            user_age = server_data.get("età", "inserisci dati")
            
            # SALVIAMO SUBITO IN CACHE per la prossima volta
            page.client_storage.set("user_weight", user_weight)
            page.client_storage.set("user_height", user_height)
            page.client_storage.set("user_age", user_age)
        else:
            # Fallback se server offline e cache vuota
            user_weight = "inserisci dati"
            user_height = "inserisci dati"
            user_age = "inserisci dati"
    else:
        print("⚡ Dati utente caricati dalla Cache locale (Nessuna chiamata server).")


    # --- 2. LOGICA CALCOLO BMI & BMR ---
    def calculate_metrics():
        try:
            w = float(user_weight)
            h = float(user_height)
            a = float(user_age)
            
            # BMI
            bmi = w / ((h / 100) ** 2)
            lbl_bmi_val.value = f"{bmi:.1f}"
            
            if bmi < 18.5: lbl_bmi_desc.value, lbl_bmi_desc.color = "Sottopeso", "orange"
            elif bmi < 25: lbl_bmi_desc.value, lbl_bmi_desc.color = "Normopeso", "green"
            elif bmi < 30: lbl_bmi_desc.value, lbl_bmi_desc.color = "Sovrappeso", "orange"
            else: lbl_bmi_desc.value, lbl_bmi_desc.color = "Obeso", "red"

            # BMR (Formula Mifflin-St Jeor approssimata per uomo)
            bmr = (10 * w) + (6.25 * h) - (5 * a) + 5
            lbl_bmr_val.value = f"{int(bmr)}"
            
        except:
            lbl_bmi_val.value = "--"
            lbl_bmr_val.value = "--"
        
        page.update()

    # UI Elementi per le metriche
    lbl_bmi_val = ft.Text("--", size=30, weight="bold", color="white")
    lbl_bmi_desc = ft.Text("...", size=14, color="grey")
    lbl_bmr_val = ft.Text("--", size=30, weight="bold", color="white")

    # --- 3. DIALOG MODIFICA DATI ---
    txt_edit_weight = ft.TextField(label="Peso (kg)", value=user_weight, bgcolor="#1e293b", color="white", border_color="#334155")
    txt_edit_height = ft.TextField(label="Altezza (cm)", value=user_height, bgcolor="#1e293b", color="white", border_color="#334155")
    txt_edit_age = ft.TextField(label="Età", value=user_age, bgcolor="#1e293b", color="white", border_color="#334155")

    def save_stats(e):
        nonlocal user_weight, user_height, user_age
        
        # 1. Prendiamo i nuovi valori inputati
        new_weight = txt_edit_weight.value
        new_height = txt_edit_height.value
        new_age = txt_edit_age.value
        
        # 2. Aggiorniamo le variabili locali
        user_weight = new_weight
        user_height = new_height
        user_age = new_age
        
        # 3. Aggiorniamo la UI subito
        lbl_weight.value = f"{user_weight} kg"
        lbl_height.value = f"{user_height} cm"
        lbl_age.value = f"{user_age} anni"
        
        # 4. AGGIORNAMENTO SERVER (Thread separato per non bloccare)
        user_biometrics={
            "peso": user_weight,
            "altezza": user_height,
            "età": user_age,
            "oid": user_oid,
        }
        update_user(user_biometrics)

        # 5. AGGIORNAMENTO CACHE LOCALE (Fondamentale!)
        # Così al prossimo riavvio l'app troverà i dati nuovi senza chiedere al server
        page.client_storage.set("user_weight", user_weight)
        page.client_storage.set("user_height", user_height)
        page.client_storage.set("user_age", user_age)
        print("✅ Cache locale aggiornata con i nuovi dati.")
        
        calculate_metrics()
        page.close(dialog_edit)
        page.update()

    dialog_edit = ft.AlertDialog(
        modal=True,
        title=ft.Text("Aggiorna i tuoi dati"),
        bgcolor="#0f172a",
        content=ft.Column([txt_edit_weight, txt_edit_height, txt_edit_age], height=200, tight=True),
        actions=[
            ft.TextButton("Annulla", on_click=lambda e: page.close(dialog_edit)),
            ft.ElevatedButton("Salva", on_click=save_stats, bgcolor=ft.Colors.BLUE_600, color="white")
        ]
    )

    # --- 4. CARICAMENTO STATISTICHE ALLENAMENTO (Ottimizzato) ---
    # Anche qui usiamo una cache "leggera" per mostrare subito i numeri,
    # poi il thread in background controlla se ci sono novità.
    
    cached_num_schede = page.client_storage.get("stats_num_schede") or "..."
    cached_num_ex = page.client_storage.get("stats_num_ex") or "..."

    lbl_count_schede = ft.Text(str(cached_num_schede), size=24, weight="bold", color=ft.Colors.CYAN_400)
    lbl_count_esercizi = ft.Text(str(cached_num_ex), size=24, weight="bold", color=ft.Colors.PURPLE_400)

    def load_gym_stats():
        if not user_email: return
        try:
            # Scarica i dati freschi
            schede = get_schede(user_email)
            num_schede = len(schede)
            num_ex = sum(len(s.get('esercizi', [])) for s in schede)
            
            # Aggiorna UI
            lbl_count_schede.value = str(num_schede)
            lbl_count_esercizi.value = str(num_ex)
            page.update()
            
            # Aggiorna Cache per la prossima volta
            page.client_storage.set("stats_num_schede", num_schede)
            page.client_storage.set("stats_num_ex", num_ex)
            
        except Exception as e:
            print(f"Errore stats: {e}")

    # Avviamo il thread per aggiornare i numeri in background
    # (Così l'utente vede subito i vecchi numeri cache, poi si aggiornano da soli)
    threading.Thread(target=load_gym_stats, daemon=True).start()

    # --- 5. COMPONENTI UI (Resto del codice invariato) ---
    
    header = ft.Row([
        ft.Column([
            ft.Text(f"Ciao, {user_name}", size=28, weight=ft.FontWeight.BOLD, color="white", no_wrap=False),
            ft.Text("Pronto a superare i tuoi limiti?", size=14, color="#94a3b8"),
        ], expand=True),  # <--- QUESTO expand=True È LA SOLUZIONE
        
        ft.IconButton(ft.Icons.LOGOUT, icon_color="red", tooltip="Esci", 
                      on_click=lambda e: [page.client_storage.clear(), page.go("/welcome")])
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)



    def stat_mini_card(icon, label, value_ref, color):
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, color=color, size=24),
                ft.Text(label, size=12, color="grey"),
                value_ref 
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor="#1e293b",
            padding=15,
            border_radius=15,
            expand=True,
            border=ft.border.all(1, "#334155")
        )

    lbl_weight = ft.Text(f"{user_weight} kg", weight="bold", color="white")
    lbl_height = ft.Text(f"{user_height} cm", weight="bold", color="white")
    lbl_age = ft.Text(f"{user_age} anni", weight="bold", color="white")

    physical_stats_row = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("I tuoi dati", weight="bold", color="white", size=16),
                ft.IconButton(ft.Icons.EDIT, icon_color=ft.Colors.BLUE_400, icon_size=20, on_click=lambda e: page.open(dialog_edit))
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Row([
                stat_mini_card(ft.Icons.MONITOR_WEIGHT, "PESO", lbl_weight, ft.Colors.BLUE_400),
                ft.Container(width=10),
                stat_mini_card(ft.Icons.HEIGHT, "ALTEZZA", lbl_height, ft.Colors.BLUE_400),
                ft.Container(width=10),
                stat_mini_card(ft.Icons.CAKE, "ETÀ", lbl_age, ft.Colors.BLUE_400),
            ])
        ]),
        bgcolor="#0f172a", 
        margin=ft.margin.only(bottom=20)
    )

    def big_metric_card(title, value_ctrl, subtitle_ctrl, icon, color):
        return ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(icon, color=color), ft.Text(title, weight="bold", color=color)]),
                ft.Container(height=5),
                value_ctrl,
                subtitle_ctrl
            ]),
            bgcolor="#1e293b", padding=20, border_radius=15, expand=True
        )

    metrics_row = ft.Row([
        big_metric_card("BMI", lbl_bmi_val, lbl_bmi_desc, ft.Icons.HEALTH_AND_SAFETY, ft.Colors.GREEN_400),
        ft.Container(width=10),
        big_metric_card("BMR (Kcal)", lbl_bmr_val, ft.Text("Kcal/giorno", color="grey", size=12), ft.Icons.LOCAL_FIRE_DEPARTMENT, ft.Colors.ORANGE_400)
    ])

    gym_stats_card = ft.Container(
        content=ft.Column([
            ft.Text("Overview Allenamenti", size=16, weight="bold", color="white"),
            ft.Divider(color="transparent", height=10),
            ft.Row([
                ft.Column([
                    lbl_count_schede,
                    ft.Text("Schede Create", color="grey", size=12)
                ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                
                ft.Container(width=1, height=40, bgcolor="#334155"), 
                
                ft.Column([
                    lbl_count_esercizi,
                    ft.Text("Esercizi Aggiunti", color="grey", size=12)
                ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ])
        ]),
        bgcolor="#1e293b",
        padding=20,
        border_radius=15,
        border=ft.border.all(1, ft.Colors.CYAN_900),
        shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.CYAN_900, offset=ft.Offset(0,0))
    )

    # --- NAVIGAZIONE (Modificata) ---
    def nav_change(e):
        index = e.control.selected_index
        if index == 0: page.go("/schede")
        elif index == 1: pass # Siamo in Home
        elif index == 2: page.go("/workout") # Nuova sezione Allenamento

    # Calcoliamo le metriche subito con i dati (cache o server)
    calculate_metrics()

    return ft.View(
        "/",
        bgcolor="#0f172a",
        padding=20,
        scroll=ft.ScrollMode.AUTO, 
        controls=[
            header,
            ft.Divider(color="transparent", height=20),
            physical_stats_row,
            metrics_row,
            ft.Divider(color="transparent", height=20),
            gym_stats_card
        ],
        navigation_bar=ft.NavigationBar(
            destinations=[
                # ORDINE: Schede - Home - Allenamento
                ft.NavigationBarDestination(icon=ft.Icons.FOLDER_COPY, label="Schede"),
                ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Home"),
                ft.NavigationBarDestination(icon=ft.Icons.SPORTS_GYMNASTICS, label="Allenamento"),
            ],
            bgcolor="#1e293b",
            indicator_color=ft.Colors.BLUE_600,
            selected_index=1, # Home è l'indice 1 (Centro)
            on_change=nav_change
        )
    )