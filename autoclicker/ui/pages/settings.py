import customtkinter as ctk
import threading
from pathlib import Path
from autoclicker.version import __version__
from autoclicker.config import load_config, save_config
from autoclicker.updater import Updater
from .base import BasePage

class SettingsPage(BasePage):
    def setup_ui(self):
        """설정 페이지 UI 생성"""
        # 스크롤 가능한 컨테이너
        scrollable_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scrollable_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # ========== 오토마우스 설정 섹션 프레임 ==========
        self.autoclicker_settings_section = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        self.autoclicker_settings_section.pack(fill="x", padx=0, pady=0)

        ctk.CTkLabel(
            self.autoclicker_settings_section,
            text="오토마우스 설정",
            font=ctk.CTkFont(size=20, weight="bold"),
            anchor="w"
        ).pack(fill="x", padx=20, pady=(15, 10))
        
        # 시작 단축키 항목
        self.hotkey_start_btn = self._create_setting_item(
            self.autoclicker_settings_section, "시작 단축키", "클릭 자동화를 시작합니다",
            self.controller.config.get("hotkey_start", "F6"),
            lambda: self.controller._start_hotkey_setting("start")
        )

        # 중지 단축키 항목
        self.hotkey_stop_btn = self._create_setting_item(
            self.autoclicker_settings_section, "중지 단축키", "클릭 자동화를 중지합니다",
            self.controller.config.get("hotkey_stop", "F7"),
            lambda: self.controller._start_hotkey_setting("stop")
        )

        # 랜덤 변동값 항목
        self._create_variance_item(self.autoclicker_settings_section)

        # ========== 메인 설정 섹션 프레임 ==========
        self.main_settings_section = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        self.main_settings_section.pack(fill="x", padx=0, pady=0)

        ctk.CTkLabel(
            self.main_settings_section,
            text="메인 설정",
            font=ctk.CTkFont(size=20, weight="bold"),
            anchor="w"
        ).pack(fill="x", padx=20, pady=(10, 10))

        # 테마 모드 항목
        self._create_theme_item(self.main_settings_section)

        # 업데이트 항목
        self._create_update_item(self.main_settings_section)

        # 하단 공통 요소
        self.settings_footer = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        self.settings_footer.pack(fill="x", padx=0, pady=0)

        ctk.CTkLabel(
            self.settings_footer,
            text="💡 버튼을 클릭한 후 원하는 키를 누르세요",
            font=ctk.CTkFont(size=13),
            text_color="#888888",
        ).pack(pady=(10, 8), padx=20)

        self.settings_status = ctk.CTkLabel(
            self.settings_footer,
            text="",
            font=ctk.CTkFont(size=14),
            text_color="#2ecc71"
        )
        self.settings_status.pack(pady=(8, 15), padx=20)

        self.save_settings_btn = ctk.CTkButton(
            self.settings_footer,
            text="설정 저장",
            width=140,
            height=42,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#3498db",
            hover_color="#2980b9",
            command=self.controller._save_settings
        )
        self.save_settings_btn.pack(pady=(5, 20))

    def _create_setting_item(self, parent, title, desc, btn_text, command):
        item = ctk.CTkFrame(parent)
        item.pack(pady=(0, 12), fill="x", padx=20)

        left = ctk.CTkFrame(item, fg_color="transparent")
        left.pack(side="left", padx=20, pady=15)
        
        ctk.CTkLabel(left, text=title, font=ctk.CTkFont(size=17, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(left, text=desc, font=ctk.CTkFont(size=13), text_color="gray").pack(anchor="w")

        btn = ctk.CTkButton(
            item, text=btn_text, width=100, height=40,
            fg_color="#404040", hover_color="#505050",
            font=ctk.CTkFont(size=15), command=command
        )
        btn.pack(side="right", padx=20, pady=15)
        return btn

    def _create_variance_item(self, parent):
        item = ctk.CTkFrame(parent)
        item.pack(pady=(0, 20), fill="x", padx=20)

        left = ctk.CTkFrame(item, fg_color="transparent")
        left.pack(side="left", padx=20, pady=15)
        
        ctk.CTkLabel(left, text="랜덤 변동값 (±초)", font=ctk.CTkFont(size=17, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(left, text="클릭 간격에 랜덤 변동을 추가합니다", font=ctk.CTkFont(size=13), text_color="gray").pack(anchor="w")

        right = ctk.CTkFrame(item, fg_color="transparent")
        right.pack(side="right", padx=20, pady=15)
        
        variance_enabled = self.controller.config.get("random_variance_enabled", True)
        if isinstance(variance_enabled, str):
            variance_enabled = variance_enabled.lower() == "true"
        
        self.variance_switch = ctk.CTkSwitch(
            right, text="ON" if variance_enabled else "OFF",
            command=self.controller._on_variance_switch_change
        )
        self.variance_switch.pack(side="left", padx=(0, 12))
        if variance_enabled:
            self.variance_switch.select()
        
        input_frame = ctk.CTkFrame(right, fg_color="transparent")
        input_frame.pack(side="left")
        
        self.variance_entry = ctk.CTkEntry(input_frame, width=120, height=40, font=ctk.CTkFont(size=14))
        self.variance_entry.insert(0, self.controller.config.get("random_variance", "0.03"))
        self.variance_entry.pack(side="left", padx=(0, 8))
        self.variance_entry.bind("<KeyRelease>", lambda e: self.controller._mark_settings_dirty())
        
        if not variance_enabled:
            self.variance_entry.configure(state="disabled")
        
        ctk.CTkButton(
            input_frame, text="저장", width=60, height=40,
            font=ctk.CTkFont(size=13), command=self.controller._save_variance
        ).pack(side="left")

    def _create_theme_item(self, parent):
        item = ctk.CTkFrame(parent)
        item.pack(pady=(0, 12), fill="x", padx=20)

        left = ctk.CTkFrame(item, fg_color="transparent")
        left.pack(side="left", padx=20, pady=15)
        
        ctk.CTkLabel(left, text="테마 모드", font=ctk.CTkFont(size=17, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(left, text="다크모드 또는 라이트모드를 선택합니다", font=ctk.CTkFont(size=13), text_color="gray").pack(anchor="w")

        right = ctk.CTkFrame(item, fg_color="transparent")
        right.pack(side="right", padx=20, pady=15)
        
        appearance_mode = self.controller.config.get("appearance_mode", "dark")
        self.theme_mode = ctk.CTkSegmentedButton(
            right, values=["다크모드", "라이트모드"],
            command=self.controller._on_theme_mode_change,
            height=40, width=200
        )
        self.theme_mode.set("라이트모드" if appearance_mode == "light" else "다크모드")
        self.theme_mode.pack()

    def _create_update_item(self, parent):
        item = ctk.CTkFrame(parent)
        item.pack(pady=(0, 20), fill="x", padx=20)

        left = ctk.CTkFrame(item, fg_color="transparent")
        left.pack(side="left", padx=20, pady=15, fill="both", expand=True)
        
        ctk.CTkLabel(left, text="업데이트", font=ctk.CTkFont(size=17, weight="bold")).pack(anchor="w")
        
        version_info = ctk.CTkFrame(left, fg_color="transparent")
        version_info.pack(anchor="w", pady=(5, 0))
        ctk.CTkLabel(version_info, text=f"현재 버전: v{__version__}", font=ctk.CTkFont(size=13), text_color="gray").pack(side="left")
        
        right = ctk.CTkFrame(item, fg_color="transparent")
        right.pack(side="right", padx=20, pady=15)
        
        btns_frame = ctk.CTkFrame(right, fg_color="transparent")
        btns_frame.pack()
        
        self.update_check_btn = ctk.CTkButton(
            btns_frame, text="업데이트 확인", width=120, height=40,
            font=ctk.CTkFont(size=14), command=self.controller._check_update_manual
        )
        self.update_check_btn.pack(side="left", padx=(0, 8))
        
        self.update_download_btn = ctk.CTkButton(
            btns_frame, text="다운로드", width=100, height=40,
            font=ctk.CTkFont(size=14), fg_color="#3498db", hover_color="#2980b9",
            command=self.controller._download_update, state="disabled"
        )
        self.update_download_btn.pack(side="left")
        
        self.update_status_label = ctk.CTkLabel(
            right, text="", width=220, font=ctk.CTkFont(size=13),
            text_color="#2ecc71", anchor="center"
        )
        self.update_status_label.pack(pady=(6, 0))

    def get_settings_state(self):
        return {
            "hotkey_start": self.hotkey_start_btn.cget("text"),
            "hotkey_stop": self.hotkey_stop_btn.cget("text"),
            "random_variance": self.variance_entry.get().strip(),
            "random_variance_enabled": bool(self.variance_switch.get()),
        }

    def apply_settings(self, config):
        self.hotkey_start_btn.configure(text=config.get("hotkey_start", "F6"), fg_color="#404040")
        self.hotkey_stop_btn.configure(text=config.get("hotkey_stop", "F7"), fg_color="#404040")

        self.variance_entry.configure(state="normal")
        self.variance_entry.delete(0, "end")
        self.variance_entry.insert(0, config.get("random_variance", "0.03"))

        variance_enabled = config.get("random_variance_enabled", True)
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

        appearance_mode = config.get("appearance_mode", "dark")
        self.theme_mode.set("라이트모드" if appearance_mode == "light" else "다크모드")
