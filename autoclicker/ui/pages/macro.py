import customtkinter as ctk
from autoclicker.version import __version__
from .base import BasePage


class MacroPage(BasePage):
    def setup_ui(self):
        record_box = ctk.CTkFrame(self)
        record_box.pack(pady=10, fill="x")

        ctk.CTkLabel(
            record_box, 
            text="🎬 매크로 녹화", 
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(padx=15, pady=(15, 10), anchor="w")

        row_target = ctk.CTkFrame(record_box)
        row_target.pack(padx=15, pady=10, fill="x")

        ctk.CTkLabel(row_target, text="녹화 대상", font=ctk.CTkFont(size=16)).pack(side="left", padx=15)
        self.record_target = ctk.CTkSegmentedButton(
            row_target, 
            values=["키보드", "마우스", "키보드+마우스"],
            height=35
        )
        self.record_target.set(self.controller.config.get("macro_target", "키보드+마우스"))
        self.record_target.pack(side="right", padx=15)

        record_btns = ctk.CTkFrame(record_box)
        record_btns.pack(padx=15, pady=(5, 15), fill="x")

        record_key = self.controller.config.get("hotkey_macro_record", "F8")
        self.record_btn = ctk.CTkButton(
            record_btns, 
            text=f"🔴 녹화 시작 ({record_key})", 
            height=45,
            fg_color="#3498db", 
            hover_color="#2980b9",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._toggle_record
        )
        self.record_btn.pack(side="left", padx=(15, 10), expand=True, fill="x")

        self.clear_btn = ctk.CTkButton(
            record_btns, 
            text="🗑️ 초기화", 
            height=45,
            fg_color="#555555", 
            hover_color="#444444",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._clear_macro
        )
        self.clear_btn.pack(side="right", padx=(10, 15), expand=True, fill="x")

        self.record_status = ctk.CTkLabel(
            record_box, 
            text="녹화된 동작: 0개", 
            font=ctk.CTkFont(size=13),
            text_color="gray"
        )
        self.record_status.pack(padx=15, pady=(0, 10))

        file_btns = ctk.CTkFrame(record_box)
        file_btns.pack(padx=15, pady=(0, 15), fill="x")

        self.save_btn = ctk.CTkButton(
            file_btns, 
            text="💾 저장", 
            height=38,
            fg_color="#555555", 
            hover_color="#444444",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._save_macro
        )
        self.save_btn.pack(side="left", padx=(15, 10), expand=True, fill="x")

        self.load_btn = ctk.CTkButton(
            file_btns, 
            text="📂 불러오기", 
            height=38,
            fg_color="#555555", 
            hover_color="#444444",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._load_macro
        )
        self.load_btn.pack(side="right", padx=(10, 15), expand=True, fill="x")

        play_box = ctk.CTkFrame(self)
        play_box.pack(pady=10, fill="x")

        ctk.CTkLabel(
            play_box, 
            text="▶️ 매크로 재생", 
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(padx=15, pady=(15, 10), anchor="w")

        row_repeat = ctk.CTkFrame(play_box)
        row_repeat.pack(padx=15, pady=10, fill="x")

        ctk.CTkLabel(row_repeat, text="반복 모드", font=ctk.CTkFont(size=16)).pack(side="left", padx=15)
        self.repeat_mode = ctk.CTkSegmentedButton(
            row_repeat, 
            values=["1회", "반복", "무한"],
            command=self._on_repeat_mode_change,
            height=35
        )
        self.repeat_mode.set(self.controller.config.get("macro_repeat_mode", "1회"))
        self.repeat_mode.pack(side="right", padx=15)

        self.repeat_count_row = ctk.CTkFrame(play_box)
        self.repeat_count_row.pack(padx=15, pady=10, fill="x")

        self.repeat_count_label = ctk.CTkLabel(
            self.repeat_count_row, 
            text="반복 횟수", 
            font=ctk.CTkFont(size=16)
        )
        self.repeat_count_label.pack(side="left", padx=15)
        
        self.repeat_count = ctk.CTkEntry(
            self.repeat_count_row, 
            width=180, 
            height=35, 
            font=ctk.CTkFont(size=14)
        )
        self.repeat_count.insert(0, self.controller.config.get("macro_repeat_count", "10"))
        self.repeat_count.pack(side="right", padx=15)

        row_speed = ctk.CTkFrame(play_box)
        row_speed.pack(padx=15, pady=10, fill="x")

        ctk.CTkLabel(row_speed, text="재생 속도", font=ctk.CTkFont(size=16)).pack(side="left", padx=15)
        self.play_speed = ctk.CTkSegmentedButton(
            row_speed, 
            values=["0.5x", "1x", "2x", "4x"],
            height=35
        )
        self.play_speed.set(self.controller.config.get("macro_speed", "1x"))
        self.play_speed.pack(side="right", padx=15)

        self.speed_hint = ctk.CTkLabel(
            play_box,
            text="1x = 녹화된 속도 그대로 재생",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        )
        self.speed_hint.pack(padx=15, pady=(0, 15))

        self._on_repeat_mode_change(self.controller.config.get("macro_repeat_mode", "1회"))

        btns = ctk.CTkFrame(self)
        btns.pack(pady=15, fill="x")

        self.start_btn = ctk.CTkButton(
            btns, 
            text=f"▶️ 재생 ({self.controller.config.get('hotkey_macro_start', 'F9')})", 
            height=55,
            fg_color="#3498db", 
            hover_color="#2980b9",
            font=ctk.CTkFont(size=18, weight="bold"),
            command=self._start_macro
        )
        self.start_btn.pack(side="left", padx=15, pady=15, expand=True, fill="x")

        self.stop_btn = ctk.CTkButton(
            btns, 
            text=f"⏹️ 중지 ({self.controller.config.get('hotkey_macro_stop', 'F10')})", 
            height=55,
            fg_color="#555555", 
            hover_color="#444444",
            font=ctk.CTkFont(size=18, weight="bold"),
            command=self._stop_macro,
            state="disabled"
        )
        self.stop_btn.pack(side="right", padx=15, pady=15, expand=True, fill="x")

        self.status = ctk.CTkLabel(self, text="⏸️ 대기 중...", font=ctk.CTkFont(size=16))
        self.status.pack(pady=(12, 0))

        self.hotkey_display = ctk.CTkLabel(
            self,
            text=f"단축키: {self.controller.config.get('hotkey_macro_record', 'F8')} 녹화 / {self.controller.config.get('hotkey_macro_start', 'F9')} 재생 / {self.controller.config.get('hotkey_macro_stop', 'F10')} 중지",
            font=ctk.CTkFont(size=13), 
            text_color="gray"
        )
        self.hotkey_display.pack(pady=(6, 15))

        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", pady=(10, 0))

        ctk.CTkLabel(
            bottom_frame,
            text="© 2025 Dugyeon. All rights reserved.",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(side="left", padx=5)

        ctk.CTkLabel(
            bottom_frame,
            text=f"v{__version__}",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(side="right", padx=5)

        # 내부 상태 변수
        self._recording = False
        self._playing = False
        self._macro_actions = []

    def _on_repeat_mode_change(self, mode: str):
        if mode == "반복":
            self.repeat_count_row.pack(padx=15, pady=10, fill="x", after=self.repeat_mode.master)
            self.repeat_count.configure(state="normal")
            self.repeat_count_label.configure(text_color=("gray10", "gray90"))
        else:
            self.repeat_count_row.pack_forget()

    def _toggle_record(self):
        if self._recording:
            self._stop_record()
        else:
            self._start_record()

    def _start_record(self):
        self._recording = True
        self._macro_actions = []
        record_key = self.controller.config.get("hotkey_macro_record", "F8")
        self.record_btn.configure(text=f"⏹️ 녹화 중지 ({record_key})", fg_color="#e74c3c", hover_color="#c0392b")
        self.status.configure(text="🔴 녹화 중... (동작을 수행하세요)")
        self.record_status.configure(text="녹화된 동작: 0개")
        self.start_btn.configure(state="disabled")
        
        if hasattr(self.controller, 'start_macro_record'):
            self.controller.start_macro_record()

    def _stop_record(self):
        self._recording = False
        record_key = self.controller.config.get("hotkey_macro_record", "F8")
        self.record_btn.configure(text=f"🔴 녹화 시작 ({record_key})", fg_color="#3498db", hover_color="#2980b9")
        self.status.configure(text="⏸️ 대기 중...")
        self.start_btn.configure(state="normal")
        
        if hasattr(self.controller, 'stop_macro_record'):
            action_count = self.controller.stop_macro_record()
            self._macro_actions = getattr(self.controller, '_macro_actions', [])
            self.record_status.configure(text=f"녹화된 동작: {len(self._macro_actions)}개")

    def _clear_macro(self):
        self._macro_actions = []
        self.record_status.configure(text="녹화된 동작: 0개")
        self.status.configure(text="⏸️ 매크로가 초기화되었습니다")
        
        if hasattr(self.controller, 'clear_macro'):
            self.controller.clear_macro()

    def _save_macro(self):
        if not self._macro_actions and not getattr(self.controller, '_macro_actions', []):
            self.status.configure(text="⚠️ 저장할 매크로가 없습니다")
            return
        
        if hasattr(self.controller, 'save_macro'):
            success, message = self.controller.save_macro()
            if success:
                self.status.configure(text=f"✅ {message}")
            else:
                self.status.configure(text=f"⚠️ {message}")

    def _load_macro(self):
        if hasattr(self.controller, 'load_macro'):
            success, message = self.controller.load_macro()
            if success:
                self._macro_actions = getattr(self.controller, '_macro_actions', [])
                self.status.configure(text=f"✅ {message}")
            else:
                self.status.configure(text=f"⚠️ {message}")

    def _start_macro(self):
        if not self._macro_actions and not getattr(self.controller, '_macro_actions', []):
            self.status.configure(text="⚠️ 먼저 매크로를 녹화해주세요")
            return

        self._playing = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.record_btn.configure(state="disabled")
        self.status.configure(text="▶️ 매크로 재생 중...")
        
        self.controller.config["macro_target"] = self.record_target.get()
        self.controller.config["macro_repeat_mode"] = self.repeat_mode.get()
        self.controller.config["macro_repeat_count"] = self.repeat_count.get()
        self.controller.config["macro_speed"] = self.play_speed.get()
        
        if hasattr(self.controller, 'start_macro_play'):
            self.controller.start_macro_play(
                repeat_mode=self.repeat_mode.get(),
                repeat_count=self.repeat_count.get(),
                speed=self.play_speed.get()
            )

    def _stop_macro(self):
        self._playing = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.record_btn.configure(state="normal")
        self.status.configure(text="⏸️ 대기 중...")
        
        if hasattr(self.controller, 'stop_macro_play'):
            self.controller.stop_macro_play()

    def update_record_status(self, count: int):
        self.record_status.configure(text=f"녹화된 동작: {count}개")

    def set_status(self, text: str):
        self.status.configure(text=text)

    def update_hotkey_labels(self):
        record = self.controller.config.get("hotkey_macro_record", "F8")
        start = self.controller.config.get("hotkey_macro_start", "F9")
        stop = self.controller.config.get("hotkey_macro_stop", "F10")
        self.record_btn.configure(text=f"🔴 녹화 시작 ({record})" if not self._recording else f"⏹️ 녹화 중지 ({record})")
        self.start_btn.configure(text=f"▶️ 재생 ({start})")
        self.stop_btn.configure(text=f"⏹️ 중지 ({stop})")
        self.hotkey_display.configure(text=f"단축키: {record} 녹화 / {start} 재생 / {stop} 중지")

    def on_macro_finish(self):
        self._playing = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.record_btn.configure(state="normal")
        self.status.configure(text="✅ 매크로 재생 완료")

