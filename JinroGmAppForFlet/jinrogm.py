import flet as ft
import random
from dataclasses import dataclass, field
from typing import Optional

# ===== カラーテーマ =====
class C:
    BG       = "#1A1C1E"
    SURFACE  = "#2D3033"
    SURFACE2 = "#383B3F"
    PRIMARY  = "#A8DADC"
    SECONDARY = "#457B9D"
    ACCENT   = "#E63946"   # 人狼・警告（赤）
    JINRO_BG = "#4A1515"   # 人狼カード背景
    TEXT     = "#F1FAEE"
    TEXT_DIM = "#909090"
    ALIVE_BG = "#2C3E50"
    DEAD_BG  = "#181818"
    GREEN    = "#2E7D32"
    ORANGE   = "#E65100"
    BORDER   = "#4A4D52"

ROLES = ["人狼", "狂人", "占い師", "霊媒師", "狩人"]
WOLF_TEAM = {"人狼", "狂人"}
# (min, max) per role
ROLE_LIMITS = {
    "人狼": (1, 4),
    "狂人": (0, 3),
    "占い師": (0, 1),
    "霊媒師": (0, 2),
    "狩人": (0, 1),
}


class Player:
    def __init__(self, name: str = ""):
        self.name = name
        self.role = ""
        self.is_alive = True
        self.exclude_from_village = False  # 村カウント除外（✕マーク）
        self.otsuge = False               # お告げ済み（◯マーク）


@dataclass
class DayRecord:
    day: int
    syokei: Optional[int] = None    # 処刑対象 index
    uranai: Optional[int] = None    # 占い対象 index
    goei: Optional[int] = None      # 護衛対象 index
    syugeki: Optional[int] = None   # 襲撃対象 index
    tsuika: list = field(default_factory=list)  # 追加死亡 index リスト（最大3）


