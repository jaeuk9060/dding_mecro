"""
Auto Clicker
- 좌/우클릭 선택
- 초 단위 간격 (예: 0.1, 0.0001)
- 지정 간격마다 1회 클릭
- 단축키 설정 가능

필수:
  pip install customtkinter pynput keyboard
"""

import os
import json
import time
import threading

import customtkinter as ctk
from pynput.mouse import Button, Controller as MouseController
import keyboard  # 글로벌 단축키


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# 설정 파일 경로
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

# 기본 설정
DEFAULT_CONFIG = {
    "hotkey_start": "F6",
    "hotkey_stop": "F7",
    "click_interval": "0.1",
    "click_type": "좌클릭",
    "click_mode": "반복"
}


def load_config():
    """설정 파일 로드"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                # 누락된 키 채우기
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(config):
    """설정 파일 저장"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


class AutoClickerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("🖱️ Auto Clicker")
        self.geometry("400x400")
        self.resizable(False, False)

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

        self.create_widgets()
        self.setup_hotkeys()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    # ---------------- UI ----------------
    def create_widgets(self):
        # 상단 헤더 (타이틀 + 설정 버튼)
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 5))

        self.title_label = ctk.CTkLabel(
            header,
            text="🖱️ 자동 클릭",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        self.title_label.pack(side="left", padx=10)

        self.settings_btn = ctk.CTkButton(
            header,
            text="⚙️",
            width=40,
            height=40,
            font=ctk.CTkFont(size=20),
            fg_color="transparent",
            hover_color="#3a3a3a",
            command=self.toggle_page
        )
        self.settings_btn.pack(side="right", padx=5)

        # 메인 페이지 컨테이너
        self.main_page = ctk.CTkFrame(self, fg_color="transparent")
        self.main_page.pack(fill="both", expand=True, padx=20, pady=10)

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
        row1.pack(padx=10, pady=(10, 6), fill="x")

        ctk.CTkLabel(row1, text="클릭 버튼", font=ctk.CTkFont(size=13)).pack(side="left", padx=10)
        self.click_type = ctk.CTkSegmentedButton(row1, values=["좌클릭", "우클릭"])
        self.click_type.set(self.config.get("click_type", "좌클릭"))
        self.click_type.pack(side="right", padx=10)

        # 클릭 모드
        row_mode = ctk.CTkFrame(box)
        row_mode.pack(padx=10, pady=6, fill="x")

        ctk.CTkLabel(row_mode, text="클릭 모드", font=ctk.CTkFont(size=13)).pack(side="left", padx=10)
        self.click_mode = ctk.CTkSegmentedButton(
            row_mode, 
            values=["반복", "꾹누르기"],
            command=self._on_mode_change
        )
        self.click_mode.set(self.config.get("click_mode", "반복"))
        self.click_mode.pack(side="right", padx=10)

        # 간격(초)
        self.interval_row = ctk.CTkFrame(box)
        self.interval_row.pack(padx=10, pady=6, fill="x")

        self.interval_label = ctk.CTkLabel(self.interval_row, text="클릭 간격 (초)", font=ctk.CTkFont(size=13))
        self.interval_label.pack(side="left", padx=10)
        self.interval_sec = ctk.CTkEntry(self.interval_row, width=140)
        self.interval_sec.insert(0, self.config.get("click_interval", "0.1"))
        self.interval_sec.pack(side="right", padx=10)

        self.hint = ctk.CTkLabel(
            box,
            text="예: 1초=1.0 / 0.1초=0.1 / 1ms=0.001",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        self.hint.pack(padx=10, pady=(0, 10))

        # 초기 모드에 따라 간격 표시/숨김
        self._on_mode_change(self.config.get("click_mode", "반복"))

        # 버튼
        btns = ctk.CTkFrame(self.main_page)
        btns.pack(pady=10, fill="x")

        self.start_btn = ctk.CTkButton(
            btns, text=f"▶️ 시작 ({self.config.get('hotkey_start', 'F6')})", height=45,
            fg_color="#2ecc71", hover_color="#27ae60",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.start
        )
        self.start_btn.pack(side="left", padx=10, pady=10, expand=True, fill="x")

        self.stop_btn = ctk.CTkButton(
            btns, text=f"⏹️ 중지 ({self.config.get('hotkey_stop', 'F7')})", height=45,
            fg_color="#e74c3c", hover_color="#c0392b",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.stop,
            state="disabled"
        )
        self.stop_btn.pack(side="right", padx=10, pady=10, expand=True, fill="x")

        # 상태
        self.status = ctk.CTkLabel(self.main_page, text="⏸️ 대기 중...", font=ctk.CTkFont(size=13))
        self.status.pack(pady=(8, 0))

        self.hotkey_display = ctk.CTkLabel(
            self.main_page,
            text=f"단축키: {self.config.get('hotkey_start', 'F6')} 시작 / {self.config.get('hotkey_stop', 'F7')} 중지",
            font=ctk.CTkFont(size=11), text_color="gray"
        )
        self.hotkey_display.pack(pady=(4, 10))

    def _create_settings_page(self):
        """설정 페이지 UI 생성"""
        # 시작 단축키 항목
        start_item = ctk.CTkFrame(self.settings_page)
        start_item.pack(pady=(5, 8), fill="x")

        start_left = ctk.CTkFrame(start_item, fg_color="transparent")
        start_left.pack(side="left", padx=15, pady=12)
        
        ctk.CTkLabel(
            start_left, 
            text="시작 단축키", 
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")
        ctk.CTkLabel(
            start_left, 
            text="클릭 자동화를 시작합니다", 
            font=ctk.CTkFont(size=11), 
            text_color="gray"
        ).pack(anchor="w")

        self.hotkey_start_btn = ctk.CTkButton(
            start_item,
            text=self.config.get("hotkey_start", "F6"),
            width=80,
            height=32,
            fg_color="#404040",
            hover_color="#505050",
            font=ctk.CTkFont(size=13),
            command=lambda: self._start_hotkey_setting("start")
        )
        self.hotkey_start_btn.pack(side="right", padx=15, pady=12)

        # 중지 단축키 항목
        stop_item = ctk.CTkFrame(self.settings_page)
        stop_item.pack(pady=(0, 8), fill="x")

        stop_left = ctk.CTkFrame(stop_item, fg_color="transparent")
        stop_left.pack(side="left", padx=15, pady=12)
        
        ctk.CTkLabel(
            stop_left, 
            text="중지 단축키", 
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")
        ctk.CTkLabel(
            stop_left, 
            text="클릭 자동화를 중지합니다", 
            font=ctk.CTkFont(size=11), 
            text_color="gray"
        ).pack(anchor="w")

        self.hotkey_stop_btn = ctk.CTkButton(
            stop_item,
            text=self.config.get("hotkey_stop", "F7"),
            width=80,
            height=32,
            fg_color="#404040",
            hover_color="#505050",
            font=ctk.CTkFont(size=13),
            command=lambda: self._start_hotkey_setting("stop")
        )
        self.hotkey_stop_btn.pack(side="right", padx=15, pady=12)

        # 안내 문구
        hint_label = ctk.CTkLabel(
            self.settings_page,
            text="💡 버튼을 클릭한 후 원하는 키를 누르세요",
            font=ctk.CTkFont(size=11),
            text_color="#888888",
        )
        hint_label.pack(pady=(15, 5))

        # 설정 상태 메시지
        self.settings_status = ctk.CTkLabel(
            self.settings_page,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#2ecc71"
        )
        self.settings_status.pack(pady=(5, 10))

    def toggle_page(self):
        """메인 페이지 ↔ 설정 페이지 전환"""
        if self._current_page == "main":
            # 설정 페이지로 전환
            self.main_page.pack_forget()
            self.settings_page.pack(fill="both", expand=True, padx=20, pady=10)
            self.title_label.configure(text="⚙️ 설정")
            self.settings_btn.configure(text="←")
            self._current_page = "settings"
        else:
            # 메인 페이지로 전환
            self.settings_page.pack_forget()
            self.main_page.pack(fill="both", expand=True, padx=20, pady=10)
            self.title_label.configure(text="🖱️ 자동 클릭")
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

        # 설정 저장
        save_config(self.config)

        # 단축키 다시 등록
        self.setup_hotkeys()

        # UI 업데이트
        self.hotkey_display.configure(
            text=f"단축키: {self.config['hotkey_start']} 시작 / {self.config['hotkey_stop']} 중지"
        )
        self.settings_status.configure(text=f"✅ 단축키 변경됨: {key}", text_color="#2ecc71")

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
        if click_mode == "반복":
            interval = self._parse_float(self.interval_sec, "클릭 간격(초)", min_value=0.0001)
            if interval is None:
                with self._lock:
                    self._running = False
                return

        # 설정 저장
        self.config["click_interval"] = self.interval_sec.get()
        self.config["click_type"] = click_type
        self.config["click_mode"] = click_mode
        save_config(self.config)

        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        
        if click_mode == "꾹누르기":
            self._set_status(f"🔄 {click_type} 꾹누르는 중...")
            self._click_thread = threading.Thread(
                target=self._hold_loop,
                args=(button,),
                daemon=True
            )
        else:
            self._set_status("🔄 실행 중...")
            self._click_thread = threading.Thread(
                target=self._click_loop,
                args=(button, interval),
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

    # ---------------- Worker loops ----------------
    def _click_loop(self, button: Button, interval_sec: float):
        """
        반복 클릭 모드:
        드리프트 보정형 스케줄로 next_tick 기준으로 주기를 유지
        """
        try:
            next_tick = time.perf_counter()
            while not self._stop_event.is_set():
                now = time.perf_counter()
                remain = next_tick - now
                if remain > 0:
                    if remain > 0.005:
                        time.sleep(remain - 0.001)
                    continue

                # 클릭 1회
                self.mouse.click(button)

                # 다음 tick 예약
                next_tick += interval_sec

                # next_tick이 너무 뒤처지면 현재 기준으로 재정렬
                if (time.perf_counter() - next_tick) > (interval_sec * 3):
                    next_tick = time.perf_counter() + interval_sec

        except Exception as e:
            self.after(0, lambda: self._set_status(f"⚠️ 클릭 루프 오류: {e}"))
        finally:
            self.after(0, self._finish)

    def _hold_loop(self, button: Button):
        """
        꾹누르기 모드:
        버튼을 누른 상태 유지, 중지 시 뗌
        """
        try:
            # 버튼 누르기
            self.mouse.press(button)
            
            # 중지 신호가 올 때까지 대기
            while not self._stop_event.is_set():
                time.sleep(0.05)

        except Exception as e:
            self.after(0, lambda: self._set_status(f"⚠️ 꾹누르기 오류: {e}"))
        finally:
            # 버튼 떼기
            try:
                self.mouse.release(button)
            except Exception:
                pass
            self.after(0, self._finish)

    # ---------------- Cleanup ----------------
    def on_closing(self):
        self._stop_event.set()
        self.teardown_hotkeys()
        self.destroy()


if __name__ == "__main__":
    app = AutoClickerApp()
    app.mainloop()
