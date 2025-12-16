"""
손처럼 클릭 GUI 애플리케이션
"""
import os
from pathlib import Path
import threading
import customtkinter as ctk
from PIL import Image
from pynput.mouse import Button, Controller as MouseController
import keyboard  # 글로벌 단축키
import tkinter.messagebox as messagebox

from autoclicker.config import load_config, save_config
from autoclicker.clicker import Clicker
from autoclicker.updater import Updater, check_update_async
from autoclicker.version import __version__


# appearance_mode는 설정에서 로드한 후 설정됨
ctk.set_default_color_theme("blue")


class AutoClickerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("띵타이쿤 일꾼용")
        self.geometry("550x650")
        self.minsize(400, 500)  # 최소 크기 설정 (너비, 높이)
        self.resizable(True, True)
        

        # 아이콘 설정
        self._set_icon()

        self.mouse = MouseController()
        self.config = load_config()
        
        # appearance_mode 설정 적용
        appearance_mode = self.config.get("appearance_mode", "dark")
        ctk.set_appearance_mode(appearance_mode)

        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._running = False
        self._click_thread: threading.Thread | None = None

        self._hotkey_start = None
        self._hotkey_stop = None

        # 단축키 설정 중 상태
        self._setting_hotkey = None

        # 현재 화면 상태
        self._current_page = "menu"  # "menu", "autoclicker", "settings"
        self._settings_dirty = False
        self._settings_snapshot = {}
        self._suppress_dirty = False

        # 헤더 로고 이미지 (아이콘과 텍스트 간격 최소화)
        self.logo_image = self._load_logo_image()

        self.create_widgets()
        self.setup_hotkeys()
        
        # 업데이트 체크 (백그라운드)
        self.check_for_updates()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _set_icon(self):
        """윈도우 아이콘 설정"""
        base_dir = Path(__file__).resolve().parent.parent
        assets_dir = base_dir / "assets"

        icon_paths = [
            assets_dir / "icon.ico",
            assets_dir / "app.ico",
            assets_dir / "icon.png",
            assets_dir / "app.png",
        ]

        for icon_path in icon_paths:
            if icon_path.exists():
                try:
                    self.iconbitmap(str(icon_path))
                    break
                except Exception:
                    continue

    def _load_logo_image(self):
        """헤더 로고 이미지 로드"""
        base_dir = Path(__file__).resolve().parent.parent
        assets_dir = base_dir / "assets"
        logo_candidates = [
            assets_dir / "icon.png",
            assets_dir / "app.png",
        ]

        for logo_path in logo_candidates:
            if logo_path.exists():
                try:
                    # 작은 사이즈로 축소하여 텍스트와 자연스럽게 붙임
                    img = Image.open(logo_path).resize((28, 28))
                    return ctk.CTkImage(light_image=img, dark_image=img, size=(28, 28))
                except Exception:
                    continue
        return None

    # ---------------- UI ----------------
    def create_widgets(self):
        # 상단 헤더 (타이틀 + 설정 버튼)
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 5))

        title_area = ctk.CTkFrame(header, fg_color="transparent")
        title_area.pack(side="left", padx=10)

        if self.logo_image:
            ctk.CTkLabel(
                title_area,
                image=self.logo_image,
                text="",
                width=32,
            ).pack(side="left", padx=(0, 6))

        self.title_label = ctk.CTkLabel(
            title_area,
            text="띵타이쿤 일꾼용",
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        self.title_label.pack(side="left")

        # 설정 버튼 (메인 화면일 때만 표시)
        self.settings_btn = ctk.CTkButton(
            header,
            text="⚙️",
            width=30,
            height=30,
            font=ctk.CTkFont(size=18),
            fg_color="transparent",
            hover_color="#3a3a3a",
            text_color=("black", "white"),  # 라이트 모드: 검정, 다크 모드: 흰색
            command=self.toggle_settings,
        )
        self.settings_btn.pack(side="right", padx=5)

        # 뒤로가기 버튼 (메뉴가 아닐 때만 표시)
        self.back_btn = ctk.CTkButton(
            header,
            text="←",
            width=30,
            height=30,
            font=ctk.CTkFont(size=20),
            fg_color="transparent",
            hover_color="#3a3a3a",
            text_color=("black", "white"),  # 라이트 모드: 검정, 다크 모드: 흰색
            command=self.go_back,
        )
        self.back_btn.pack(side="right", padx=5)
        self.back_btn.pack_forget()  # 처음엔 숨김

        # 메인 메뉴 페이지 컨테이너
        self.menu_page = ctk.CTkFrame(self, fg_color="transparent")
        self.menu_page.pack(fill="both", expand=True, padx=25, pady=15)

        # 오토마우스 페이지 컨테이너 (처음엔 숨김)
        self.autoclicker_page = ctk.CTkFrame(self, fg_color="transparent")

        # 설정 페이지 컨테이너 (처음엔 숨김)
        self.settings_page = ctk.CTkFrame(self, fg_color="transparent")

        self._create_main_menu_page()
        self._create_autoclicker_page()
        self._create_settings_page()

    def _get_card_colors(self):
        """현재 테마에 맞는 카드 색상 반환"""
        current_mode = ctk.get_appearance_mode()
        if current_mode == "Light":
            return {
                "active": "#e3f2fd",  # 밝은 파란색
                "active_hover": "#bbdefb",  # 더 밝은 파란색
                "inactive": "#f5f5f5",  # 밝은 회색
                "inactive_hover": "#e0e0e0",  # 약간 어두운 회색
            }
        else:  # Dark
            return {
                "active": "#2c3e50",  # 다크 그레이
                "active_hover": "#34495e",  # 더 밝은 다크 그레이
                "inactive": "#34495e",  # 다크 그레이
                "inactive_hover": "#3d566e",  # 더 밝은 다크 그레이
            }

    def _create_main_menu_page(self):
        """메인 메뉴 페이지 UI 생성 (카드 형태)"""
        # 카드 컨테이너 (스크롤 가능)
        cards_frame = ctk.CTkScrollableFrame(self.menu_page, fg_color="transparent")
        cards_frame.pack(fill="both", expand=True, padx=20, pady=(20, 0))

        card_colors = self._get_card_colors()

        # 오토마우스 카드
        autoclicker_card = ctk.CTkFrame(
            cards_frame,
            fg_color=card_colors["inactive"],
            corner_radius=15,
            height=150
        )
        autoclicker_card.pack(fill="x", pady=15, padx=10)
        autoclicker_card.pack_propagate(False)
        autoclicker_card.bind("<Button-1>", lambda e: self.navigate_to_page("autoclicker"))
        
        def on_enter_active(e):
            colors = self._get_card_colors()
            autoclicker_card.configure(fg_color=colors["inactive_hover"])
            autoclicker_card._is_hovered = True
        def on_leave_active(e):
            colors = self._get_card_colors()
            autoclicker_card.configure(fg_color=colors["inactive"])
            autoclicker_card._is_hovered = False
        
        autoclicker_card._is_hovered = False
        autoclicker_card.bind("<Enter>", on_enter_active)
        autoclicker_card.bind("<Leave>", on_leave_active)
        autoclicker_card.configure(cursor="hand2")
        
        # 카드 참조 저장 (테마 변경 시 업데이트용)
        if not hasattr(self, '_menu_cards'):
            self._menu_cards = []
        self._menu_cards.append({"card": autoclicker_card, "type": "inactive"})

        autoclicker_content = ctk.CTkFrame(autoclicker_card, fg_color="transparent")
        autoclicker_content.pack(fill="both", expand=True, padx=25, pady=20)
        autoclicker_content.bind("<Button-1>", lambda e: self.navigate_to_page("autoclicker"))
        autoclicker_content.bind("<Enter>", on_enter_active)
        autoclicker_content.bind("<Leave>", on_leave_active)
        autoclicker_content.configure(cursor="hand2")

        def bind_events_to_children(parent):
            """모든 자식 위젯에 클릭 및 hover 이벤트 바인딩"""
            for child in parent.winfo_children():
                child.bind("<Button-1>", lambda e: self.navigate_to_page("autoclicker"))
                child.bind("<Enter>", on_enter_active)
                child.bind("<Leave>", on_leave_active)
                if hasattr(child, 'configure'):
                    try:
                        child.configure(cursor="hand2")
                    except:
                        pass
                bind_events_to_children(child)

        ctk.CTkLabel(
            autoclicker_content,
            text="🖱️",
            font=ctk.CTkFont(size=40)
        ).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(
            autoclicker_content,
            text="오토마우스",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(anchor="w", pady=(0, 5))

        ctk.CTkLabel(
            autoclicker_content,
            text="자동으로 마우스를 클릭합니다",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        ).pack(anchor="w")

        bind_events_to_children(autoclicker_card)

        # 매크로 카드 (준비 중)
        macro_card = ctk.CTkFrame(
            cards_frame,
            fg_color=card_colors["inactive"],
            corner_radius=15,
            height=150
        )
        macro_card.pack(fill="x", pady=15, padx=10)
        macro_card.pack_propagate(False)
        
        def on_enter_inactive(e):
            colors = self._get_card_colors()
            macro_card.configure(fg_color=colors["inactive_hover"])
            macro_card._is_hovered = True
        def on_leave_inactive(e):
            colors = self._get_card_colors()
            macro_card.configure(fg_color=colors["inactive"])
            macro_card._is_hovered = False
        
        macro_card._is_hovered = False
        macro_card.bind("<Enter>", on_enter_inactive)
        macro_card.bind("<Leave>", on_leave_inactive)
        self._menu_cards.append({"card": macro_card, "type": "inactive"})

        macro_content = ctk.CTkFrame(macro_card, fg_color="transparent")
        macro_content.pack(fill="both", expand=True, padx=25, pady=20)
        macro_content.bind("<Enter>", on_enter_inactive)
        macro_content.bind("<Leave>", on_leave_inactive)

        ctk.CTkLabel(
            macro_content,
            text="⌨️",
            font=ctk.CTkFont(size=40)
        ).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(
            macro_content,
            text="매크로",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(anchor="w", pady=(0, 5))

        ctk.CTkLabel(
            macro_content,
            text="준비 중입니다",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        ).pack(anchor="w")

        def bind_hover_to_children_macro(parent):
            """매크로 카드의 모든 자식 위젯에 hover 이벤트 바인딩"""
            for child in parent.winfo_children():
                child.bind("<Enter>", on_enter_inactive)
                child.bind("<Leave>", on_leave_inactive)
                bind_hover_to_children_macro(child)
        
        bind_hover_to_children_macro(macro_card)

        # 카드 3 (준비 중)
        card3 = ctk.CTkFrame(
            cards_frame,
            fg_color=card_colors["inactive"],
            corner_radius=15,
            height=150
        )
        card3.pack(fill="x", pady=15, padx=10)
        card3.pack_propagate(False)
        
        def on_enter_card3(e):
            colors = self._get_card_colors()
            card3.configure(fg_color=colors["inactive_hover"])
            card3._is_hovered = True
        def on_leave_card3(e):
            colors = self._get_card_colors()
            card3.configure(fg_color=colors["inactive"])
            card3._is_hovered = False
        
        card3._is_hovered = False
        card3.bind("<Enter>", on_enter_card3)
        card3.bind("<Leave>", on_leave_card3)
        self._menu_cards.append({"card": card3, "type": "inactive"})

        card3_content = ctk.CTkFrame(card3, fg_color="transparent")
        card3_content.pack(fill="both", expand=True, padx=25, pady=20)
        card3_content.bind("<Enter>", on_enter_card3)
        card3_content.bind("<Leave>", on_leave_card3)

        ctk.CTkLabel(
            card3_content,
            text="📝",
            font=ctk.CTkFont(size=40)
        ).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(
            card3_content,
            text="기능 3",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(anchor="w", pady=(0, 5))

        ctk.CTkLabel(
            card3_content,
            text="준비 중입니다",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        ).pack(anchor="w")

        def bind_hover_to_children_card3(parent):
            """카드3의 모든 자식 위젯에 hover 이벤트 바인딩"""
            for child in parent.winfo_children():
                child.bind("<Enter>", on_enter_card3)
                child.bind("<Leave>", on_leave_card3)
                bind_hover_to_children_card3(child)
        
        bind_hover_to_children_card3(card3)

        # 카드 4 (준비 중)
        card4 = ctk.CTkFrame(
            cards_frame,
            fg_color=card_colors["inactive"],
            corner_radius=15,
            height=150
        )
        card4.pack(fill="x", pady=15, padx=10)
        card4.pack_propagate(False)
        
        def on_enter_card4(e):
            colors = self._get_card_colors()
            card4.configure(fg_color=colors["inactive_hover"])
            card4._is_hovered = True
        def on_leave_card4(e):
            colors = self._get_card_colors()
            card4.configure(fg_color=colors["inactive"])
            card4._is_hovered = False
        
        card4._is_hovered = False
        card4.bind("<Enter>", on_enter_card4)
        card4.bind("<Leave>", on_leave_card4)
        self._menu_cards.append({"card": card4, "type": "inactive"})

        card4_content = ctk.CTkFrame(card4, fg_color="transparent")
        card4_content.pack(fill="both", expand=True, padx=25, pady=20)
        card4_content.bind("<Enter>", on_enter_card4)
        card4_content.bind("<Leave>", on_leave_card4)

        ctk.CTkLabel(
            card4_content,
            text="⚙️",
            font=ctk.CTkFont(size=40)
        ).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(
            card4_content,
            text="기능 4",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(anchor="w", pady=(0, 5))

        ctk.CTkLabel(
            card4_content,
            text="준비 중입니다",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        ).pack(anchor="w")

        def bind_hover_to_children_card4(parent):
            """카드4의 모든 자식 위젯에 hover 이벤트 바인딩"""
            for child in parent.winfo_children():
                child.bind("<Enter>", on_enter_card4)
                child.bind("<Leave>", on_leave_card4)
                bind_hover_to_children_card4(child)
        
        bind_hover_to_children_card4(card4)

        # 하단 정보 표시 (저작권 + 버전)
        bottom_frame = ctk.CTkFrame(self.menu_page, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", pady=(10, 0))
        
        # 왼쪽: 저작권 표시
        copyright_label = ctk.CTkLabel(
            bottom_frame,
            text=f"© 2025 Dugyeon. All rights reserved.",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        copyright_label.pack(side="left", padx=5)
        
        # 오른쪽: 버전 표시
        version_label = ctk.CTkLabel(
            bottom_frame,
            text=f"v{__version__}",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        version_label.pack(side="right", padx=5)

    def _create_autoclicker_page(self):
        """오토마우스 페이지 UI 생성"""
        # 클릭 설정 박스
        box = ctk.CTkFrame(self.autoclicker_page)
        box.pack(pady=10, fill="x")

        # 클릭 타입
        row1 = ctk.CTkFrame(box)
        row1.pack(padx=15, pady=(15, 10), fill="x")

        ctk.CTkLabel(row1, text="클릭 버튼", font=ctk.CTkFont(size=16)).pack(side="left", padx=15)
        self.click_type = ctk.CTkSegmentedButton(row1, values=["좌클릭", "우클릭"], height=35)
        self.click_type.set(self.config.get("click_type", "좌클릭"))
        self.click_type.pack(side="right", padx=15)

        # 클릭 모드
        row_mode = ctk.CTkFrame(box)
        row_mode.pack(padx=15, pady=10, fill="x")

        ctk.CTkLabel(row_mode, text="클릭 모드", font=ctk.CTkFont(size=16)).pack(side="left", padx=15)
        self.click_mode = ctk.CTkSegmentedButton(
            row_mode, 
            values=["반복", "꾹누르기"],
            command=self._on_mode_change,
            height=35
        )
        self.click_mode.set(self.config.get("click_mode", "반복"))
        self.click_mode.pack(side="right", padx=15)

        # 간격(초)
        self.interval_row = ctk.CTkFrame(box)
        self.interval_row.pack(padx=15, pady=10, fill="x")

        self.interval_label = ctk.CTkLabel(self.interval_row, text="클릭 간격 (초)", font=ctk.CTkFont(size=16))
        self.interval_label.pack(side="left", padx=15)
        self.interval_sec = ctk.CTkEntry(self.interval_row, width=180, height=35, font=ctk.CTkFont(size=14))
        self.interval_sec.insert(0, self.config.get("click_interval", "0.1"))
        self.interval_sec.pack(side="right", padx=15)

        self.hint = ctk.CTkLabel(
            box,
            text="예: 1초=1.0 / 0.1초=0.1 / 1ms=0.001",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        )
        self.hint.pack(padx=15, pady=(0, 15))

        # 초기 모드에 따라 간격 표시/숨김
        self._on_mode_change(self.config.get("click_mode", "반복"))

        # 버튼
        btns = ctk.CTkFrame(self.autoclicker_page)
        btns.pack(pady=15, fill="x")

        self.start_btn = ctk.CTkButton(
            btns, text=f"▶️ 시작 ({self.config.get('hotkey_start', 'F6')})", height=55,
            fg_color="#2ecc71", hover_color="#27ae60",
            font=ctk.CTkFont(size=18, weight="bold"),
            command=self.start
        )
        self.start_btn.pack(side="left", padx=15, pady=15, expand=True, fill="x")

        self.stop_btn = ctk.CTkButton(
            btns, text=f"⏹️ 중지 ({self.config.get('hotkey_stop', 'F7')})", height=55,
            fg_color="#e74c3c", hover_color="#c0392b",
            font=ctk.CTkFont(size=18, weight="bold"),
            command=self.stop,
            state="disabled"
        )
        self.stop_btn.pack(side="right", padx=15, pady=15, expand=True, fill="x")

        # 상태
        self.status = ctk.CTkLabel(self.autoclicker_page, text="⏸️ 대기 중...", font=ctk.CTkFont(size=16))
        self.status.pack(pady=(12, 0))

        self.hotkey_display = ctk.CTkLabel(
            self.autoclicker_page,
            text=f"단축키: {self.config.get('hotkey_start', 'F6')} 시작 / {self.config.get('hotkey_stop', 'F7')} 중지",
            font=ctk.CTkFont(size=13), text_color="gray"
        )
        self.hotkey_display.pack(pady=(6, 15))
        
        # 하단 정보 표시 (저작권 + 버전)
        bottom_frame = ctk.CTkFrame(self.autoclicker_page, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", pady=(10, 0))
        
        # 왼쪽: 저작권 표시
        copyright_label = ctk.CTkLabel(
            bottom_frame,
            text=f"© 2025 Dugyeon. All rights reserved.",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        copyright_label.pack(side="left", padx=5)
        
        # 오른쪽: 버전 표시
        version_label = ctk.CTkLabel(
            bottom_frame,
            text=f"v{__version__}",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        version_label.pack(side="right", padx=5)

    def _create_settings_page(self):
        """설정 페이지 UI 생성"""
        # 스크롤 가능한 컨테이너
        scrollable_frame = ctk.CTkScrollableFrame(self.settings_page, fg_color="transparent")
        scrollable_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # ========== 오토마우스 설정 섹션 ==========
        autoclicker_section_label = ctk.CTkLabel(
            scrollable_frame,
            text="오토마우스 설정",
            font=ctk.CTkFont(size=20, weight="bold"),
            anchor="w"
        )
        autoclicker_section_label.pack(fill="x", padx=20, pady=(15, 10))
        
        # 시작 단축키 항목
        start_item = ctk.CTkFrame(scrollable_frame)
        start_item.pack(pady=(0, 12), fill="x", padx=20)

        start_left = ctk.CTkFrame(start_item, fg_color="transparent")
        start_left.pack(side="left", padx=20, pady=15)
        
        ctk.CTkLabel(
            start_left, 
            text="시작 단축키", 
            font=ctk.CTkFont(size=17, weight="bold")
        ).pack(anchor="w")
        ctk.CTkLabel(
            start_left, 
            text="클릭 자동화를 시작합니다", 
            font=ctk.CTkFont(size=13), 
            text_color="gray"
        ).pack(anchor="w")

        self.hotkey_start_btn = ctk.CTkButton(
            start_item,
            text=self.config.get("hotkey_start", "F6"),
            width=100,
            height=40,
            fg_color="#404040",
            hover_color="#505050",
            font=ctk.CTkFont(size=15),
            command=lambda: self._start_hotkey_setting("start")
        )
        self.hotkey_start_btn.pack(side="right", padx=20, pady=15)

        # 중지 단축키 항목
        stop_item = ctk.CTkFrame(scrollable_frame)
        stop_item.pack(pady=(0, 12), fill="x", padx=20)

        stop_left = ctk.CTkFrame(stop_item, fg_color="transparent")
        stop_left.pack(side="left", padx=20, pady=15)
        
        ctk.CTkLabel(
            stop_left, 
            text="중지 단축키", 
            font=ctk.CTkFont(size=17, weight="bold")
        ).pack(anchor="w")
        ctk.CTkLabel(
            stop_left, 
            text="클릭 자동화를 중지합니다", 
            font=ctk.CTkFont(size=13), 
            text_color="gray"
        ).pack(anchor="w")

        self.hotkey_stop_btn = ctk.CTkButton(
            stop_item,
            text=self.config.get("hotkey_stop", "F7"),
            width=100,
            height=40,
            fg_color="#404040",
            hover_color="#505050",
            font=ctk.CTkFont(size=15),
            command=lambda: self._start_hotkey_setting("stop")
        )
        self.hotkey_stop_btn.pack(side="right", padx=20, pady=15)

        # 랜덤 변동값 항목
        variance_item = ctk.CTkFrame(scrollable_frame)
        variance_item.pack(pady=(0, 20), fill="x", padx=20)
        
        # ========== 메인 설정 섹션 ==========
        main_section_label = ctk.CTkLabel(
            scrollable_frame,
            text="메인 설정",
            font=ctk.CTkFont(size=20, weight="bold"),
            anchor="w"
        )
        main_section_label.pack(fill="x", padx=20, pady=(10, 10))

        variance_left = ctk.CTkFrame(variance_item, fg_color="transparent")
        variance_left.pack(side="left", padx=20, pady=15)
        
        ctk.CTkLabel(
            variance_left, 
            text="랜덤 변동값 (±초)", 
            font=ctk.CTkFont(size=17, weight="bold")
        ).pack(anchor="w")
        ctk.CTkLabel(
            variance_left, 
            text="클릭 간격에 랜덤 변동을 추가합니다", 
            font=ctk.CTkFont(size=13), 
            text_color="gray"
        ).pack(anchor="w")

        variance_right = ctk.CTkFrame(variance_item, fg_color="transparent")
        variance_right.pack(side="right", padx=20, pady=15)
        
        # ON/OFF 스위치
        variance_enabled = self.config.get("random_variance_enabled", True)
        if isinstance(variance_enabled, str):
            variance_enabled = variance_enabled.lower() == "true"
        
        self.variance_switch = ctk.CTkSwitch(
            variance_right,
            text="ON",
            command=self._on_variance_switch_change
        )
        self.variance_switch.pack(side="left", padx=(0, 12))
        if variance_enabled:
            self.variance_switch.select()
        
        variance_input_frame = ctk.CTkFrame(variance_right, fg_color="transparent")
        variance_input_frame.pack(side="left")
        
        self.variance_entry = ctk.CTkEntry(
            variance_input_frame,
            width=120,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.variance_entry.insert(0, self.config.get("random_variance", "0.03"))
        self.variance_entry.pack(side="left", padx=(0, 8))
        self.variance_entry.bind("<KeyRelease>", lambda event: self._mark_settings_dirty())
        
        # 스위치 상태에 따라 입력 필드 활성화/비활성화
        if not variance_enabled:
            self.variance_entry.configure(state="disabled")
        
        save_variance_btn = ctk.CTkButton(
            variance_input_frame,
            text="저장",
            width=60,
            height=40,
            font=ctk.CTkFont(size=13),
            command=self._save_variance
        )
        save_variance_btn.pack(side="left")

        # 다크모드/라이트모드 항목
        theme_item = ctk.CTkFrame(scrollable_frame)
        theme_item.pack(pady=(0, 12), fill="x", padx=20)

        theme_left = ctk.CTkFrame(theme_item, fg_color="transparent")
        theme_left.pack(side="left", padx=20, pady=15)
        
        ctk.CTkLabel(
            theme_left, 
            text="테마 모드", 
            font=ctk.CTkFont(size=17, weight="bold")
        ).pack(anchor="w")
        ctk.CTkLabel(
            theme_left, 
            text="다크모드 또는 라이트모드를 선택합니다", 
            font=ctk.CTkFont(size=13), 
            text_color="gray"
        ).pack(anchor="w")

        theme_right = ctk.CTkFrame(theme_item, fg_color="transparent")
        theme_right.pack(side="right", padx=20, pady=15)
        
        # 다크모드/라이트모드 선택
        appearance_mode = self.config.get("appearance_mode", "dark")
        self.theme_mode = ctk.CTkSegmentedButton(
            theme_right,
            values=["다크모드", "라이트모드"],
            command=self._on_theme_mode_change,
            height=40,
            width=200
        )
        if appearance_mode == "light":
            self.theme_mode.set("라이트모드")
        else:
            self.theme_mode.set("다크모드")
        self.theme_mode.pack()

        # 업데이트 항목
        update_item = ctk.CTkFrame(scrollable_frame)
        update_item.pack(pady=(0, 20), fill="x", padx=20)

        update_left = ctk.CTkFrame(update_item, fg_color="transparent")
        update_left.pack(side="left", padx=20, pady=15, fill="both", expand=True)
        
        ctk.CTkLabel(
            update_left, 
            text="업데이트", 
            font=ctk.CTkFont(size=17, weight="bold")
        ).pack(anchor="w")
        
        version_info = ctk.CTkFrame(update_left, fg_color="transparent")
        version_info.pack(anchor="w", pady=(5, 0))
        
        ctk.CTkLabel(
            version_info,
            text=f"현재 버전: v{__version__}",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        ).pack(side="left")
        
        update_right = ctk.CTkFrame(update_item, fg_color="transparent")
        update_right.pack(side="right", padx=20, pady=15)
        
        # 버튼들을 담는 프레임
        buttons_frame = ctk.CTkFrame(update_right, fg_color="transparent")
        buttons_frame.pack()
        
        self.update_check_btn = ctk.CTkButton(
            buttons_frame,
            text="업데이트 확인",
            width=120,
            height=40,
            font=ctk.CTkFont(size=14),
            command=self._check_update_manual
        )
        self.update_check_btn.pack(side="left", padx=(0, 8))
        
        self.update_download_btn = ctk.CTkButton(
            buttons_frame,
            text="다운로드",
            width=100,
            height=40,
            font=ctk.CTkFont(size=14),
            fg_color="#3498db",
            hover_color="#2980b9",
            command=self._download_update,
            state="disabled"
        )
        self.update_download_btn.pack(side="left")
        
        # 상태 라벨을 버튼 아래에 배치
        # 버튼 영역과 폭을 맞춘 상태 라벨
        self.update_status_label = ctk.CTkLabel(
            update_right,
            text="",
            width=220,  # 버튼 2개 너비와 비슷하게 제한
            font=ctk.CTkFont(size=13),
            text_color="#2ecc71",
            anchor="center"
        )
        self.update_status_label.pack(pady=(6, 0))

        # 안내 문구
        hint_label = ctk.CTkLabel(
            scrollable_frame,
            text="💡 버튼을 클릭한 후 원하는 키를 누르세요",
            font=ctk.CTkFont(size=13),
            text_color="#888888",
        )
        hint_label.pack(pady=(10, 8), padx=20)

        # 설정 상태 메시지
        self.settings_status = ctk.CTkLabel(
            scrollable_frame,
            text="",
            font=ctk.CTkFont(size=14),
            text_color="#2ecc71"
        )
        self.settings_status.pack(pady=(8, 15), padx=20)

        # 설정 저장 버튼
        save_all_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        save_all_frame.pack(pady=(5, 20), padx=20)
        self.save_settings_btn = ctk.CTkButton(
            save_all_frame,
            text="설정 저장",
            width=140,
            height=42,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#3498db",
            hover_color="#2980b9",
            command=self._save_settings
        )
        self.save_settings_btn.pack()

    def navigate_to_page(self, page: str):
        """페이지 네비게이션"""
        if page == "autoclicker":
            self._show_page("autoclicker")
        elif page == "menu":
            self._show_page("menu")
        elif page == "settings":
            self._show_page("settings")

    def go_back(self):
        """뒤로가기 버튼 클릭"""
        if self._current_page == "autoclicker":
            self._show_page("menu")
        elif self._current_page == "settings":
            # 설정 페이지에서 뒤로가기 시 현재 페이지로 돌아감
            if self._settings_dirty:
                result = self._ask_save_changes()
                if result == "cancel":
                    return
                if result == "yes":
                    if not self._save_settings():
                        return
                else:
                    # 변경사항 취소
                    self.config = load_config()
                    self._apply_settings_from_config()
                    self.teardown_hotkeys()
                    self.setup_hotkeys()
                    self._update_main_hotkey_labels()
                    self._settings_dirty = False
                    self._refresh_settings_snapshot()
            self._show_page("menu")

    def toggle_settings(self):
        """설정 페이지 토글"""
        if self._current_page == "settings":
            self.go_back()
        else:
            # 설정 페이지로 전환
            # 최신 설정 불러오기
            self.config = load_config()
            self._apply_settings_from_config()
            self._refresh_settings_snapshot()
            self._show_page("settings")

    def _show_page(self, page: str):
        """페이지 표시/숨김 처리"""
        # 모든 페이지 숨기기
        self.menu_page.pack_forget()
        self.autoclicker_page.pack_forget()
        self.settings_page.pack_forget()

        # 뒤로가기 버튼 및 설정 버튼 표시/숨김 및 창 크기 조정
        if page == "menu":
            self.back_btn.pack_forget()
            self.settings_btn.pack(side="right", padx=5)  # 설정 버튼 표시
            self.title_label.configure(text="띵타이쿤 일꾼용")
        else:
            self.back_btn.pack(side="right", padx=5)
            self.settings_btn.pack_forget()  # 설정 버튼 숨김
            if page == "autoclicker":
                self.title_label.configure(text="오토마우스")
            elif page == "settings":
                self.title_label.configure(text="설정")

        # 해당 페이지 표시
        if page == "menu":
            self.menu_page.pack(fill="both", expand=True, padx=25, pady=15)
        elif page == "autoclicker":
            self.autoclicker_page.pack(fill="both", expand=True, padx=25, pady=15)
        elif page == "settings":
            self.settings_page.pack(fill="both", expand=True, padx=25, pady=15)

        self._current_page = page
        
        # 설정 상태 메시지 초기화 (설정 페이지가 아닐 때)
        if page != "settings" and hasattr(self, "settings_status"):
            self.settings_status.configure(text="")

    # ---------------- Hotkey Setting ----------------
    def _start_hotkey_setting(self, which: str):
        """단축키 설정 시작"""
        if self._running:
            self.settings_status.configure(text="⚠️ 실행 중에는 변경할 수 없습니다.", text_color="#e74c3c")
            return

        self._setting_hotkey = which

        if which == "start":
            self.hotkey_start_btn.configure(text="...", fg_color="#3498db")
        else:
            self.hotkey_stop_btn.configure(text="...", fg_color="#3498db")

        self.settings_status.configure(text="⌨️ 원하는 키를 누르세요...", text_color="#f39c12")

        # 키 입력 대기
        keyboard.on_press(self._on_hotkey_press)

    def _on_hotkey_press(self, event):
        """키 입력 감지"""
        if self._setting_hotkey is None:
            return

        keyboard.unhook_all()

        key = event.name.upper()
        which = self._setting_hotkey
        self._setting_hotkey = None

        # UI 업데이트는 메인 스레드에서
        self.after(0, lambda: self._apply_hotkey(which, key))

    def _apply_hotkey(self, which: str, key: str):
        """단축키 적용"""
        # 기존 단축키 해제
        self.teardown_hotkeys()

        if which == "start":
            self.config["hotkey_start"] = key
            self.hotkey_start_btn.configure(text=key, fg_color="#404040")
            self.start_btn.configure(text=f"▶️ 시작 ({key})")
        else:
            self.config["hotkey_stop"] = key
            self.hotkey_stop_btn.configure(text=key, fg_color="#404040")
            self.stop_btn.configure(text=f"⏹️ 중지 ({key})")

        # 단축키 다시 등록
        self.setup_hotkeys()

        # UI 업데이트
        self.hotkey_display.configure(
            text=f"단축키: {self.config['hotkey_start']} 시작 / {self.config['hotkey_stop']} 중지"
        )
        self._mark_settings_dirty(f"💾 단축키 변경됨: {key}")

    # ---------------- Hotkeys ----------------
    def setup_hotkeys(self):
        try:
            start_key = self.config.get("hotkey_start", "F6")
            stop_key = self.config.get("hotkey_stop", "F7")

            self._hotkey_start = keyboard.add_hotkey(start_key, lambda: self.after(0, self.start))
            self._hotkey_stop = keyboard.add_hotkey(stop_key, lambda: self.after(0, self.stop))
        except Exception as e:
            print(f"단축키 등록 실패: {e}")

    def teardown_hotkeys(self):
        try:
            if self._hotkey_start is not None:
                keyboard.remove_hotkey(self._hotkey_start)
                self._hotkey_start = None
            if self._hotkey_stop is not None:
                keyboard.remove_hotkey(self._hotkey_stop)
                self._hotkey_stop = None
        except Exception:
            pass

    # ---------------- Mode Change ----------------
    def _on_mode_change(self, mode: str):
        """클릭 모드 변경 시 UI 업데이트"""
        if mode == "꾹누르기":
            # 간격 설정 비활성화
            self.interval_sec.configure(state="disabled")
            self.interval_label.configure(text_color="gray")
            self.hint.configure(text="버튼을 누른 상태로 유지합니다")
        else:
            # 간격 설정 활성화
            self.interval_sec.configure(state="normal")
            self.interval_label.configure(text_color=("gray10", "gray90"))
            self.hint.configure(text="예: 1초=1.0 / 0.1초=0.1 / 1ms=0.001")

    # ---------------- Helpers ----------------
    def _set_status(self, text: str):
        self.status.configure(text=text)

    def _parse_float(self, entry: ctk.CTkEntry, name: str, min_value: float) -> float | None:
        raw = entry.get().strip()
        try:
            value = float(raw)
        except ValueError:
            self._set_status(f"⚠️ {name} 값이 숫자가 아닙니다.")
            return None
        if value < min_value:
            self._set_status(f"⚠️ {name} 값은 {min_value} 이상이어야 합니다.")
            return None
        return value

    def _get_settings_state(self) -> dict:
        """현재 설정 페이지의 값을 딕셔너리로 반환"""
        return {
            "hotkey_start": self.hotkey_start_btn.cget("text"),
            "hotkey_stop": self.hotkey_stop_btn.cget("text"),
            "random_variance": self.variance_entry.get().strip(),
            "random_variance_enabled": bool(self.variance_switch.get()),
        }

    def _mark_settings_dirty(self, message: str = "💾 변경 사항이 있습니다. 저장을 눌러주세요."):
        """설정 변경 상태 표시"""
        if self._suppress_dirty:
            return
        self._settings_dirty = True
        if hasattr(self, "settings_status"):
            self.settings_status.configure(text=message, text_color="#f39c12")

    def _refresh_settings_snapshot(self):
        """현재 설정 상태를 스냅샷으로 저장하고 dirty 플래그 해제"""
        self._settings_snapshot = self._get_settings_state()
        self._settings_dirty = False
        if hasattr(self, "settings_status"):
            self.settings_status.configure(text="", text_color="#2ecc71")

    def _ask_save_changes(self) -> str:
        """설정 변경 사항 저장 여부를 커스텀 다이얼로그로 확인"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("변경 사항 확인")
        dialog.geometry("360x190")
        dialog.resizable(False, False)
        dialog.attributes("-topmost", True)
        dialog.transient(self)
        dialog.grab_set()
        # 다이얼로그 아이콘 동일하게 적용
        try:
            base_dir = Path(__file__).resolve().parent.parent
            assets_dir = base_dir / "assets"
            icon_path = assets_dir / "icon.ico"
            if icon_path.exists():
                dialog.iconbitmap(str(icon_path))
        except Exception:
            pass

        # 중앙 정렬
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - 180
        y = self.winfo_rooty() + (self.winfo_height() // 2) - 95
        dialog.geometry(f"+{x}+{y}")

        # 컨텐츠
        body = ctk.CTkFrame(dialog, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=20)

        title = ctk.CTkLabel(
            body,
            text="변경 사항이 있습니다.",
            font=ctk.CTkFont(size=17, weight="bold")
        )
        title.pack(anchor="w", pady=(0, 6))

        msg = ctk.CTkLabel(
            body,
            text="저장하지 않고 나가면 변경 내용이 사라집니다.\n저장하시겠습니까?",
            font=ctk.CTkFont(size=13),
            justify="left"
        )
        msg.pack(anchor="w")

        btns = ctk.CTkFrame(body, fg_color="transparent")
        btns.pack(side="bottom", fill="x", pady=(16, 0))

        choice = {"value": "cancel"}

        def _select(val: str):
            choice["value"] = val
            dialog.destroy()

        save_btn = ctk.CTkButton(
            btns, text="저장 후 이동", width=100,
            fg_color="#3498db", hover_color="#2980b9",
            command=lambda: _select("yes")
        )
        save_btn.pack(side="left", padx=(0, 8))

        discard_btn = ctk.CTkButton(
            btns, text="저장 안 함", width=100,
            fg_color="#404040", hover_color="#505050",
            command=lambda: _select("no")
        )
        discard_btn.pack(side="left", padx=(0, 8))

        cancel_btn = ctk.CTkButton(
            btns, text="취소", width=80,
            fg_color="#e74c3c", hover_color="#c0392b",
            command=lambda: _select("cancel")
        )
        cancel_btn.pack(side="right")

        dialog.focus_force()
        dialog.wait_window()
        return choice["value"]

    def _apply_settings_from_config(self):
        """config 값을 UI에 반영"""
        self._suppress_dirty = True
        self.hotkey_start_btn.configure(text=self.config.get("hotkey_start", "F6"), fg_color="#404040")
        self.hotkey_stop_btn.configure(text=self.config.get("hotkey_stop", "F7"), fg_color="#404040")

        self.variance_entry.configure(state="normal")
        self.variance_entry.delete(0, "end")
        self.variance_entry.insert(0, self.config.get("random_variance", "0.03"))

        variance_enabled = self.config.get("random_variance_enabled", True)
        if isinstance(variance_enabled, str):
            variance_enabled = variance_enabled.lower() == "true"
        if variance_enabled:
            self.variance_switch.select()
            self.variance_switch.configure(text="ON")
            self.variance_entry.configure(state="normal")
        else:
            self.variance_switch.deselect()
            self.variance_switch.configure(text="OFF")
            self.variance_entry.configure(state="disabled")

        # 테마 모드 적용
        appearance_mode = self.config.get("appearance_mode", "dark")
        if hasattr(self, "theme_mode"):
            if appearance_mode == "light":
                self.theme_mode.set("라이트모드")
            else:
                self.theme_mode.set("다크모드")
        ctk.set_appearance_mode(appearance_mode)
        
        # 버튼 아이콘 색상 업데이트
        self._update_button_colors()

        self._update_main_hotkey_labels()
        self._suppress_dirty = False

    def _update_main_hotkey_labels(self):
        """메인 페이지의 단축키 표시 업데이트"""
        start = self.config.get("hotkey_start", "F6")
        stop = self.config.get("hotkey_stop", "F7")
        self.start_btn.configure(text=f"▶️ 시작 ({start})")
        self.stop_btn.configure(text=f"⏹️ 중지 ({stop})")
        self.hotkey_display.configure(
            text=f"단축키: {start} 시작 / {stop} 중지"
        )

    def _save_settings(self) -> bool:
        """설정을 저장하고 상태를 갱신"""
        variance = self._parse_float(self.variance_entry, "랜덤 변동값", min_value=0.0)
        if variance is None:
            if hasattr(self, "settings_status"):
                self.settings_status.configure(text="⚠️ 유효한 랜덤 변동값을 입력하세요.", text_color="#e74c3c")
            return False

        self.config["hotkey_start"] = self.hotkey_start_btn.cget("text")
        self.config["hotkey_stop"] = self.hotkey_stop_btn.cget("text")
        self.config["random_variance"] = str(variance)
        self.config["random_variance_enabled"] = bool(self.variance_switch.get())
        
        # 테마 모드 저장
        theme_mode = self.theme_mode.get()
        if theme_mode == "라이트모드":
            self.config["appearance_mode"] = "light"
        else:
            self.config["appearance_mode"] = "dark"
        ctk.set_appearance_mode(self.config["appearance_mode"])
        
        # 버튼 아이콘 색상 업데이트
        self._update_button_colors()

        save_config(self.config)
        self.teardown_hotkeys()
        self.setup_hotkeys()
        self._update_main_hotkey_labels()

        self._refresh_settings_snapshot()
        if hasattr(self, "settings_status"):
            self.settings_status.configure(text="✅ 설정이 저장되었습니다.", text_color="#2ecc71")
        return True

    def _on_variance_switch_change(self):
        """랜덤 변동값 스위치 변경 시"""
        is_enabled = self.variance_switch.get()
        
        if is_enabled:
            self.variance_entry.configure(state="normal")
            self.variance_switch.configure(text="ON")
        else:
            self.variance_entry.configure(state="disabled")
            self.variance_switch.configure(text="OFF")
        self.config["random_variance_enabled"] = is_enabled
        self._mark_settings_dirty("💾 변경 사항이 있습니다. 저장을 눌러주세요.")

    def _update_button_colors(self):
        """버튼 아이콘 색상을 현재 테마에 맞게 업데이트"""
        current_mode = ctk.get_appearance_mode()
        if current_mode == "Light":
            # 라이트 모드: 검정색
            text_color = "black"
            hover_color = "#e0e0e0"
        else:
            # 다크 모드: 흰색
            text_color = "white"
            hover_color = "#3a3a3a"
        
        if hasattr(self, 'settings_btn'):
            self.settings_btn.configure(text_color=text_color, hover_color=hover_color)
        if hasattr(self, 'back_btn'):
            self.back_btn.configure(text_color=text_color, hover_color=hover_color)

    def _update_card_colors(self):
        """카드 색상을 현재 테마에 맞게 업데이트"""
        if not hasattr(self, '_menu_cards'):
            return
        
        card_colors = self._get_card_colors()
        for card_info in self._menu_cards:
            card = card_info["card"]
            card_type = card_info["type"]
            
            # 카드의 hover 상태를 확인하여 적절한 색상으로 업데이트
            is_hovered = getattr(card, '_is_hovered', False)
            
            if card_type == "active":
                if is_hovered:
                    card.configure(fg_color=card_colors["active_hover"])
                else:
                    card.configure(fg_color=card_colors["active"])
            else:
                if is_hovered:
                    card.configure(fg_color=card_colors["inactive_hover"])
                else:
                    card.configure(fg_color=card_colors["inactive"])

    def _on_theme_mode_change(self, mode: str):
        """테마 모드 변경 시"""
        if mode == "라이트모드":
            appearance_mode = "light"
        else:
            appearance_mode = "dark"
        
        ctk.set_appearance_mode(appearance_mode)
        self.config["appearance_mode"] = appearance_mode
        save_config(self.config)
        self._mark_settings_dirty("💾 테마 모드가 변경되었습니다.")
        
        # 버튼 아이콘 색상 즉시 업데이트
        self._update_button_colors()
        
        # 카드 색상 즉시 업데이트 (메인 페이지가 표시 중일 때만 의미가 있지만 항상 호출)
        self._update_card_colors()

    def _save_variance(self):
        """랜덤 변동값 저장(전체 설정 저장과 동일)"""
        self._save_settings()
    
    def check_for_updates(self):
        """앱 시작 시 자동으로 업데이트 확인"""
        def update_callback(has_update, latest_version, message):
            if has_update and latest_version:
                self.after(0, lambda: self._on_update_found(latest_version, message))
        
        check_update_async(update_callback)
    
    def _check_update_manual(self):
        """수동으로 업데이트 확인"""
        self.update_status_label.configure(text="확인 중...", text_color="#f39c12")
        self.update_check_btn.configure(state="disabled")
        
        def update_callback(has_update, latest_version, message):
            self.after(0, lambda: self._on_update_check_complete(has_update, latest_version, message))
        
        check_update_async(update_callback)
    
    def _on_update_check_complete(self, has_update, latest_version, message):
        """업데이트 확인 완료 시 호출"""
        self.update_check_btn.configure(state="normal")
        
        if has_update and latest_version:
            self.update_status_label.configure(
                text=f"최신 버전: v{latest_version} 사용 가능", 
                text_color="#2ecc71"
            )
            self.update_download_btn.configure(state="normal")
            self._latest_version = latest_version
        else:
            self.update_status_label.configure(text="최신 버전입니다.", text_color="#2ecc71")
            self.update_download_btn.configure(state="disabled")
    
    def _on_update_found(self, latest_version, message):
        """자동 업데이트 확인 시 업데이트 발견"""
        result = messagebox.askyesno(
            "업데이트 사용 가능",
            f"새로운 버전 v{latest_version}이(가) 있습니다.\n\n"
            f"설정 페이지에서 다운로드할 수 있습니다.\n\n"
            f"지금 설정 페이지로 이동하시겠습니까?",
            icon="info"
        )
        if result:
            if self._current_page != "settings":
                self.navigate_to_page("settings")
            self._latest_version = latest_version
            self.update_status_label.configure(
                text=f"최신 버전: v{latest_version} 사용 가능", 
                text_color="#2ecc71"
            )
            self.update_download_btn.configure(state="normal")
    
    def _download_update(self):
        """업데이트 다운로드"""
        if not hasattr(self, '_latest_version'):
            self.settings_status.configure(
                text="⚠️ 먼저 업데이트를 확인해주세요.", 
                text_color="#e74c3c"
            )
            return
        
        self.update_download_btn.configure(state="disabled", text="다운로드 중...")
        self.settings_status.configure(text="다운로드 중...", text_color="#f39c12")
        
        def download_thread():
            updater = Updater()
            success, message = updater.download_update()
            
            self.after(0, lambda: self._on_download_complete(success, message))
        
        thread = threading.Thread(target=download_thread, daemon=True)
        thread.start()
    
    def _on_download_complete(self, success, message):
        """다운로드 완료 시 호출"""
        self.update_download_btn.configure(state="normal", text="다운로드")
        
        if success:
            self.settings_status.configure(
                text=f"✅ {message}", 
                text_color="#2ecc71"
            )
            result = messagebox.askyesno(
                "다운로드 완료",
                f"{message}\n\n업데이트를 설치하시겠습니까?",
                icon="question"
            )
            if result:
                updater = Updater()
                if updater.install_update(message.split(": ")[-1] if ": " in message else ""):
                    self.settings_status.configure(
                        text="✅ 업데이트 설치를 시작했습니다. 앱을 종료합니다.", 
                        text_color="#2ecc71"
                    )
                    self.after(2000, self.on_closing)
        else:
            self.settings_status.configure(
                text=f"⚠️ {message}", 
                text_color="#e74c3c"
            )

    # ---------------- Start/Stop ----------------
    def start(self):
        with self._lock:
            if self._running:
                return
            self._running = True
            self._stop_event.clear()

        click_type = self.click_type.get()
        click_mode = self.click_mode.get()
        button = Button.left if click_type == "좌클릭" else Button.right

        # 반복 모드일 때만 간격 검증
        interval = None
        variance = 0.0
        if click_mode == "반복":
            interval = self._parse_float(self.interval_sec, "클릭 간격(초)", min_value=0.0001)
            if interval is None:
                with self._lock:
                    self._running = False
                return
            
            # 랜덤 변동값 가져오기 (활성화된 경우에만)
            variance_enabled = self.config.get("random_variance_enabled", True)
            if isinstance(variance_enabled, str):
                variance_enabled = variance_enabled.lower() == "true"
            
            if variance_enabled:
                try:
                    variance = float(self.config.get("random_variance", "0.03"))
                    if variance < 0:
                        variance = 0.0
                except (ValueError, TypeError):
                    variance = 0.0
            else:
                variance = 0.0

        # 설정 저장
        self.config["click_interval"] = self.interval_sec.get()
        self.config["click_type"] = click_type
        self.config["click_mode"] = click_mode
        save_config(self.config)

        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        
        # Clicker 인스턴스 생성
        clicker = Clicker(self.mouse, self._stop_event)
        
        if click_mode == "꾹누르기":
            self._set_status(f"🔄 {click_type} 꾹누르는 중...")
            self._click_thread = threading.Thread(
                target=clicker.hold_loop,
                args=(button,),
                kwargs={
                    "status_callback": lambda msg: self.after(0, lambda: self._set_status(msg)),
                    "finish_callback": lambda: self.after(0, self._finish)
                },
                daemon=True
            )
        else:
            self._set_status("🔄 실행 중...")
            self._click_thread = threading.Thread(
                target=clicker.click_loop,
                args=(button, interval, variance),
                kwargs={
                    "status_callback": lambda msg: self.after(0, lambda: self._set_status(msg)),
                    "finish_callback": lambda: self.after(0, self._finish)
                },
                daemon=True
            )
        self._click_thread.start()

    def stop(self):
        self._stop_event.set()

        try:
            self.mouse.release(Button.left)
            self.mouse.release(Button.right)
        except Exception:
            pass

        self._finish()

    def _finish(self):
        with self._lock:
            self._running = False

        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self._set_status("⏸️ 대기 중...")

    # ---------------- Cleanup ----------------
    def on_closing(self):
        self._stop_event.set()
        self.teardown_hotkeys()
        self.destroy()
