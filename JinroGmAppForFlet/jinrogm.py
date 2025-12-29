import flet as ft
import random

# --- モダン・カラーテーマ ---
class AppColors:
    BG = "#1A1C1E"          # 深い紺色の背景
    SURFACE = "#2D3033"     # カードの背景
    PRIMARY = "#A8DADC"     # メインアクセント（水色系）
    SECONDARY = "#457B9D"   # サブ
    ACCENT = "#E63946"      # 警告・人狼（赤）
    VILLAGER = "#1D3557"    # 村人陣営（濃紺）
    TEXT = "#F1FAEE"        # テキスト（白）
    TEXT_DIM = "#909090"    # 補助テキスト
    ALIVE_BG = "#34495E"
    DEAD_BG = "#121212"

class Player:
    def __init__(self, name=""):
        self.name = name
        self.role = ""
        self.is_alive = True

def main(page: ft.Page):
    page.title = "人狼GM Dashboard"
    page.bgcolor = AppColors.BG
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.window_width = 1400
    page.window_height = 900

    # --- 状態管理 ---
    registered_members = []
    game_members = []
    role_counts = {"人狼": 0, "狂人": 0, "占い師": 0, "霊媒師": 0, "狩人": 0}

    # --- UIコンポーネントの定義 ---
    member_list_view = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO)
    game_member_list_view = ft.ListView(expand=True, spacing=8)
    role_settings_view = ft.Column(spacing=10)

    # --- UI更新関数 ---
    def update_registered_ui():
        member_list_view.controls.clear()
        chips = []
        for i, p in enumerate(registered_members):
            chips.append(
                ft.Chip(
                    label=ft.Text(p.name, color=AppColors.TEXT),
                    bgcolor=AppColors.SECONDARY,
                    on_click=lambda e, idx=i: add_to_game(idx),
                    on_delete=lambda e, idx=i: delete_registered(idx),
                )
            )
        member_list_view.controls = [ft.Row(chips, wrap=True)]
        page.update()

    def update_game_ui():
        game_member_list_view.controls.clear()
        for i, p in enumerate(game_members):
            status_color = AppColors.PRIMARY if p.is_alive else AppColors.TEXT_DIM
            card_bg = AppColors.ALIVE_BG if p.is_alive else AppColors.DEAD_BG
            
            game_member_list_view.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(f"{i+1}", width=30, weight="bold", color=AppColors.TEXT_DIM),
                        ft.Text(p.name, expand=2, size=18, weight="bold", color=status_color),
                        ft.Container(
                            content=ft.Text(p.role if p.role else "役職未設定", size=12, color=AppColors.TEXT),
                            padding=ft.padding.all(5),
                            bgcolor=AppColors.SECONDARY if p.is_alive else ft.colors.TRANSPARENT,
                            border_radius=5,
                        ),
                        ft.IconButton(
                            ft.Icons.FACE if p.is_alive else ft.Icons.SKULL, 
                            icon_color=AppColors.ACCENT if not p.is_alive else AppColors.PRIMARY,
                            on_click=lambda e, idx=i: toggle_alive(idx),
                        ),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=AppColors.TEXT_DIM, 
                                      on_click=lambda e, idx=i: remove_from_game(idx)),
                    ]),
                    padding=10,
                    bgcolor=card_bg,
                    border_radius=10,
                    border=ft.border.all(1, AppColors.SECONDARY if p.is_alive else ft.colors.BLACK)
                )
            )
        page.update()

    def update_role_ui():
        role_settings_view.controls.clear()
        for role, count in role_counts.items():
            role_settings_view.controls.append(
                ft.Row([
                    ft.Text(role, expand=1, size=16),
                    ft.IconButton(ft.Icons.REMOVE_CIRCLE_OUTLINE, on_click=lambda e, r=role: adjust_role(r, -1)),
                    ft.Text(str(count), width=30, text_align="center", size=18, weight="bold"),
                    ft.IconButton(ft.Icons.ADD_CIRCLE_OUTLINE, on_click=lambda e, r=role: adjust_role(r, 1)),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            )
        page.update()

    # --- ロジック関数 ---
    def toggle_alive(idx):
        game_members[idx].is_alive = not game_members[idx].is_alive
        update_game_ui()

    def adjust_role(role, delta):
        role_counts[role] = max(0, role_counts[role] + delta)
        update_role_ui()

    def register_member2(e):
        name_input = ft.TextField(label="名前", autofocus=True)
        def confirm(e):
            if name_input.value:
                registered_members.append(Player(name_input.value))
                dlg.open = False
                update_registered_ui()
                page.update()
        dlg = ft.AlertDialog(title=ft.Text("新規登録"), content=name_input, actions=[ft.TextButton("追加", on_click=confirm)])
        page.dialog = dlg
        dlg.open = True
        page.update()

    def register_member(e):
        # 名前入力フィールド（Enterキー押下でもconfirmが実行されるように設定）
        name_input = ft.TextField(
            label="名前を入力してください",
            autofocus=True,
            on_submit=lambda _: confirm(None)
        )

        def confirm(e):
            if name_input.value.strip():  # 空文字やスペースのみを除外
                # プレイヤーリストに追加
                registered_members.append(Player(name_input.value.strip()))
                # ダイアログを閉じる
                dlg.open = False
                # UIを更新
                update_registered_ui()
            else:
                # 名前が空の場合はエラー表示（任意）
                name_input.error_text = "名前を入力してください"
                page.update()

        # ダイアログの定義
        dlg = ft.AlertDialog(
            title=ft.Text("新規プレイヤー登録"),
            content=name_input,
            actions=[
                ft.TextButton("キャンセル", on_click=lambda _: close_dlg()),
                ft.ElevatedButton("追加", bgcolor=AppColors.SECONDARY, color=AppColors.TEXT, on_click=confirm),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        def close_dlg():
            dlg.open = False
            page.update()

        # ダイアログを表示
        # page.dialog = dlg
        # dlg.open = True
        page.open(dlg)
        page.update()

    def add_to_game(idx):
        if len(game_members) < 16 and registered_members[idx] not in game_members:
            game_members.append(registered_members[idx])
            update_game_ui()

    def remove_from_game(idx):
        game_members.pop(idx)
        update_game_ui()

    def delete_registered(idx):
        registered_members.pop(idx)
        update_registered_ui()

    def haieki(e):
        if not game_members: return
        roles = []
        for r, c in role_counts.items(): roles.extend([r]*c)
        mura = len(game_members) - len(roles)
        if mura < 0: return
        roles.extend(["村人"] * mura)
        random.shuffle(roles)
        for i, p in enumerate(game_members):
            p.role = roles[i]
            p.is_alive = True
        update_game_ui()

    # --- レイアウト構築 ---

    # 修正ポイント: カード自体のbgcolorを削除し、内部Containerのbgcolorで色を付ける
    sidebar = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("GAME SETTINGS", size=20, weight="bold", color=AppColors.PRIMARY),
                ft.Divider(),
                ft.ElevatedButton("プレイヤー登録", icon=ft.Icons.PERSON_ADD, on_click=register_member, width=250),
                ft.Text("役職構成", weight="bold", color=AppColors.TEXT_DIM),
                role_settings_view,
                ft.Container(expand=True), 
                ft.FilledButton("役職を配布", icon=ft.Icons.SHUFFLE, on_click=haieki, width=250, bgcolor=AppColors.SECONDARY),
                ft.OutlinedButton("全リセット", icon=ft.Icons.REFRESH, on_click=lambda _: page.update(), width=250),
            ]),
            padding=20,
            bgcolor=AppColors.SURFACE, # ここで背景色を指定
            border_radius=10,
        ),
        width=300,
    )

    main_table = ft.Column([
        ft.Text("ACTIVE PLAYERS", size=20, weight="bold", color=AppColors.PRIMARY),
        ft.Container(
            content=member_list_view,
            padding=10,
            bgcolor=AppColors.SURFACE,
            border_radius=10,
            height=120,
        ),
        ft.Text("ゲームメンバー一覧", size=14, color=AppColors.TEXT_DIM),
        game_member_list_view,
    ], expand=True, spacing=15)

    log_panel = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("PROGRESS", size=20, weight="bold", color=AppColors.PRIMARY),
                ft.Divider(),
                ft.ListView(
                    controls=[
                        ft.ExpansionTile(
                            title=ft.Text(f"Day {i}"),
                            controls=[
                                ft.Row([
                                    ft.TextButton("処刑", icon=ft.Icons.GAVEL),
                                    ft.TextButton("襲撃", icon=ft.Icons.BLOCK, icon_color=AppColors.ACCENT),
                                ])
                            ]
                        ) for i in range(1, 8)
                    ],
                    expand=True
                )
            ]),
            padding=20,
            bgcolor=AppColors.SURFACE, # ここで背景色を指定
            border_radius=10,
        ),
        width=300,
    )

    page.add(
        ft.Row([
            sidebar,
            main_table,
            log_panel
        ], expand=True, spacing=20)
    )

    update_role_ui()

ft.app(target=main)