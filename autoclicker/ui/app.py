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


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class AutoClickerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"🖱️손처럼 클릭 v{__version__}")
        self.geometry("550x650")
        self.minsize(400, 500)  # 최소 크기 설정 (너비, 높이)
        self.resizable(True, True)

        # 아이콘 설정
        self._set_icon()

        self.mouse = MouseController()
        self.config = load_config()

        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._running = False
        self._click_thread: threading.Thread | None = None

        self._hotkey_start = None
        self._hotkey_stop = None

        # 단축키 설정 중 상태
        self._setting_hotkey = None

        # 현재 화면 상태
        self._current_page = "main"
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
            text="손처럼 클릭",
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        self.title_label.pack(side="left")

        self.settings_btn = ctk.CTkButton(
            header,
            text="⚙",
            width=20,
            height=20,
            font=ctk.CTkFont(size=24),
            fg_color="transparent",
            hover_color="#3a3a3a",
            command=self.toggle_page
        )
        self.settings_btn.pack(side="right", padx=5)

        # 메인 페이지 컨테이너
        self.main_page = ctk.CTkFrame(self, fg_color="transparent")
        self.main_page.pack(fill="both", expand=True, padx=25, pady=15)

        # 설정 페이지 컨테이너 (처음엔 숨김)
        self.settings_page = ctk.CTkFrame(self, fg_color="transparent")

        self._create_main_page()
        self._create_settings_page()

    def _create_main_page(self):
        """메인 페이지 UI 생성"""
        # 클릭 설정 박스
        box = ctk.CTkFrame(self.main_page)
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
        btns = ctk.CTkFrame(self.main_page)
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
        self.status = ctk.CTkLabel(self.main_page, text="⏸️ 대기 중...", font=ctk.CTkFont(size=16))
        self.status.pack(pady=(12, 0))

        self.hotkey_display = ctk.CTkLabel(
            self.main_page,
            text=f"단축키: {self.config.get('hotkey_start', 'F6')} 시작 / {self.config.get('hotkey_stop', 'F7')} 중지",
            font=ctk.CTkFont(size=13), text_color="gray"
        )
        self.hotkey_display.pack(pady=(6, 15))
        
        # 하단 정보 표시 (저작권 + 버전)
        bottom_frame = ctk.CTkFrame(self.main_page, fg_color="transparent")
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
        # 시작 단축키 항목
        start_item = ctk.CTkFrame(self.settings_page)
        start_item.pack(pady=(10, 12), fill="x")

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
        stop_item = ctk.CTkFrame(self.settings_page)
        stop_item.pack(pady=(0, 12), fill="x")

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
        variance_item = ctk.CTkFrame(self.settings_page)
        variance_item.pack(pady=(10, 12), fill="x")

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

        # 업데이트 항목
        update_item = ctk.CTkFrame(self.settings_page)
        update_item.pack(pady=(10, 12), fill="x")

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
        ).pack(side="left", padx=(0, 10))
        
        self.update_status_label = ctk.CTkLabel(
            version_info,
            text="",
            font=ctk.CTkFont(size=13),
            text_color="#2ecc71"
        )
        self.update_status_label.pack(side="left")
        
        update_right = ctk.CTkFrame(update_item, fg_color="transparent")
        update_right.pack(side="right", padx=20, pady=15)
        
        self.update_check_btn = ctk.CTkButton(
            update_right,
            text="업데이트 확인",
            width=120,
            height=40,
            font=ctk.CTkFont(size=14),
            command=self._check_update_manual
        )
        self.update_check_btn.pack(side="left", padx=(0, 8))
        
        self.update_download_btn = ctk.CTkButton(
            update_right,
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

        # 안내 문구
        hint_label = ctk.CTkLabel(
            self.settings_page,
            text="💡 버튼을 클릭한 후 원하는 키를 누르세요",
            font=ctk.CTkFont(size=13),
            text_color="#888888",
        )
        hint_label.pack(pady=(20, 8))

        # 설정 상태 메시지
        self.settings_status = ctk.CTkLabel(
            self.settings_page,
            text="",
            font=ctk.CTkFont(size=14),
            text_color="#2ecc71"
        )
        self.settings_status.pack(pady=(8, 15))

        # 설정 저장 버튼
        save_all_frame = ctk.CTkFrame(self.settings_page, fg_color="transparent")
        save_all_frame.pack(pady=(5, 10))
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

    def toggle_page(self):
        """메인 페이지 ↔ 설정 페이지 전환"""
        if self._current_page == "main":
            # 설정 페이지로 전환
            # 최신 설정 불러오기
            self.config = load_config()
            self._apply_settings_from_config()
            self._refresh_settings_snapshot()
            self.main_page.pack_forget()
            self.settings_page.pack(fill="both", expand=True, padx=25, pady=15)
            self.title_label.configure(text="설정")
            self.settings_btn.configure(text="←")
            self._current_page = "settings"
        else:
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
            # 메인 페이지로 전환
            self.settings_page.pack_forget()
            self.main_page.pack(fill="both", expand=True, padx=25, pady=15)
            self.title_label.configure(text="손처럼 클릭")
            self.settings_btn.configure(text="⚙️")
            self._current_page = "main"
            # 설정 상태 메시지 초기화
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
            if self._current_page == "main":
                self.toggle_page()
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
