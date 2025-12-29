import threading
from pathlib import Path
from typing import Tuple
import customtkinter as ctk
from PIL import Image
from pynput.mouse import Button, Controller as MouseController
import keyboard
import tkinter.messagebox as messagebox

from tkinter import filedialog
from autoclicker.config import load_config, save_config
from autoclicker.clicker import Clicker
from autoclicker.macro_recorder import MacroRecorder, MacroPlayer, save_macro_to_file, load_macro_from_file
from autoclicker.updater import Updater, check_update_async
from autoclicker.version import __version__

from autoclicker.ui.pages.main_menu import MainMenuPage
from autoclicker.ui.pages.autoclicker import AutoClickerPage
from autoclicker.ui.pages.dding_info import DdingInfoPage
from autoclicker.ui.pages.settings import SettingsPage
from autoclicker.ui.pages.macro import MacroPage
from autoclicker.ui.pages.gangwa_calculator import GangwaCalculatorPage

ctk.set_default_color_theme("blue")

class AutoClickerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("띵타이쿤 일꾼용")
        self.geometry("600x850")
        self.minsize(450, 700)
        self.resizable(True, True)

        self._set_icon()

        self.mouse = MouseController()
        self.config = load_config()
        
        appearance_mode = self.config.get("appearance_mode", "dark")
        ctk.set_appearance_mode(appearance_mode)

        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._running = False
        self._click_thread: threading.Thread | None = None

        self._hotkey_start = None
        self._hotkey_stop = None
        
        self._hotkey_macro_record = None
        self._hotkey_macro_start = None
        self._hotkey_macro_stop = None

        self._setting_hotkey = None

        self._macro_recorder = MacroRecorder()
        self._macro_player = MacroPlayer()
        self._macro_actions = []

        self._current_page = "menu"
        self._last_page = "menu"
        self._settings_dirty = False
        self._settings_snapshot = {}
        self._suppress_dirty = False

        self.logo_image = self._load_logo_image()

        self.create_widgets()
        self.setup_hotkeys()
        
        self.check_for_updates()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _set_icon(self):
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
        base_dir = Path(__file__).resolve().parent.parent
        assets_dir = base_dir / "assets"
        logo_candidates = [
            assets_dir / "icon.png",
            assets_dir / "app.png",
        ]

        for logo_path in logo_candidates:
            if logo_path.exists():
                try:
                    img = Image.open(logo_path).resize((28, 28))
                    return ctk.CTkImage(light_image=img, dark_image=img, size=(28, 28))
                except Exception:
                    continue
        return None

    def create_widgets(self):
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

        self.settings_btn = ctk.CTkButton(
            header,
            text="⚙️",
            width=30,
            height=30,
            font=ctk.CTkFont(size=18),
            fg_color="transparent",
            hover_color="#3a3a3a",
            text_color=("black", "white"),
            command=self.toggle_settings,
        )
        self.settings_btn.pack(side="right", padx=5)

        self.back_btn = ctk.CTkButton(
            header,
            text="←",
            width=30,
            height=30,
            font=ctk.CTkFont(size=20),
            fg_color="transparent",
            hover_color="#3a3a3a",
            text_color=("black", "white"),
            command=self.go_back,
        )
        self.back_btn.pack(side="right", padx=5)
        self.back_btn.pack_forget()

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=25, pady=15)

        self.pages = {}
        for PageClass, name in [
            (MainMenuPage, "menu"),
            (AutoClickerPage, "autoclicker"),
            (DdingInfoPage, "dding_info"),
            (SettingsPage, "settings"),
            (MacroPage, "macro"),
            (GangwaCalculatorPage, "gangwa_calculator")
        ]:
            page = PageClass(self.container, self)
            self.pages[name] = page
        
        self._show_page("menu")

    def _get_card_colors(self):
        current_mode = ctk.get_appearance_mode()
        if current_mode == "Light":
            return {
                "active": "#e3f2fd",
                "active_hover": "#bbdefb",
                "inactive": "#f5f5f5",
                "inactive_hover": "#e0e0e0",
            }
        else:
            return {
                "active": "#2c3e50",
                "active_hover": "#34495e",
                "inactive": "#34495e",
                "inactive_hover": "#3d566e",
            }

    def navigate_to_page(self, page_name: str):
        self._show_page(page_name)

    def go_back(self):
        if self._current_page in ["autoclicker", "dding_info", "macro", "gangwa_calculator"]:
            self._show_page("menu")
        elif self._current_page == "settings":
            if self._settings_dirty:
                result = self._ask_save_changes()
                if result == "cancel":
                    return
                if result == "yes":
                    if not self._save_settings():
                        return
                else:
                    self.config = load_config()
                    self._apply_settings_from_config()
                    self.teardown_hotkeys()
                    self.setup_hotkeys()
                    self.pages["autoclicker"].update_hotkey_labels()
                    self._settings_dirty = False
                    self._refresh_settings_snapshot()
            self._show_page(self._last_page)

    def toggle_settings(self):
        if self._current_page == "settings":
            self.go_back()
        else:
            self.config = load_config()
            self._apply_settings_from_config()
            self._refresh_settings_snapshot()
            self._show_page("settings")

    def _show_page(self, page_name: str):
        for page in self.pages.values():
            page.pack_forget()

        if page_name == "menu":
            self.back_btn.pack_forget()
            self.settings_btn.pack(side="right", padx=5)
            self.title_label.configure(text="띵타이쿤 일꾼용")
        else:
            self.back_btn.pack(side="right", padx=5)
            if page_name == "settings":
                self.settings_btn.pack_forget()
                self.title_label.configure(text="설정")
            else:
                self.settings_btn.pack(side="right", padx=5)
                title_map = {"autoclicker": "오토마우스", "dding_info": "띵타이쿤 정보", "macro": "매크로", "gangwa_calculator": "강화계산기"}
                self.title_label.configure(text=title_map.get(page_name, ""))

        self.pages[page_name].pack(fill="both", expand=True)

        if page_name == "settings":
            settings_page = self.pages["settings"]
            if self._last_page == "autoclicker":
                settings_page.autoclicker_settings_section.pack(fill="x", padx=0, pady=0, before=settings_page.settings_footer)
                settings_page.macro_settings_section.pack_forget()
                settings_page.main_settings_section.pack_forget()
            elif self._last_page == "macro":
                settings_page.autoclicker_settings_section.pack_forget()
                settings_page.macro_settings_section.pack(fill="x", padx=0, pady=0, before=settings_page.settings_footer)
                settings_page.main_settings_section.pack_forget()
            else:
                settings_page.autoclicker_settings_section.pack(fill="x", padx=0, pady=0, before=settings_page.macro_settings_section)
                settings_page.macro_settings_section.pack(fill="x", padx=0, pady=0, before=settings_page.main_settings_section)
                settings_page.main_settings_section.pack(fill="x", padx=0, pady=0, before=settings_page.settings_footer)

        if self._current_page != "settings":
            self._last_page = self._current_page
        self._current_page = page_name

    def _start_hotkey_setting(self, which: str):
        if self._running:
            self.pages["settings"].settings_status.configure(text="⚠️ 실행 중에는 변경할 수 없습니다.", text_color="#e74c3c")
            return

        self._setting_hotkey = which
        
        btn_map = {
            "start": self.pages["settings"].hotkey_start_btn,
            "stop": self.pages["settings"].hotkey_stop_btn,
            "macro_record": self.pages["settings"].hotkey_macro_record_btn,
            "macro_start": self.pages["settings"].hotkey_macro_start_btn,
            "macro_stop": self.pages["settings"].hotkey_macro_stop_btn,
        }
        btn = btn_map.get(which)
        if btn:
            btn.configure(text="...", fg_color="#3498db")
        self.pages["settings"].settings_status.configure(text="⌨️ 원하는 키를 누르세요...", text_color="#f39c12")

        keyboard.on_press(self._on_hotkey_press)

    def _on_hotkey_press(self, event):
        if self._setting_hotkey is None:
            return
        keyboard.unhook_all()
        key = event.name.upper()
        which = self._setting_hotkey
        self._setting_hotkey = None
        self.after(0, lambda: self._apply_hotkey(which, key))

    def _apply_hotkey(self, which: str, key: str):
        self.teardown_hotkeys()
        
        config_key_map = {
            "start": "hotkey_start",
            "stop": "hotkey_stop",
            "macro_record": "hotkey_macro_record",
            "macro_start": "hotkey_macro_start",
            "macro_stop": "hotkey_macro_stop",
        }
        btn_map = {
            "start": self.pages["settings"].hotkey_start_btn,
            "stop": self.pages["settings"].hotkey_stop_btn,
            "macro_record": self.pages["settings"].hotkey_macro_record_btn,
            "macro_start": self.pages["settings"].hotkey_macro_start_btn,
            "macro_stop": self.pages["settings"].hotkey_macro_stop_btn,
        }
        
        config_key = config_key_map.get(which)
        btn = btn_map.get(which)
        
        if config_key:
            self.config[config_key] = key
        if btn:
            btn.configure(text=key, fg_color="#404040")

        self.setup_hotkeys()
        self.pages["autoclicker"].update_hotkey_labels()
        
        if which in ["macro_record", "macro_start", "macro_stop"]:
            self.pages["macro"].update_hotkey_labels()
        
        self._mark_settings_dirty(f"💾 단축키 변경됨: {key}")

    def setup_hotkeys(self):
        try:
            start_key = self.config.get("hotkey_start", "F6")
            stop_key = self.config.get("hotkey_stop", "F7")
            
            def on_start_press():
                if self._current_page == "autoclicker":
                    self.after(0, self.start)
            def on_stop_press():
                if self._current_page == "autoclicker":
                    self.after(0, self.stop)

            self._hotkey_start = keyboard.add_hotkey(start_key, on_start_press)
            self._hotkey_stop = keyboard.add_hotkey(stop_key, on_stop_press)
            
            macro_record_key = self.config.get("hotkey_macro_record", "F8")
            macro_start_key = self.config.get("hotkey_macro_start", "F9")
            macro_stop_key = self.config.get("hotkey_macro_stop", "F10")
            
            def on_macro_record_press():
                if self._current_page == "macro":
                    self.after(0, self._toggle_macro_record)
            def on_macro_start_press():
                if self._current_page == "macro":
                    self.after(0, self._start_macro_play)
            def on_macro_stop_press():
                if self._current_page == "macro":
                    self.after(0, self._stop_macro_play)

            self._hotkey_macro_record = keyboard.add_hotkey(macro_record_key, on_macro_record_press)
            self._hotkey_macro_start = keyboard.add_hotkey(macro_start_key, on_macro_start_press)
            self._hotkey_macro_stop = keyboard.add_hotkey(macro_stop_key, on_macro_stop_press)
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
            # 매크로 단축키 해제
            if self._hotkey_macro_record is not None:
                keyboard.remove_hotkey(self._hotkey_macro_record)
                self._hotkey_macro_record = None
            if self._hotkey_macro_start is not None:
                keyboard.remove_hotkey(self._hotkey_macro_start)
                self._hotkey_macro_start = None
            if self._hotkey_macro_stop is not None:
                keyboard.remove_hotkey(self._hotkey_macro_stop)
                self._hotkey_macro_stop = None
        except Exception:
            pass

    def _set_status(self, text: str):
        self.pages["autoclicker"].set_status(text)

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
        return self.pages["settings"].get_settings_state()

    def _mark_settings_dirty(self, message: str = "💾 변경 사항이 있습니다. 저장을 눌러주세요."):
        if self._suppress_dirty:
            return
        self._settings_dirty = True
        self.pages["settings"].settings_status.configure(text=message, text_color="#f39c12")

    def _refresh_settings_snapshot(self):
        self._settings_snapshot = self._get_settings_state()
        self._settings_dirty = False
        self.pages["settings"].settings_status.configure(text="", text_color="#2ecc71")

    def _ask_save_changes(self) -> str:
        dialog = ctk.CTkToplevel(self)
        dialog.title("변경 사항 확인")
        dialog.geometry("360x190")
        dialog.resizable(False, False)
        dialog.attributes("-topmost", True)
        dialog.transient(self)
        dialog.grab_set()
        
        try:
            base_dir = Path(__file__).resolve().parent.parent
            icon_path = base_dir / "assets" / "icon.ico"
            if icon_path.exists():
                dialog.iconbitmap(str(icon_path))
        except Exception:
            pass

        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - 180
        y = self.winfo_rooty() + (self.winfo_height() // 2) - 95
        dialog.geometry(f"+{x}+{y}")

        body = ctk.CTkFrame(dialog, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(body, text="변경 사항이 있습니다.", font=ctk.CTkFont(size=17, weight="bold")).pack(anchor="w", pady=(0, 6))
        ctk.CTkLabel(body, text="저장하지 않고 나가면 변경 내용이 사라집니다.\n저장하시겠습니까?", font=ctk.CTkFont(size=13), justify="left").pack(anchor="w")

        btns = ctk.CTkFrame(body, fg_color="transparent")
        btns.pack(side="bottom", fill="x", pady=(16, 0))

        choice = {"value": "cancel"}
        def _select(val: str):
            choice["value"] = val
            dialog.destroy()

        ctk.CTkButton(btns, text="저장 후 이동", width=100, fg_color="#3498db", hover_color="#2980b9", command=lambda: _select("yes")).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btns, text="저장 안 함", width=100, fg_color="#404040", hover_color="#505050", command=lambda: _select("no")).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btns, text="취소", width=80, fg_color="#e74c3c", hover_color="#c0392b", command=lambda: _select("cancel")).pack(side="right")

        dialog.focus_force()
        dialog.wait_window()
        return choice["value"]

    def _apply_settings_from_config(self):
        self._suppress_dirty = True
        self.pages["settings"].apply_settings(self.config)
        
        appearance_mode = self.config.get("appearance_mode", "dark")
        ctk.set_appearance_mode(appearance_mode)
        self._update_button_colors()
        self.pages["autoclicker"].update_hotkey_labels()
        self._suppress_dirty = False

    def _save_settings(self) -> bool:
        settings_page = self.pages["settings"]
        variance = self._parse_float(settings_page.variance_entry, "랜덤 변동값", min_value=0.0)
        if variance is None:
            settings_page.settings_status.configure(text="⚠️ 유효한 랜덤 변동값을 입력하세요.", text_color="#e74c3c")
            return False

        self.config["hotkey_start"] = settings_page.hotkey_start_btn.cget("text")
        self.config["hotkey_stop"] = settings_page.hotkey_stop_btn.cget("text")
        self.config["random_variance"] = str(variance)
        self.config["random_variance_enabled"] = bool(settings_page.variance_switch.get())
        
        # 매크로 단축키 저장
        self.config["hotkey_macro_record"] = settings_page.hotkey_macro_record_btn.cget("text")
        self.config["hotkey_macro_start"] = settings_page.hotkey_macro_start_btn.cget("text")
        self.config["hotkey_macro_stop"] = settings_page.hotkey_macro_stop_btn.cget("text")
        
        theme_mode = settings_page.theme_mode.get()
        self.config["appearance_mode"] = "light" if theme_mode == "라이트모드" else "dark"
        
        ctk.set_appearance_mode(self.config["appearance_mode"])
        self._update_button_colors()

        save_config(self.config)
        self.teardown_hotkeys()
        self.setup_hotkeys()
        self.pages["autoclicker"].update_hotkey_labels()
        self.pages["macro"].update_hotkey_labels()

        self._refresh_settings_snapshot()
        settings_page.settings_status.configure(text="✅ 설정이 저장되었습니다.", text_color="#2ecc71")
        return True

    def _on_variance_switch_change(self):
        settings_page = self.pages["settings"]
        is_enabled = settings_page.variance_switch.get()
        settings_page.variance_switch.configure(text="ON" if is_enabled else "OFF")
        settings_page.variance_entry.configure(state="normal" if is_enabled else "disabled")
        
        self.config["random_variance_enabled"] = is_enabled
        self._mark_settings_dirty()

    def _update_button_colors(self):
        current_mode = ctk.get_appearance_mode()
        text_color = "black" if current_mode == "Light" else "white"
        hover_color = "#e0e0e0" if current_mode == "Light" else "#3a3a3a"
        
        self.settings_btn.configure(text_color=text_color, hover_color=hover_color)
        self.back_btn.configure(text_color=text_color, hover_color=hover_color)
        self.pages["menu"].update_card_colors()

    def _on_theme_mode_change(self, mode: str):
        appearance_mode = "light" if mode == "라이트모드" else "dark"
        ctk.set_appearance_mode(appearance_mode)
        self.config["appearance_mode"] = appearance_mode
        save_config(self.config)
        self._mark_settings_dirty("💾 테마 모드가 변경되었습니다.")
        self._update_button_colors()

    def _save_variance(self):
        self._save_settings()
    
    def check_for_updates(self):
        def update_callback(has_update, latest_version, message):
            if has_update and latest_version:
                self.after(0, lambda: self._on_update_found(latest_version, message))
        check_update_async(update_callback)
    
    def _check_update_manual(self):
        settings_page = self.pages["settings"]
        settings_page.update_status_label.configure(text="확인 중...", text_color="#f39c12")
        settings_page.update_check_btn.configure(state="disabled")
        
        def update_callback(has_update, latest_version, message):
            self.after(0, lambda: self._on_update_check_complete(has_update, latest_version, message))
        check_update_async(update_callback)
    
    def _on_update_check_complete(self, has_update, latest_version, message):
        settings_page = self.pages["settings"]
        settings_page.update_check_btn.configure(state="normal")
        
        if has_update and latest_version:
            settings_page.update_status_label.configure(
                text=f"최신 버전: v{latest_version} 사용 가능", 
                text_color="#2ecc71"
            )
            settings_page.update_download_btn.configure(state="normal")
            self._latest_version = latest_version
        else:
            settings_page.update_status_label.configure(text="최신 버전입니다.", text_color="#2ecc71")
            settings_page.update_download_btn.configure(state="disabled")
    
    def _on_update_found(self, latest_version, message):
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
            settings_page = self.pages["settings"]
            settings_page.update_status_label.configure(
                text=f"최신 버전: v{latest_version} 사용 가능", 
                text_color="#2ecc71"
            )
            settings_page.update_download_btn.configure(state="normal")
    
    def _download_update(self):
        if not hasattr(self, '_latest_version'):
            self.pages["settings"].settings_status.configure(text="⚠️ 먼저 업데이트를 확인해주세요.", text_color="#e74c3c")
            return
        
        settings_page = self.pages["settings"]
        settings_page.update_download_btn.configure(state="disabled", text="다운로드 중...")
        settings_page.settings_status.configure(text="다운로드 중...", text_color="#f39c12")
        
        def download_thread():
            updater = Updater()
            success, message = updater.download_update()
            self.after(0, lambda: self._on_download_complete(success, message))
        
        threading.Thread(target=download_thread, daemon=True).start()
    
    def _on_download_complete(self, success, message):
        settings_page = self.pages["settings"]
        settings_page.update_download_btn.configure(state="normal", text="다운로드")
        
        if success:
            settings_page.settings_status.configure(text=f"✅ {message}", text_color="#2ecc71")
            result = messagebox.askyesno("다운로드 완료", f"{message}\n\n업데이트를 설치하시겠습니까?", icon="question")
            if result:
                updater = Updater()
                if updater.install_update(message.split(": ")[-1] if ": " in message else ""):
                    settings_page.settings_status.configure(text="✅ 업데이트 설치를 시작했습니다. 앱을 종료합니다.", text_color="#2ecc71")
                    self.after(2000, self.on_closing)
        else:
            settings_page.settings_status.configure(text=f"⚠️ {message}", text_color="#e74c3c")

    # ========== 매크로 관련 메서드 ==========
    def _toggle_macro_record(self):
        """매크로 녹화 시작/중지 토글 (단축키에서 호출)"""
        macro_page = self.pages["macro"]
        macro_page._toggle_record()

    def _start_macro_play(self):
        """매크로 재생 시작 (단축키에서 호출)"""
        macro_page = self.pages["macro"]
        macro_page._start_macro()

    def _stop_macro_play(self):
        """매크로 재생 중지 (단축키에서 호출)"""
        macro_page = self.pages["macro"]
        macro_page._stop_macro()

    def start_macro_record(self):
        """매크로 녹화 시작 (MacroPage에서 호출)"""
        macro_page = self.pages["macro"]
        
        # 녹화 대상 설정
        target = macro_page.record_target.get()
        self._macro_recorder.set_record_target(target)
        
        # 녹화 단축키 설정 (이 키는 녹화에서 제외)
        record_hotkey = self.config.get("hotkey_macro_record", "F8")
        self._macro_recorder.set_record_hotkey(record_hotkey)
        
        # 녹화 상태 콜백 설정
        def on_action_recorded(count):
            self.after(0, lambda: macro_page.update_record_status(count))
        
        self._macro_recorder.set_action_callback(on_action_recorded)
        
        # 녹화 시작
        self._macro_recorder.start_recording()
    
    def stop_macro_record(self) -> int:
        """매크로 녹화 중지 (MacroPage에서 호출)"""
        action_count = self._macro_recorder.stop_recording()
        self._macro_actions = self._macro_recorder.get_actions()
        return action_count
    
    def clear_macro(self):
        """매크로 초기화 (MacroPage에서 호출)"""
        self._macro_recorder.clear()
        self._macro_actions = []
    
    def start_macro_play(self, repeat_mode: str, repeat_count: str, speed: str):
        """매크로 재생 시작 (MacroPage에서 호출)"""
        if not self._macro_actions:
            self.pages["macro"].set_status("⚠️ 먼저 매크로를 녹화해주세요")
            return
        
        # 반복 횟수 파싱
        try:
            count = int(repeat_count)
            if count < 1:
                count = 1
        except ValueError:
            count = 1
        
        # 속도 파싱 (0.5x, 1x, 2x, 4x)
        speed_map = {"0.5x": 0.5, "1x": 1.0, "2x": 2.0, "4x": 4.0}
        speed_value = speed_map.get(speed, 1.0)
        
        # 콜백 설정
        def on_status(text):
            self.after(0, lambda: self.pages["macro"].set_status(text))
        
        def on_finish():
            self.after(0, self.pages["macro"].on_macro_finish)
        
        self._macro_player.set_callbacks(on_status, on_finish)
        
        # 재생 시작
        self._macro_player.play(
            self._macro_actions,
            repeat_mode=repeat_mode,
            repeat_count=count,
            speed=speed_value
        )
    
    def stop_macro_play(self):
        """매크로 재생 중지 (MacroPage에서 호출)"""
        self._macro_player.stop()
    
    def save_macro(self) -> Tuple[bool, str]:
        """매크로를 파일로 저장"""
        if not self._macro_actions:
            return False, "저장할 매크로가 없습니다"
        
        # 파일 저장 다이얼로그
        filepath = filedialog.asksaveasfilename(
            title="매크로 저장",
            defaultextension=".macro",
            filetypes=[
                ("매크로 파일", "*.macro"),
                ("JSON 파일", "*.json"),
                ("모든 파일", "*.*")
            ],
            initialfile="macro.macro"
        )
        
        if not filepath:
            return False, "저장이 취소되었습니다"
        
        success, message = save_macro_to_file(self._macro_actions, filepath)
        return success, message
    
    def load_macro(self) -> Tuple[bool, str]:
        filepath = filedialog.askopenfilename(
            title="매크로 불러오기",
            filetypes=[
                ("매크로 파일", "*.macro"),
                ("JSON 파일", "*.json"),
                ("모든 파일", "*.*")
            ]
        )
        
        if not filepath:
            return False, "불러오기가 취소되었습니다"
        
        actions, success, message = load_macro_from_file(filepath)
        
        if success:
            self._macro_actions = actions
            self.pages["macro"].update_record_status(len(actions))
            self.pages["macro"]._macro_actions = actions
        
        return success, message

    def start(self):
        with self._lock:
            if self._running:
                return
            self._running = True
            self._stop_event.clear()

        ac_page = self.pages["autoclicker"]
        click_type = ac_page.click_type.get()
        click_mode = ac_page.click_mode.get()
        button = Button.left if click_type == "좌클릭" else Button.right

        interval = None
        variance = 0.0
        if click_mode == "반복":
            interval = self._parse_float(ac_page.interval_sec, "클릭 간격(초)", min_value=0.0001)
            if interval is None:
                with self._lock:
                    self._running = False
                return
            
            variance_enabled = self.config.get("random_variance_enabled", True)
            if isinstance(variance_enabled, str):
                variance_enabled = variance_enabled.lower() == "true"
            
            if variance_enabled:
                try:
                    variance = float(self.config.get("random_variance", "0.03"))
                    if variance < 0: variance = 0.0
                except (ValueError, TypeError):
                    variance = 0.0

        self.config["click_interval"] = ac_page.interval_sec.get()
        self.config["click_type"] = click_type
        self.config["click_mode"] = click_mode
        save_config(self.config)

        ac_page.start_btn.configure(state="disabled")
        ac_page.stop_btn.configure(state="normal")
        
        clicker = Clicker(self.mouse, self._stop_event)
        
        if click_mode == "꾹누르기":
            self._set_status(f"🔄 {click_type} 꾹누르는 중...")
            self._click_thread = threading.Thread(
                target=clicker.hold_loop, args=(button,),
                kwargs={
                    "status_callback": lambda msg: self.after(0, lambda: self._set_status(msg)),
                    "finish_callback": lambda: self.after(0, self._finish)
                },
                daemon=True
            )
        else:
            self._set_status("🔄 실행 중...")
            self._click_thread = threading.Thread(
                target=clicker.click_loop, args=(button, interval, variance),
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
        ac_page = self.pages["autoclicker"]
        ac_page.start_btn.configure(state="normal")
        ac_page.stop_btn.configure(state="disabled")
        self._set_status("⏸️ 대기 중...")

    def on_closing(self):
        self._stop_event.set()
        self.teardown_hotkeys()
        self.destroy()
