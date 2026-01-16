import flet as ft
import time
import threading
from datetime import datetime
from services.azure_db import save_workout_log_blocking, get_workout_logs

def active_workout_view(page: ft.Page):

    #recupero scheda scelta per allenamento
    scheda_source = page.client_storage.get("workout_active_scheda")
    user_email = page.client_storage.get("user_email")

    if not scheda_source:
        page.go("/workout")
        return ft.View("/live_workout", controls=[])

    # recupero dati del vecchio allenamento 
    history_map = {} 
    
    try:
        logs = get_workout_logs(user_email)
        if logs:
            print(f"[DEBUG] Trovati {len(logs)} allenamenti nello storico")
            for log in logs:
                for details in log.get("dettagli_esercizi", []):
                    raw_name = details.get("exercise_name", "")
                    clean_name = raw_name.strip().lower()
                    
                    # salvataggio esercizio svolto
                    if clean_name and clean_name not in history_map:
                        history_map[clean_name] = details.get("sets_performed", [])
    except Exception as e:
        print(f"XXX Errore recupero storico per ghost values: {e}")


    # timer
    start_time = time.time()
    timer_running = True
    txt_timer = ft.Text("00:00", size=35, weight="bold", color=ft.Colors.CYAN_400, font_family="Consolas, monospace")

    def update_timer():
        while timer_running:
            elapsed = int(time.time() - start_time)
            mins, secs = divmod(elapsed, 60)
            txt_timer.value = f"{mins:02d}:{secs:02d}"
            try:
                page.update()
            except:
                break
            time.sleep(1)

    threading.Thread(target=update_timer, daemon=True).start()

    # struttura dati
    exercises_data = {} 
    btn_termina = ft.ElevatedButton("TERMINA ALLENAMENTO", bgcolor=ft.Colors.RED_600, color="white", height=50, width=200)

    def finish_workout(e):
        nonlocal timer_running
        
        # feedback visivo
        btn_termina.text = "SALVATAGGIO..."
        btn_termina.disabled = True
        btn_termina.bgcolor = ft.Colors.GREY_700
        page.update()

        timer_running = False
        
        # calcolo durata
        elapsed_seconds = int(time.time() - start_time)
        mins, secs = divmod(elapsed_seconds, 60)
        final_duration = f"{mins}m {secs}s"
        
        log_exercises = []
        
        # raccolta dati dagli input
        for i, ex_original in enumerate(scheda_source.get("esercizi", [])):
            sets_done = []
            input_rows = exercises_data.get(i, [])
            
            for row_refs in input_rows:
                kg_val = row_refs["kg"].current.value
                reps_val = row_refs["reps"].current.value
                
                # salvataggio solo se c'è almeno un dato 
                if kg_val or reps_val:
                    sets_done.append({"kg": kg_val or "0", "reps": reps_val or "0"})
            
            log_exercises.append({
                "exercise_name": ex_original.get("exercise_name") or ex_original.get("nome"),
                "sets_performed": sets_done
            })

        workout_log = {
            "user_email": user_email,
            "nome_scheda": scheda_source.get("nome_scheda"),
            "durata": final_duration,
            "data": datetime.now().strftime("%Y-%m-%d"),
            "dettagli_esercizi": log_exercises
        }
        
        def _save_process():
            success = save_workout_log_blocking(workout_log)
            if success:
                page.open(ft.SnackBar(ft.Text(f"Grande! Allenamento completato in {final_duration}."), bgcolor="green"))
                page.go("/workout")
            else:
                btn_termina.text = "RIPROVA"
                btn_termina.disabled = False
                btn_termina.bgcolor = ft.Colors.RED_600
                page.update()
                page.open(ft.SnackBar(ft.Text("Errore salvataggio. Riprova."), bgcolor="red"))

        threading.Thread(target=_save_process).start()
    
    btn_termina.on_click = finish_workout


    # costruzione UI lista esercizi
    exercises_ui_list = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=25)

    for i, ex in enumerate(scheda_source.get("esercizi", [])):
        nome_ex = ex.get("exercise_name") or ex.get("nome", "Esercizio")
        target_reps = ex.get("ripetizioni", "8-10") 
        
        #recupero storico esercizio
        clean_nome_ex = nome_ex.strip().lower()
        prev_sets = history_map.get(clean_nome_ex, [])
        
        sets_column = ft.Column(spacing=8)
        exercises_data[i] = [] 

        # funzione per aggiungere righe/serie
        def add_set_row(e, ex_idx=i, container=sets_column, default_target=target_reps, history_list=prev_sets):

            current_set_idx = len(exercises_data[ex_idx])
            display_num = current_set_idx + 1
            
            # ricerca i dati ghost dallo storico
            ghost_kg = ""
            ghost_reps = ""
            if current_set_idx < len(history_list):
                prev_data = history_list[current_set_idx]
                val_kg = str(prev_data.get("kg", ""))
                val_reps = str(prev_data.get("reps", ""))
                
                if val_kg and val_kg != "0": ghost_kg = val_kg
                if val_reps and val_reps != "0": ghost_reps = val_reps

            ref_kg = ft.Ref[ft.TextField]()
            ref_reps = ft.Ref[ft.TextField]()
            
            # check btn
            def toggle_check(e):
                is_checked = e.control.icon == ft.Icons.CHECK_CIRCLE
                if is_checked:
                    # uncheck
                    e.control.icon = ft.Icons.RADIO_BUTTON_UNCHECKED
                    e.control.icon_color = "grey"
                    row_container.bgcolor = "#1e293b" 
                else:
                    # check
                    e.control.icon = ft.Icons.CHECK_CIRCLE
                    e.control.icon_color = ft.Colors.GREEN_400
                    row_container.bgcolor = "#14532d" 
                page.update()

            check_btn = ft.IconButton(
                icon=ft.Icons.RADIO_BUTTON_UNCHECKED, 
                icon_color="grey", 
                tooltip="Segna come fatto", 
                on_click=toggle_check
            )

            txt_kg = ft.TextField(
                ref=ref_kg,
                hint_text=ghost_kg if ghost_kg else "Kg",
                
                hint_style=ft.TextStyle(color=ft.Colors.WHITE24), 
                width=80, 
                bgcolor=ft.Colors.BLACK12, 
                border_radius=8,
                border_width=0, 
                text_align="center", 
                keyboard_type=ft.KeyboardType.NUMBER,
                text_style=ft.TextStyle(size=18, weight="bold", color="white")
            )

            txt_reps = ft.TextField(
                ref=ref_reps, 
                hint_text=ghost_reps if ghost_reps else default_target, 
                
                hint_style=ft.TextStyle(color=ft.Colors.WHITE24),
                width=80, 
                bgcolor=ft.Colors.BLACK12,
                border_radius=8,
                border_width=0,
                text_align="center", 
                keyboard_type=ft.KeyboardType.NUMBER,
                text_style=ft.TextStyle(size=18, weight="bold", color="white")
            )

            row_container = ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Text(str(display_num), weight="bold", color="grey", size=16), 
                        width=30, alignment=ft.alignment.center
                    ),
                    txt_kg,
                    txt_reps,
                    check_btn,
                    ft.IconButton(
                        ft.Icons.DELETE_OUTLINE, 
                        icon_color=ft.Colors.RED_300, 
                        icon_size=20, 
                        tooltip="Rimuovi serie",
                        on_click=lambda e, c=container: remove_last_set(c, ex_idx)
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                bgcolor="#1e293b", 
                padding=10, 
                border_radius=12,
                animate=ft.Animation(300, "easeOut")
            )
            
            exercises_data[ex_idx].append({"kg": ref_kg, "reps": ref_reps})
            container.controls.append(row_container)
            page.update()

        def remove_last_set(container, ex_idx):
            if container.controls:
                container.controls.pop()
                exercises_data[ex_idx].pop()
                page.update()

        try: num_series = int(ex.get("serie", 3))
        except: num_series = 3
            
        for _ in range(num_series):
            add_set_row(None)

        #card esercizio
        last_log_str = "Primo Allenamento"
        if prev_sets:
            s1 = prev_sets[0]
            val_kg = str(s1.get('kg','0'))
            val_reps = str(s1.get('reps','0'))
            if val_kg != "0":
                last_log_str = f"Ultimo: {val_kg}kg x {val_reps}"
            else:
                last_log_str = "Ultimo: (Vuoto)"

        ex_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Column([
                        ft.Text(nome_ex, size=18, weight="bold", color="white"),
                        ft.Row([
                            ft.Container(content=ft.Text(f"Target: {target_reps}", size=11, weight="bold"), bgcolor=ft.Colors.BLUE_900, padding=4, border_radius=4),
                            ft.Text(last_log_str, color="grey", size=12, italic=True)
                        ])
                    ], spacing=3),
                ], alignment=ft.MainAxisAlignment.START),
                
                ft.Divider(color="transparent", height=10),
                
                ft.Row([
                    ft.Text("SET", width=30, text_align="center", color="#64748b", size=11, weight="bold"),
                    ft.Text("KG", width=80, text_align="center", color="#64748b", size=11, weight="bold"),
                    ft.Text("REPS", width=80, text_align="center", color="#64748b", size=11, weight="bold"),
                    ft.Text("FATTO", width=40, text_align="center", color="#64748b", size=11, weight="bold"),
                    ft.Container(width=40) 
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                sets_column,
                
                ft.Container(height=10),
                ft.TextButton(
                    "+ Aggiungi Serie", 
                    icon=ft.Icons.ADD, 
                    icon_color=ft.Colors.BLUE_400,
                    style=ft.ButtonStyle(color=ft.Colors.BLUE_400),
                    on_click=lambda e, i=i, c=sets_column: add_set_row(e, i, c)
                )
            ]),
            bgcolor="#0f172a", 
            padding=15,
            border_radius=15,
            border=ft.border.all(1, "#334155")
        )
        exercises_ui_list.controls.append(ex_card)


    header = ft.Container(
        content=ft.Column([
            ft.Text(scheda_source.get("nome_scheda", "Allenamento").upper(), size=16, color="grey", weight="bold"),
            ft.Container(height=5),
            ft.Row([
                txt_timer,
            ], alignment=ft.MainAxisAlignment.CENTER),
        ]),
        padding=ft.padding.only(bottom=20)
    )

    return ft.View(
        "/live_workout",
        bgcolor="#0f172a",
        padding=ft.padding.only(top=60, left=20, right=20, bottom=20),
        controls=[
            header,
            exercises_ui_list,
            ft.Container(height=10),
            ft.Container(content=btn_termina, alignment=ft.alignment.center, padding=20)
        ]
    )