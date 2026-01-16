import flet as ft

def dettaglio_allenamento_view(page: ft.Page):
    # recuoero dati dalla memoria
    workout = page.client_storage.get("allenamento_selezionato")
    
    # se mancano i dati ritorna allo storico
    if not workout:
        page.go("/workout")
        return ft.View("/dettaglio_allenamento", controls=[])

    # estrazione dati
    nome_scheda = workout.get('nome_scheda', 'Allenamento')
    data_log = workout.get('data', 'Senza data') 
    durata = workout.get('durata', '--')
    esercizi_svolti = workout.get('dettagli_esercizi', [])

    header_info_card = ft.Container(
        content=ft.Column([
            ft.Text(nome_scheda, size=24, weight="bold", color=ft.Colors.CYAN_400),
            ft.Row([
                ft.Icon(ft.Icons.CALENDAR_MONTH, size=16, color="grey"),
                ft.Text(f"Data: {data_log}", color="grey", size=12),
            ]),
            ft.Row([
                ft.Icon(ft.Icons.TIMER, size=16, color="grey"),
                ft.Text(f"Durata: {durata}", color="grey", size=12),
            ]),
        ], spacing=5),
        padding=20,
        bgcolor="#1e293b",
        border_radius=15,
        border=ft.border.only(left=ft.border.BorderSide(5, ft.Colors.CYAN_400))
    )

    # lista esercizi
    exercises_column = ft.Column(spacing=15)

    if not esercizi_svolti:
        exercises_column.controls.append(ft.Text("Nessun dettaglio registrato.", italic=True, color="grey"))
    else:
        for ex in esercizi_svolti:
            nome_ex = ex.get('exercise_name', 'Esercizio')
            sets = ex.get('sets_performed', [])

            rows_sets = []
            
            # --- AGGIUNTA INTESTAZIONI COLONNE ---
            if sets:
                rows_sets.append(
                    ft.Row([
                        ft.Text("SET", width=40, color="#64748b", size=11, weight="bold"),
                        ft.Text("KG", width=60, color="#64748b", size=11, weight="bold"),
                        ft.Text("REPS", width=40, color="#64748b", size=11, weight="bold"),
                    ], spacing=10)
                )

            # righe delle serie
            for idx, s in enumerate(sets, 1):
                kg = s.get('kg', '-')
                reps = s.get('reps', '-')
                rows_sets.append(
                    ft.Row([
                        ft.Text(f"{idx}°", color="white", size=14, width=40),
                        ft.Text(f"{kg}", color="white", weight="bold", width=60),
                        ft.Text(f"{reps}", color="white", weight="bold", width=40),
                    ], spacing=10)
                )

            # box-card esercizio
            card = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.FITNESS_CENTER, size=18, color="grey"),
                        ft.Text(nome_ex, size=18, weight="bold", color="white"),
                    ], spacing=10),
                    ft.Divider(color="#334155", height=20),
                    ft.Column(rows_sets, spacing=8)
                ]),
                bgcolor="#1e293b",
                padding=15,
                border_radius=12,
                border=ft.border.all(1, "#334155")
            )
            exercises_column.controls.append(card)

    return ft.View(
        "/dettaglio_allenamento",
        bgcolor="#0f172a",
        padding=20, 
        controls=[
            ft.SafeArea(
                ft.Column([
                    ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.ARROW_BACK_IOS, 
                            icon_color="white", 
                            icon_size=20,
                            tooltip="Indietro",
                            on_click=lambda e: page.go("/workout")
                        ),
                        ft.Text("Dettaglio Allenamento", size=20, weight="bold", color="white")
                    ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    
                    ft.Divider(color="transparent", height=10),
                    
                    ft.Column([
                        header_info_card,
                        ft.Divider(color="transparent", height=20),
                        ft.Text(f"ESERCIZI SVOLTI ({len(esercizi_svolti)})", size=14, weight="bold", color="#94a3b8"),
                        ft.Container(height=10),
                        exercises_column,
                        ft.Container(height=20) # spazio extra in fondo
                    ], scroll=ft.ScrollMode.AUTO, expand=True)
                    
                ], expand=True),
                expand=True
            )
        ]
    )