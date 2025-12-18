import customtkinter as ctk
from autoclicker.version import __version__
from .base import BasePage

class AutoClickerPage(BasePage):
    def setup_ui(self):
        """오토마우스 페이지 UI 생성"""
        # 클릭 설정 박스
        box = ctk.CTkFrame(self)
        box.pack(pady=10, fill="x")

        # 클릭 타입
        row1 = ctk.CTkFrame(box)
        row1.pack(padx=15, pady=(15, 10), fill="x")

        ctk.CTkLabel(row1, text="클릭 버튼", font=ctk.CTkFont(size=16)).pack(side="left", padx=15)
        self.click_type = ctk.CTkSegmentedButton(row1, values=["좌클릭", "우클릭"], height=35)
        self.click_type.set(self.controller.config.get("click_type", "좌클릭"))
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
        self.click_mode.set(self.controller.config.get("click_mode", "반복"))
        self.click_mode.pack(side="right", padx=15)

        # 간격(초)
        self.interval_row = ctk.CTkFrame(box)
        self.interval_row.pack(padx=15, pady=10, fill="x")

        self.interval_label = ctk.CTkLabel(self.interval_row, text="클릭 간격 (초)", font=ctk.CTkFont(size=16))
        self.interval_label.pack(side="left", padx=15)
        self.interval_sec = ctk.CTkEntry(self.interval_row, width=180, height=35, font=ctk.CTkFont(size=14))
        self.interval_sec.insert(0, self.controller.config.get("click_interval", "0.1"))
        self.interval_sec.pack(side="right", padx=15)

        self.hint = ctk.CTkLabel(
            box,
            text="예: 1초=1.0 / 0.1초=0.1 / 1ms=0.001",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        )
        self.hint.pack(padx=15, pady=(0, 15))

        # 초기 모드에 따라 간격 표시/숨김
        self._on_mode_change(self.controller.config.get("click_mode", "반복"))

        # 버튼
        btns = ctk.CTkFrame(self)
        btns.pack(pady=15, fill="x")

        self.start_btn = ctk.CTkButton(
            btns, text=f"▶️ 시작 ({self.controller.config.get('hotkey_start', 'F6')})", height=55,
            fg_color="#2ecc71", hover_color="#27ae60",
            font=ctk.CTkFont(size=18, weight="bold"),
            command=self.controller.start
        )
        self.start_btn.pack(side="left", padx=15, pady=15, expand=True, fill="x")

        self.stop_btn = ctk.CTkButton(
            btns, text=f"⏹️ 중지 ({self.controller.config.get('hotkey_stop', 'F7')})", height=55,
            fg_color="#e74c3c", hover_color="#c0392b",
            font=ctk.CTkFont(size=18, weight="bold"),
            command=self.controller.stop,
            state="disabled"
        )
        self.stop_btn.pack(side="right", padx=15, pady=15, expand=True, fill="x")

        # 상태
        self.status = ctk.CTkLabel(self, text="⏸️ 대기 중...", font=ctk.CTkFont(size=16))
        self.status.pack(pady=(12, 0))

        self.hotkey_display = ctk.CTkLabel(
            self,
            text=f"단축키: {self.controller.config.get('hotkey_start', 'F6')} 시작 / {self.controller.config.get('hotkey_stop', 'F7')} 중지",
            font=ctk.CTkFont(size=13), text_color="gray"
        )
        self.hotkey_display.pack(pady=(6, 15))
        
        # 하단 정보 표시 (저작권 + 버전)
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", pady=(10, 0))
        
        ctk.CTkLabel(
            bottom_frame,
            text=f"© 2025 Dugyeon. All rights reserved.",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(side="left", padx=5)
        
        ctk.CTkLabel(
            bottom_frame,
            text=f"v{__version__}",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(side="right", padx=5)

    def _on_mode_change(self, mode: str):
        """클릭 모드 변경 시 UI 업데이트"""
        if mode == "꾹누르기":
            self.interval_sec.configure(state="disabled")
            self.interval_label.configure(text_color="gray")
            self.hint.configure(text="버튼을 누른 상태로 유지합니다")
        else:
            self.interval_sec.configure(state="normal")
            self.interval_label.configure(text_color=("gray10", "gray90"))
            self.hint.configure(text="예: 1초=1.0 / 0.1초=0.1 / 1ms=0.001")

    def update_hotkey_labels(self):
        """단축키 변경 시 레이블 업데이트"""
        start = self.controller.config.get("hotkey_start", "F6")
        stop = self.controller.config.get("hotkey_stop", "F7")
        self.start_btn.configure(text=f"▶️ 시작 ({start})")
        self.stop_btn.configure(text=f"⏹️ 중지 ({stop})")
        self.hotkey_display.configure(text=f"단축키: {start} 시작 / {stop} 중지")

    def set_status(self, text: str):
        self.status.configure(text=text)