def main(page: ft.Page):
    page.title = "人狼GM ダッシュボード"
    page.bgcolor = C.BG
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.window_width = 1540
    page.window_height = 920

    # ===== 状態管理 =====
    registered_members: list[Player] = []
    game_members: list[Player] = []
    role_counts = {"人狼": 2, "狂人": 1, "占い師": 1, "霊媒師": 1, "狩人": 1}
    day_no = [0]
    goei_no = [-1]           # 前日護衛先 index
    uranai_list: list[int] = []  # 占い済み index
    syokei_idx = [-1]        # 今日の処刑予定 index（勝敗判定に使用）
    day_records: list[DayRecord] = []
    game_started = [False]

    # ===== UI コンテナ =====
    registered_list_view = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO)
    game_member_col = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO, expand=True)
    role_settings_col = ft.Column(spacing=4)
    progress_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

    # ===== ユーティリティ =====
    def snack(msg: str, color: str = C.TEXT):
        page.snack_bar = ft.SnackBar(ft.Text(msg, color=color), bgcolor=C.SURFACE2)
        page.snack_bar.open = True
        page.update()

    def close_dlg(dlg):
        page.pop_dialog()

    def judge_result() -> int:
        """0=継続, 1=村勝利, 2=人狼勝利"""
        wolves = 0
        village = 0
        for i, p in enumerate(game_members):
            if not p.is_alive:
                continue
            if i == syokei_idx[0]:  # 処刑予定者は除外してカウント
                continue
            if p.role == "人狼":
                wolves += 1
            elif not p.exclude_from_village:
                village += 1
        if wolves == 0:
            return 1   # 村陣営勝利
        if village <= wolves:
            return 2   # 人狼陣営勝利
        return 0

    def player_label(idx: Optional[int]) -> str:
        if idx is None or idx < 0:
            return "ー"
        p = game_members[idx]
        return f"{idx + 1}. {p.name}"

    # ===== 役職設定 UI =====
    def build_role_ui():
        role_settings_col.controls.clear()
        for role in ROLES:
            count = role_counts[role]
            color = C.ACCENT if role == "人狼" else (C.ORANGE if role == "狂人" else C.PRIMARY)
            role_settings_col.controls.append(
                ft.Row([
                    ft.Container(
                        ft.Text(role, size=13, color=color, weight="bold"),
                        expand=True,
                    ),
                    ft.IconButton(
                        ft.Icons.REMOVE_CIRCLE_OUTLINE, icon_color=C.TEXT_DIM, icon_size=18,
                        on_click=lambda e, r=role: adjust_role(r, -1),
                        disabled=game_started[0],
                        tooltip="減らす",
                    ),
                    ft.Text(str(count), width=26, text_align=ft.TextAlign.CENTER,
                            size=17, weight="bold", color=C.TEXT),
                    ft.IconButton(
                        ft.Icons.ADD_CIRCLE_OUTLINE, icon_color=C.TEXT_DIM, icon_size=18,
                        on_click=lambda e, r=role: adjust_role(r, 1),
                        disabled=game_started[0],
                        tooltip="増やす",
                    ),
                ], spacing=0)
            )

    def adjust_role(role: str, delta: int):
        lo, hi = ROLE_LIMITS[role]
        new_val = role_counts[role] + delta
        if lo <= new_val <= hi:
            role_counts[role] = new_val
        build_role_ui()
        page.update()

    # ===== 登録メンバー UI =====
    def build_registered_ui():
        registered_list_view.controls.clear()
        if not registered_members:
            registered_list_view.controls = [ft.Text("登録メンバーなし", color=C.TEXT_DIM, size=12)]
        else:
            chips = [
                ft.Chip(
                    label=ft.Text(p.name, color=C.TEXT, size=12),
                    bgcolor=C.SECONDARY,
                    on_click=lambda e, i=idx: add_to_game(i),
                    on_delete=lambda e, i=idx: delete_registered(i),
                    tooltip="クリックでゲームに追加",
                )
                for idx, p in enumerate(registered_members)
            ]
            registered_list_view.controls = [ft.Row(chips, wrap=True, spacing=4)]

    # ===== ゲームメンバー UI =====
    def build_game_member_ui():
        game_member_col.controls.clear()
        if not game_members:
            game_member_col.controls = [ft.Text("メンバー未追加", color=C.TEXT_DIM, size=12)]
            return

        # ヘッダー行
        if not game_started[0]:
            game_member_col.controls.append(
                ft.Container(
                    ft.Row([
                        ft.Text("#", width=28, size=11, color=C.TEXT_DIM),
                        ft.Text("名前", expand=2, size=11, color=C.TEXT_DIM),
                        ft.Text("役職", width=90, size=11, color=C.TEXT_DIM),
                        ft.Text("◯", width=36, size=11, color=C.TEXT_DIM, text_align=ft.TextAlign.CENTER, tooltip="お告げ"),
                        ft.Text("✕", width=36, size=11, color=C.TEXT_DIM, text_align=ft.TextAlign.CENTER, tooltip="村カウント除外"),
                        ft.Text("", width=36),
                    ], spacing=4),
                    padding=ft.padding.symmetric(horizontal=10, vertical=2),
                )
            )
        else:
            game_member_col.controls.append(
                ft.Container(
                    ft.Row([
                        ft.Text("#", width=28, size=11, color=C.TEXT_DIM),
                        ft.Text("名前", expand=2, size=11, color=C.TEXT_DIM),
                        ft.Text("役職", width=90, size=11, color=C.TEXT_DIM),
                        ft.Text("◯", width=22, size=11, color=C.TEXT_DIM, text_align=ft.TextAlign.CENTER),
                        ft.Text("✕", width=22, size=11, color=C.TEXT_DIM, text_align=ft.TextAlign.CENTER),
                        ft.Text("", width=70),
                    ], spacing=4),
                    padding=ft.padding.symmetric(horizontal=10, vertical=2),
                )
            )

        for i, p in enumerate(game_members):
            is_wolf = p.role == "人狼"
            role_color = (
                C.ACCENT if is_wolf
                else C.ORANGE if p.role == "狂人"
                else C.PRIMARY if p.role
                else C.TEXT_DIM
            )
            card_bg = (
                C.JINRO_BG if (is_wolf and game_started[0])
                else C.ALIVE_BG if p.is_alive
                else C.DEAD_BG
            )
            name_color = C.TEXT if p.is_alive else C.TEXT_DIM
            border_color = C.ACCENT if (is_wolf and game_started[0]) else (C.BORDER if p.is_alive else "transparent")

            role_display = p.role if p.role else "未設定"

            if not game_started[0]:
                row = ft.Row([
                    ft.Text(f"{i + 1}", width=28, weight="bold", color=C.TEXT_DIM, size=13),
                    ft.Text(p.name, expand=2, size=16, weight="bold", color=name_color,
                            no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.ElevatedButton(
                        role_display,
                        color=role_color,
                        bgcolor=C.SURFACE2,
                        on_click=lambda e, idx=i: open_role_popup(idx),
                        style=ft.ButtonStyle(
                            padding=ft.padding.symmetric(horizontal=6, vertical=2),
                            text_style=ft.TextStyle(size=12),
                        ),
                        width=90,
                    ),
                    ft.Tooltip(
                        message="お告げ済み（◯=占い先確定済み）",
                        content=ft.IconButton(
                            ft.Icons.VISIBILITY if p.otsuge else ft.Icons.VISIBILITY_OFF,
                            icon_color=C.PRIMARY if p.otsuge else C.TEXT_DIM,
                            icon_size=18,
                            on_click=lambda e, idx=i: toggle_otsuge(idx),
                        ),
                    ),
                    ft.Tooltip(
                        message="村カウント除外（✕=村人数にカウントしない）",
                        content=ft.IconButton(
                            ft.Icons.DO_NOT_DISTURB_ON if p.exclude_from_village else ft.Icons.PERSON,
                            icon_color=C.ORANGE if p.exclude_from_village else C.TEXT_DIM,
                            icon_size=18,
                            on_click=lambda e, idx=i: toggle_exclude(idx),
                        ),
                    ),
                    ft.IconButton(
                        ft.Icons.DELETE_OUTLINE, icon_color=C.TEXT_DIM, icon_size=18,
                        on_click=lambda e, idx=i: remove_from_game(idx),
                        tooltip="ゲームから除外",
                    ),
                ], spacing=4)
            else:
                row = ft.Row([
                    ft.Text(f"{i + 1}", width=28, weight="bold", color=C.TEXT_DIM, size=13),
                    ft.Text(p.name, expand=2, size=16, weight="bold", color=name_color,
                            no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Container(
                        ft.Text(role_display, size=12, color=role_color),
                        padding=ft.padding.symmetric(horizontal=6, vertical=3),
                        bgcolor=C.SURFACE2,
                        border_radius=4,
                        width=90,
                    ),
                    ft.Text(
                        "◯" if p.otsuge else "", width=22,
                        color=C.PRIMARY, size=14, text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "✕" if p.exclude_from_village else "", width=22,
                        color=C.ORANGE, size=14, text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Row([
                        ft.Tooltip(
                            message="生死を切り替え",
                            content=ft.IconButton(
                                ft.Icons.PERSON if p.is_alive else ft.Icons.PERSON_OFF,
                                icon_color=C.GREEN if p.is_alive else C.ACCENT,
                                icon_size=20,
                                on_click=lambda e, idx=i: toggle_alive(idx),
                            ),
                        ),
                        ft.Tooltip(
                            message="名前を拡大表示",
                            content=ft.IconButton(
                                ft.Icons.ZOOM_IN, icon_color=C.TEXT_DIM, icon_size=20,
                                on_click=lambda e, idx=i: show_name_large(idx),
                            ),
                        ),
                    ], spacing=0, width=70),
                ], spacing=4)

            game_member_col.controls.append(
                ft.Container(
                    content=row,
                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                    bgcolor=card_bg,
                    border_radius=8,
                    border=ft.border.all(1, border_color),
                    animate=ft.animation.Animation(150),
                )
            )

    # ===== 進行パネル UI =====
    def build_progress_ui():
        progress_col.controls.clear()
        if not game_started[0]:
            progress_col.controls = [ft.Text("ゲーム開始後に表示されます", color=C.TEXT_DIM, size=12)]
            return
        for rec in day_records:
            is_current = (rec.day == day_no[0])
            progress_col.controls.append(_build_day_card(rec, is_current))

    def _build_day_card(rec: DayRecord, is_current: bool) -> ft.Container:
        day = rec.day

        def action_btn(label: str, current_idx: Optional[int], click_fn, show_role: bool = False):
            p = game_members[current_idx] if (current_idx is not None and current_idx >= 0) else None
            is_wolf = p and p.role == "人狼"
            txt = player_label(current_idx)
            if show_role and p and p.role:
                txt += f"  [{p.role}]"
            return ft.Row([
                ft.Text(label, size=11, color=C.TEXT_DIM, width=62),
                ft.ElevatedButton(
                    txt,
                    color=C.ACCENT if is_wolf else C.TEXT,
                    bgcolor=C.JINRO_BG if is_wolf else C.SURFACE2,
                    on_click=click_fn if is_current else None,
                    disabled=not is_current,
                    expand=True,
                    style=ft.ButtonStyle(
                        padding=ft.padding.symmetric(horizontal=6, vertical=3),
                        text_style=ft.TextStyle(size=11),
                    ),
                ),
            ], spacing=4)

        def tsuika_btn(slot: int):
            idx_val = rec.tsuika[slot] if slot < len(rec.tsuika) else None
            return ft.Row([
                ft.Text(f"追加死亡{slot+1}", size=11, color=C.TEXT_DIM, width=62),
                ft.ElevatedButton(
                    player_label(idx_val),
                    bgcolor=C.SURFACE2,
                    on_click=(lambda e, s=slot: open_tsuika_popup(rec, s)) if is_current else None,
                    disabled=not is_current,
                    expand=True,
                    style=ft.ButtonStyle(
                        padding=ft.padding.symmetric(horizontal=6, vertical=3),
                        text_style=ft.TextStyle(size=11),
                    ),
                ),
            ], spacing=4)

        has_uranai_alive = any(p.is_alive and p.role == "占い師" for p in game_members)
        has_goei_alive = any(p.is_alive and p.role == "狩人" for p in game_members)

        card_controls = [
            ft.Text(
                f"{'▶ ' if is_current else ''}Day {day}",
                size=14, weight="bold",
                color=C.PRIMARY if is_current else C.TEXT_DIM,
            ),
            action_btn("処刑者",  rec.syokei,  lambda e: open_selection_popup("処刑者選択", rec, "syokei"),  show_role=True),
            action_btn("占い先",  rec.uranai,  lambda e: open_selection_popup("占い先選択", rec, "uranai"))
            if (has_uranai_alive or rec.uranai is not None or not is_current) else
            ft.Row([ft.Text("占い先", size=11, color=C.TEXT_DIM, width=62),
                    ft.Text("占い師生存なし", size=11, color=C.TEXT_DIM)], spacing=4),
            action_btn("護衛先",  rec.goei,    lambda e: open_selection_popup("護衛先選択", rec, "goei"))
            if (has_goei_alive or rec.goei is not None or not is_current) else
            ft.Row([ft.Text("護衛先", size=11, color=C.TEXT_DIM, width=62),
                    ft.Text("狩人生存なし", size=11, color=C.TEXT_DIM)], spacing=4),
            action_btn("襲撃先",  rec.syugeki, lambda e: open_selection_popup("襲撃先選択", rec, "syugeki")),
            tsuika_btn(0),
            tsuika_btn(1),
            tsuika_btn(2),
        ]

        if is_current:
            card_controls.append(
                ft.ElevatedButton(
                    "翌朝へ進む →",
                    icon=ft.Icons.ARROW_FORWARD,
                    bgcolor=C.GREEN, color=C.TEXT,
                    on_click=lambda e: confirm_next_day(),
                )
            )

        return ft.Container(
            content=ft.Column(card_controls, spacing=5),
            padding=10,
            bgcolor=C.SURFACE2 if is_current else C.SURFACE,
            border_radius=10,
            border=ft.border.all(1, C.PRIMARY if is_current else C.BORDER),
        )

    # ===== ポップアップ: 役職選択 =====
    def open_role_popup(idx: int):
        p = game_members[idx]

        def select(role: str):
            p.role = role
            p.exclude_from_village = (role == "人狼")
            page.pop_dialog()
            build_game_member_ui()
            page.update()

        custom_field = ft.TextField(label="カスタム役職名", dense=True, autofocus=False)

        def select_custom(e):
            role = custom_field.value.strip()
            if role:
                select(role)

        btns = []
        for role in ROLES:
            c = C.ACCENT if role == "人狼" else (C.ORANGE if role == "狂人" else C.PRIMARY)
            btns.append(
                ft.ElevatedButton(
                    role, color=c, bgcolor=C.SURFACE2,
                    on_click=lambda e, r=role: select(r), width=220,
                )
            )
        btns.append(ft.ElevatedButton("村人（明示）", bgcolor=C.SURFACE2, on_click=lambda e: select("村人"), width=220))
        btns.append(ft.ElevatedButton("なし（クリア）", bgcolor=C.SURFACE2, on_click=lambda e: select(""), width=220))

        dlg = ft.AlertDialog(
            title=ft.Text(f"{p.name} の役職を選択"),
            content=ft.Column(
                btns + [ft.Divider(), custom_field,
                        ft.ElevatedButton("カスタムで選択", on_click=select_custom, width=220)],
                spacing=6, tight=True, scroll=ft.ScrollMode.AUTO, height=380,
            ),
            actions=[ft.TextButton("閉じる", on_click=lambda e: close_dlg(dlg))],
        )
        page.show_dialog(dlg)

    # ===== ポップアップ: 処刑/占い/護衛/襲撃 選択 =====
    def open_selection_popup(title: str, rec: DayRecord, target_type: str):
        options = []
        for idx, p in enumerate(game_members):
            if not p.is_alive:
                continue
            # 除外ルール
            if target_type == "uranai":
                if p.role == "占い師":
                    continue
                if idx in uranai_list:
                    continue
                if rec.syokei == idx:
                    continue
            elif target_type == "goei":
                if p.role == "狩人":
                    continue
                if goei_no[0] == idx:  # 前日護衛先は選べない
                    continue
                if rec.syokei == idx:
                    continue
            elif target_type == "syugeki":
                if p.role == "人狼":
                    continue
                if rec.syokei == idx:
                    continue

            is_wolf = p.role == "人狼"
            lbl = f"{idx + 1}. {p.name}"
            if target_type == "syokei" and p.role:
                lbl += f"  [{p.role}]"

            def make_handler(i=idx):
                def handler(e):
                    setattr(rec, target_type, i)
                    if target_type == "syokei":
                        syokei_idx[0] = i
                    page.pop_dialog()
                    build_progress_ui()
                    page.update()
                    if target_type == "syokei":
                        result = judge_result()
                        if result == 1:
                            show_result_popup("村人陣営の勝利！", "全ての人狼が処刑されました")
                        elif result == 2:
                            show_result_popup("人狼陣営の勝利！", "人狼の数が村人以上になりました")
                return handler

            options.append(
                ft.ElevatedButton(
                    lbl,
                    color=C.ACCENT if is_wolf else C.TEXT,
                    bgcolor=C.JINRO_BG if is_wolf else C.ALIVE_BG,
                    on_click=make_handler(),
                    width=300,
                )
            )

        def select_none(e):
            setattr(rec, target_type, None)
            if target_type == "syokei":
                syokei_idx[0] = -1
            page.pop_dialog()
            build_progress_ui()
            page.update()

        options.append(ft.ElevatedButton("ー（なし/スキップ）", bgcolor=C.SURFACE2, on_click=select_none, width=300))

        dlg = ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Column(
                options if options else [ft.Text("対象者がいません", color=C.TEXT_DIM)],
                spacing=6, scroll=ft.ScrollMode.AUTO, height=min(60 * len(options) + 40, 480),
            ),
            actions=[ft.TextButton("閉じる", on_click=lambda e: close_dlg(dlg))],
        )
        page.show_dialog(dlg)

    # ===== ポップアップ: 追加死亡 =====
    def open_tsuika_popup(rec: DayRecord, slot: int):
        other_slots = [rec.tsuika[s] for s in range(len(rec.tsuika)) if s != slot and s < len(rec.tsuika)]
        options = []

        for idx, p in enumerate(game_members):
            if not p.is_alive:
                continue
            if idx == rec.syokei or idx == rec.syugeki:
                continue
            if idx in other_slots:
                continue

            def make_handler(i=idx):
                def handler(e):
                    while len(rec.tsuika) <= slot:
                        rec.tsuika.append(None)
                    rec.tsuika[slot] = i
                    page.pop_dialog()
                    build_progress_ui()
                    page.update()
                return handler

            options.append(
                ft.ElevatedButton(
                    f"{idx + 1}. {p.name}",
                    bgcolor=C.ALIVE_BG, color=C.TEXT,
                    on_click=make_handler(), width=300,
                )
            )

        def select_none(e):
            while len(rec.tsuika) <= slot:
                rec.tsuika.append(None)
            rec.tsuika[slot] = None
            page.pop_dialog()
            build_progress_ui()
            page.update()

        options.append(ft.ElevatedButton("ー（なし）", bgcolor=C.SURFACE2, on_click=select_none, width=300))

        dlg = ft.AlertDialog(
            title=ft.Text(f"追加死亡 {slot + 1} の選択"),
            content=ft.Column(options, spacing=6, scroll=ft.ScrollMode.AUTO, height=min(60 * len(options) + 40, 480)),
            actions=[ft.TextButton("閉じる", on_click=lambda e: close_dlg(dlg))],
        )
        page.show_dialog(dlg)

    # ===== 翌朝へ進む =====
    def confirm_next_day():
        rec = day_records[-1]

        # 占い師/狩人が処刑済みなのに占い先/護衛先が設定されている場合は警告
        if (rec.syokei is not None
                and game_members[rec.syokei].role == "占い師"
                and rec.uranai is not None):
            snack("占い師が処刑されています。占い先を「なし」にしてください。", C.ACCENT)
            return
        if (rec.syokei is not None
                and game_members[rec.syokei].role == "狩人"
                and rec.goei is not None):
            snack("狩人が処刑されています。護衛先を「なし」にしてください。", C.ACCENT)
            return

        def do_next(e):
            page.pop_dialog()
            _execute_next_day(rec)

        dlg = ft.AlertDialog(
            title=ft.Text("翌朝へ進みますか？"),
            content=ft.Text("現在の選択を確定して次の日に進みます。"),
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: close_dlg(dlg)),
                ft.ElevatedButton("進む", bgcolor=C.GREEN, color=C.TEXT, on_click=do_next),
            ],
        )
        page.show_dialog(dlg)

    def _execute_next_day(rec: DayRecord):
        # 処刑
        if rec.syokei is not None:
            game_members[rec.syokei].is_alive = False

        # 占い先を履歴に追加（毎晩記録）
        if rec.uranai is not None:
            uranai_list.append(rec.uranai)

        # 護衛先を記録
        if rec.goei is not None:
            goei_no[0] = rec.goei
        else:
            goei_no[0] = -1

        # 襲撃（護衛と一致していたら無効）
        attack_killed = False
        if rec.syugeki is not None and rec.syugeki != rec.goei:
            game_members[rec.syugeki].is_alive = False
            attack_killed = True

        # 追加死亡
        for ti in rec.tsuika:
            if ti is not None:
                game_members[ti].is_alive = False

        syokei_idx[0] = -1
        day_no[0] += 1

        # 犠牲者メッセージ
        if rec.syugeki is not None and not attack_killed:
            night_msg = "昨晩の犠牲者はいませんでした！（護衛成功）"
        elif rec.syugeki is not None:
            night_msg = f"昨晩の犠牲者は【{game_members[rec.syugeki].name}】さんでした！"
        else:
            night_msg = "昨晩の犠牲者はいませんでした！"

        # 勝敗判定
        result = judge_result()
        build_game_member_ui()

        if result == 1:
            build_progress_ui()
            page.update()
            show_result_popup("村人陣営の勝利！🎉", night_msg + "\n\n全ての人狼が倒されました！")
            return
        if result == 2:
            build_progress_ui()
            page.update()
            show_result_popup("人狼陣営の勝利！🐺", night_msg + "\n\n人狼の数が村人以上になりました！")
            return

        if day_no[0] <= 10:
            day_records.append(DayRecord(day=day_no[0]))
            snack(night_msg)
        else:
            snack("これ以上アプリでは進行できません。")

        build_progress_ui()
        page.update()

    # ===== ポップアップ: 名前拡大表示 =====
    def show_name_large(idx: int):
        p = game_members[idx]
        dlg = ft.AlertDialog(
            content=ft.Column([
                ft.Text(str(idx + 1), size=130, weight="bold", color=C.TEXT_DIM,
                        text_align=ft.TextAlign.CENTER),
                ft.Text(p.name, size=80, weight="bold", color=C.TEXT,
                        text_align=ft.TextAlign.CENTER),
                ft.Text(p.role if p.role else "", size=30, color=(
                    C.ACCENT if p.role == "人狼" else C.ORANGE if p.role == "狂人" else C.PRIMARY
                ), text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            actions=[ft.TextButton("閉じる", on_click=lambda e: close_dlg(dlg))],
            bgcolor=C.SURFACE2,
        )
        page.show_dialog(dlg)

    def show_result_popup(title: str, detail: str = ""):
        dlg = ft.AlertDialog(
            title=ft.Text(title, size=22, weight="bold"),
            content=ft.Text(detail, size=14) if detail else None,
            actions=[
                ft.ElevatedButton("閉じる", bgcolor=C.GREEN, color=C.TEXT,
                                  on_click=lambda e: close_dlg(dlg)),
            ],
            bgcolor=C.SURFACE2,
        )
        page.show_dialog(dlg)

    # ===== ロジック: 登録/追加/削除 =====
    def register_member(e):
        name_field = ft.TextField(label="プレイヤー名", autofocus=True, on_submit=lambda _: confirm(None))

        def confirm(e):
            name = name_field.value.strip()
            if not name:
                name_field.error_text = "名前を入力してください"
                page.update()
                return
            if any(p.name == name for p in registered_members):
                name_field.error_text = "同じ名前が既に登録されています"
                page.update()
                return
            registered_members.append(Player(name))
            page.pop_dialog()
            build_registered_ui()
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("プレイヤー登録"),
            content=name_field,
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: close_dlg(dlg)),
                ft.ElevatedButton("追加", bgcolor=C.SECONDARY, color=C.TEXT, on_click=confirm),
            ],
        )
        page.show_dialog(dlg)

    def add_to_game(idx: int):
        if game_started[0]:
            snack("ゲーム開始後は追加できません", C.ACCENT)
            return
        if len(game_members) >= 16:
            snack("最大16人まで追加できます", C.ACCENT)
            return
        p = registered_members[idx]
        if any(gp.name == p.name for gp in game_members):
            snack(f"「{p.name}」は既に追加されています")
            return
        game_members.append(Player(p.name))
        build_game_member_ui()
        page.update()

    def remove_from_game(idx: int):
        if game_started[0]:
            return
        game_members.pop(idx)
        build_game_member_ui()
        page.update()

    def delete_registered(idx: int):
        registered_members.pop(idx)
        build_registered_ui()
        page.update()

    def toggle_alive(idx: int):
        game_members[idx].is_alive = not game_members[idx].is_alive
        build_game_member_ui()
        page.update()

    def toggle_otsuge(idx: int):
        game_members[idx].otsuge = not game_members[idx].otsuge
        build_game_member_ui()
        page.update()

    def toggle_exclude(idx: int):
        p = game_members[idx]
        if p.role == "人狼":
            return  # 人狼は常に村カウント除外
        p.exclude_from_village = not p.exclude_from_village
        build_game_member_ui()
        page.update()

    # ===== ロジック: 自動配役 =====
    def auto_assign(e):
        if game_started[0]:
            snack("ゲーム開始後は変更できません", C.ACCENT)
            return
        total = sum(role_counts.values())
        if len(game_members) < total:
            snack(f"メンバーが足りません（設定: {total}人分、現在: {len(game_members)}人）", C.ACCENT)
            return
        # ロール一覧生成
        roles = []
        for r, c in role_counts.items():
            roles.extend([r] * c)
        village_cnt = len(game_members) - len(roles)
        roles.extend(["村人"] * village_cnt)
        random.shuffle(roles)
        for p, role in zip(game_members, roles):
            p.role = role
            p.is_alive = True
            p.otsuge = False
            p.exclude_from_village = (role == "人狼")
        build_game_member_ui()
        page.update()

    def auto_otsuge(e):
        """人狼・占い師以外からランダムに1人へお告げを設定"""
        if game_started[0]:
            snack("ゲーム開始後は変更できません", C.ACCENT)
            return
        for p in game_members:
            p.otsuge = False
        candidates = [p for p in game_members if p.role not in ("人狼", "占い師")]
        if candidates:
            random.choice(candidates).otsuge = True
        build_game_member_ui()
        page.update()

    # ===== ロジック: ゲーム開始 =====
    def game_start(e):
        if game_started[0]:
            snack("既にゲームは開始されています", C.ACCENT)
            return
        if len(game_members) < 4:
            snack("最低4人必要です", C.ACCENT)
            return
        wolf_cnt = sum(1 for p in game_members if p.role == "人狼")
        if wolf_cnt == 0:
            snack("人狼を最低1人設定してください", C.ACCENT)
            return

        def do_start(e):
            page.pop_dialog()
            game_started[0] = True
            day_no[0] = 1
            # ゲーム開始時のお告げ済みを占い履歴に登録
            for i, p in enumerate(game_members):
                if p.otsuge:
                    uranai_list.append(i)
            day_records.clear()
            day_records.append(DayRecord(day=1))
            build_role_ui()
            build_game_member_ui()
            build_progress_ui()
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("ゲームを開始しますか？"),
            content=ft.Text("役職・お告げの設定を確認してから開始してください。"),
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: close_dlg(dlg)),
                ft.ElevatedButton("開始", bgcolor=C.GREEN, color=C.TEXT, on_click=do_start),
            ],
        )
        page.show_dialog(dlg)

    # ===== ロジック: リセット =====
    def reset_game(e):
        """ゲーム進行をリセット（メンバー・役職は保持）"""
        def do_reset(e):
            page.pop_dialog()
            game_started[0] = False
            day_no[0] = 0
            goei_no[0] = -1
            syokei_idx[0] = -1
            uranai_list.clear()
            day_records.clear()
            for p in game_members:
                p.is_alive = True
                p.otsuge = False
            build_role_ui()
            build_game_member_ui()
            build_progress_ui()
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("ゲームをリセット"),
            content=ft.Text("ゲームの進行状況をリセットします。\nメンバーと役職設定は保持されます。"),
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: close_dlg(dlg)),
                ft.ElevatedButton("リセット", bgcolor=C.ORANGE, color=C.TEXT, on_click=do_reset),
            ],
        )
        page.show_dialog(dlg)

    def reset_members(e):
        """ゲームメンバーのみリセット"""
        def do_reset(e):
            page.pop_dialog()
            game_started[0] = False
            day_no[0] = 0
            goei_no[0] = -1
            syokei_idx[0] = -1
            uranai_list.clear()
            day_records.clear()
            game_members.clear()
            build_role_ui()
            build_game_member_ui()
            build_progress_ui()
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("ゲームメンバーをリセット"),
            content=ft.Text("ゲームメンバーとゲーム進行をリセットします。\n登録メンバー一覧は保持されます。"),
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: close_dlg(dlg)),
                ft.ElevatedButton("リセット", bgcolor=C.ORANGE, color=C.TEXT, on_click=do_reset),
            ],
        )
        page.show_dialog(dlg)

    def full_reset(e):
        """全データをリセット"""
        def do_reset(e):
            page.pop_dialog()
            game_started[0] = False
            day_no[0] = 0
            goei_no[0] = -1
            syokei_idx[0] = -1
            uranai_list.clear()
            day_records.clear()
            registered_members.clear()
            game_members.clear()
            build_role_ui()
            build_registered_ui()
            build_game_member_ui()
            build_progress_ui()
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("全データをリセット"),
            content=ft.Text("登録メンバーとゲームデータを全て削除します。"),
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: close_dlg(dlg)),
                ft.ElevatedButton("全リセット", bgcolor=C.ACCENT, color=C.TEXT, on_click=do_reset),
            ],
        )
        page.show_dialog(dlg)

    # ===== レイアウト構築 =====

    sidebar = ft.Container(
        content=ft.Column([
            ft.Text("SETTINGS", size=15, weight="bold", color=C.PRIMARY),
            ft.Divider(color=C.BORDER, height=8),
            ft.ElevatedButton(
                "プレイヤー登録", icon=ft.Icons.PERSON_ADD,
                on_click=register_member, width=240,
                bgcolor=C.SECONDARY, color=C.TEXT,
            ),
            ft.Text("役職構成", size=12, color=C.TEXT_DIM),
            role_settings_col,
            ft.Divider(color=C.BORDER, height=8),
            ft.ElevatedButton(
                "自動配役", icon=ft.Icons.SHUFFLE,
                on_click=auto_assign, width=240,
                bgcolor=C.SECONDARY, color=C.TEXT,
            ),
            ft.ElevatedButton(
                "自動お告げ設定", icon=ft.Icons.VISIBILITY,
                on_click=auto_otsuge, width=240,
            ),
            ft.Divider(color=C.BORDER, height=8),
            ft.ElevatedButton(
                "ゲーム開始", icon=ft.Icons.PLAY_ARROW,
                on_click=game_start, width=240,
                bgcolor=C.GREEN, color=C.TEXT,
            ),
            ft.Divider(color=C.BORDER, height=8),
            ft.ElevatedButton("ゲームリセット", icon=ft.Icons.REFRESH, on_click=reset_game, width=240),
            ft.ElevatedButton("メンバーリセット", icon=ft.Icons.GROUP_REMOVE, on_click=reset_members, width=240),
            ft.ElevatedButton(
                "全リセット", icon=ft.Icons.DELETE_FOREVER,
                on_click=full_reset, width=240, color=C.ACCENT,
            ),
        ], spacing=6, scroll=ft.ScrollMode.AUTO),
        padding=14,
        bgcolor=C.SURFACE,
        border_radius=10,
        width=270,
    )

    center_panel = ft.Container(
        content=ft.Column([
            ft.Text("PLAYERS", size=15, weight="bold", color=C.PRIMARY),
            ft.Text("登録メンバー（クリックで追加）", size=11, color=C.TEXT_DIM),
            ft.Container(
                content=registered_list_view,
                padding=8,
                bgcolor=C.SURFACE2,
                border_radius=8,
                height=90,
            ),
            ft.Text("ゲームメンバー", size=11, color=C.TEXT_DIM),
            ft.Container(
                content=game_member_col,
                expand=True,
            ),
        ], spacing=8, expand=True),
        padding=14,
        bgcolor=C.SURFACE,
        border_radius=10,
        expand=True,
    )

    right_panel = ft.Container(
        content=ft.Column([
            ft.Text("PROGRESS", size=15, weight="bold", color=C.PRIMARY),
            ft.Divider(color=C.BORDER, height=8),
            progress_col,
        ], spacing=6, expand=True),
        padding=14,
        bgcolor=C.SURFACE,
        border_radius=10,
        width=330,
    )

    page.add(
        ft.Container(
            content=ft.Row([sidebar, center_panel, right_panel], spacing=10, expand=True),
            padding=10,
            expand=True,
        )
    )

    # 初期描画
    build_role_ui()
    build_registered_ui()
    build_game_member_ui()
    build_progress_ui()


ft.app(target=main)
