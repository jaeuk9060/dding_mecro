import customtkinter as ctk
import webbrowser
import tkinter.messagebox as messagebox
from autoclicker.version import __version__
from .base import BasePage

class DdingInfoPage(BasePage):
    def setup_ui(self):
        scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 0))

        card_colors = self.controller._get_card_colors()

        def toggle_section(frame, arrow_label):
            if frame.winfo_viewable():
                frame.pack_forget()
                arrow_label.configure(text="▶")
            else:
                frame.pack(fill="x", padx=10, pady=(0, 10))
                arrow_label.configure(text="▼")

        official_container = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        official_container.pack(fill="x", pady=(10, 5))

        official_header = ctk.CTkFrame(official_container, fg_color="transparent")
        official_header.pack(fill="x", padx=10, pady=5)
        official_header.configure(cursor="hand2")

        official_arrow = ctk.CTkLabel(official_header, text="▼", font=ctk.CTkFont(size=14))
        official_arrow.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            official_header,
            text="🌐 공식",
            font=ctk.CTkFont(size=22, weight="bold"),
            anchor="w"
        ).pack(side="left")

        official_content_frame = ctk.CTkFrame(official_container, fg_color="transparent")
        official_content_frame.pack(fill="x", padx=10, pady=(0, 10))

        official_header.bind("<Button-1>", lambda e: toggle_section(official_content_frame, official_arrow))
        for child in official_header.winfo_children():
            child.bind("<Button-1>", lambda e: toggle_section(official_content_frame, official_arrow))

        self._create_link_button(official_content_frame, "📚 공식 위키", "https://wiki.ddingtycoon.kr/", card_colors)
        self._create_link_button(official_content_frame, "💬 디스코드", "https://discord.com/invite/CNK4qmvh3g", card_colors)
        self._create_link_button(official_content_frame, "☕ 네이버 카페", "https://cafe.naver.com/ddingtycoon", card_colors)

        cooking_container = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        cooking_container.pack(fill="x", pady=(10, 5))

        cooking_header = ctk.CTkFrame(cooking_container, fg_color="transparent")
        cooking_header.pack(fill="x", padx=10, pady=5)
        cooking_header.configure(cursor="hand2")

        cooking_arrow = ctk.CTkLabel(cooking_header, text="▼", font=ctk.CTkFont(size=14))
        cooking_arrow.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            cooking_header,
            text="🍳 요리",
            font=ctk.CTkFont(size=22, weight="bold"),
            anchor="w"
        ).pack(side="left")

        cooking_content_frame = ctk.CTkFrame(cooking_container, fg_color="transparent")
        cooking_content_frame.pack(fill="x", padx=10, pady=(0, 10))

        cooking_header.bind("<Button-1>", lambda e: toggle_section(cooking_content_frame, cooking_arrow))
        for child in cooking_header.winfo_children():
            child.bind("<Button-1>", lambda e: toggle_section(cooking_content_frame, cooking_arrow))

        self._create_alert_button(cooking_content_frame, "📊 요리 계산기", "요리 계산기 기능은 준비 중입니다.", card_colors)
        self._create_alert_button(cooking_content_frame, "🏆 요리 순위", "요리 순위 기능은 준비 중입니다.", card_colors)

        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", pady=(10, 0), padx=25)
        
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

    def _create_link_button(self, parent, text, url, colors):
        btn = ctk.CTkButton(
            parent,
            text=text,
            height=60,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=colors["inactive"],
            hover_color=colors["inactive_hover"],
            text_color=("black", "white"),
            anchor="w",
            command=lambda: webbrowser.open(url)
        )
        btn.pack(fill="x", pady=(0, 10))
        return btn

    def _create_alert_button(self, parent, text, message, colors):
        btn = ctk.CTkButton(
            parent,
            text=text,
            height=60,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=colors["inactive"],
            hover_color=colors["inactive_hover"],
            text_color=("black", "white"),
            anchor="w",
            command=lambda: messagebox.showinfo("안내", message)
        )
        btn.pack(fill="x", pady=(0, 10))
        return btn
