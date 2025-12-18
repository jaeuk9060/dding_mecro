import customtkinter as ctk
from datetime import datetime, timedelta
from autoclicker.version import __version__
from .base import BasePage

class MainMenuPage(BasePage):
    def __init__(self, parent, controller):
        self._menu_cards = []
        super().__init__(parent, controller)
        # setup_ui() is called in BasePage.__init__
        self._update_price_timer()

    def setup_ui(self):
        """메인 메뉴 페이지 UI 생성 (카드 형태)"""
        # --- 타이머 박스 ---
        self.timer_frame = ctk.CTkFrame(
            self, 
            fg_color=("#f0f7ff", "#1e293b"),
            border_color="#3b82f6", 
            border_width=1,
            corner_radius=12
        )
        self.timer_frame.pack(fill="x", padx=10, pady=(0, 15))
        
        timer_container = ctk.CTkFrame(self.timer_frame, fg_color="transparent")
        timer_container.pack(pady=12, padx=20)
        
        ctk.CTkLabel(
            timer_container, 
            text="⏰", 
            font=ctk.CTkFont(size=22)
        ).pack(side="left", padx=(0, 12))
        
        ctk.CTkLabel(
            timer_container, 
            text="다음 요리 가격 변동까지:", 
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(side="left", padx=(0, 10))
        
        self.timer_label = ctk.CTkLabel(
            timer_container, 
            text="0일 00시간 00분 00초", 
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#3b82f6"
        )
        self.timer_label.pack(side="left")

        # 카드 컨테이너 (스크롤 가능)
        cards_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        cards_frame.pack(fill="both", expand=True, padx=20, pady=(0, 0))

        card_colors = self.controller._get_card_colors()

        # --- 1. 띵타이쿤 정보 카드 ---
        self.info_card = self._create_card(
            cards_frame, "ℹ️", "띵타이쿤", "띵타이쿤의 최신 소식을 확인하세요",
            lambda e: self.controller.navigate_to_page("dding_info"),
            card_colors["inactive"]
        )
        self._menu_cards.append({"card": self.info_card, "type": "inactive"})

        # --- 2. 오토마우스 카드 ---
        self.autoclicker_card = self._create_card(
            cards_frame, "🖱️", "오토마우스", "자동으로 마우스를 클릭합니다",
            lambda e: self.controller.navigate_to_page("autoclicker"),
            card_colors["inactive"]
        )
        self._menu_cards.append({"card": self.autoclicker_card, "type": "inactive"})

        # --- 3. 매크로 카드 (준비 중) ---
        self.macro_card = self._create_card(
            cards_frame, "⌨️", "매크로", "준비 중입니다",
            None, card_colors["inactive"]
        )
        self._menu_cards.append({"card": self.macro_card, "type": "inactive"})

        # --- 4. 기타 기능 카드 ---
        self.card3 = self._create_card(
            cards_frame, "📝", "기능 3", "준비 중입니다",
            None, card_colors["inactive"]
        )
        self._menu_cards.append({"card": self.card3, "type": "inactive"})

        self.card4 = self._create_card(
            cards_frame, "⚙️", "기능 4", "준비 중입니다",
            None, card_colors["inactive"]
        )
        self._menu_cards.append({"card": self.card4, "type": "inactive"})

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

    def _create_card(self, parent, emoji, title, desc, command, bg_color):
        card = ctk.CTkFrame(parent, fg_color=bg_color, corner_radius=15, height=150)
        card.pack(fill="x", pady=10, padx=10)
        card.pack_propagate(False)
        
        if command:
            card.bind("<Button-1>", command)
            card.configure(cursor="hand2")

        def on_enter(e):
            colors = self.controller._get_card_colors()
            card.configure(fg_color=colors["inactive_hover"])
            card._is_hovered = True
        def on_leave(e):
            colors = self.controller._get_card_colors()
            card.configure(fg_color=colors["inactive"])
            card._is_hovered = False
            
        card._is_hovered = False
        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=25, pady=20)
        
        if command:
            content.bind("<Button-1>", command)
            content.configure(cursor="hand2")
        content.bind("<Enter>", on_enter)
        content.bind("<Leave>", on_leave)

        emoji_label = ctk.CTkLabel(content, text=emoji, font=ctk.CTkFont(size=40))
        emoji_label.pack(anchor="w", pady=(0, 10))
        
        title_label = ctk.CTkLabel(content, text=title, font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(anchor="w", pady=(0, 5))
        
        desc_label = ctk.CTkLabel(content, text=desc, font=ctk.CTkFont(size=14), text_color="gray")
        desc_label.pack(anchor="w")

        # 자식 위젯들에게도 이벤트 바인딩
        for child in [emoji_label, title_label, desc_label]:
            if command:
                child.bind("<Button-1>", command)
                child.configure(cursor="hand2")
            child.bind("<Enter>", on_enter)
            child.bind("<Leave>", on_leave)

        return card

    def _update_price_timer(self):
        """가격 변동 타이머 업데이트 (1, 3, 6, 9, 12, 15, 18, 21, 24, 27, 30일 오전 3시)"""
        try:
            now = datetime.now()
            change_days = [1, 3, 6, 9, 12, 15, 18, 21, 24, 27, 30]
            
            next_change = None
            
            # 1. 이번 달에서 다음 변동일 찾기
            for day in change_days:
                try:
                    # 해당 월에 해당 일이 존재하는지 확인 (예: 2월 30일 등 방지)
                    target = now.replace(day=day, hour=3, minute=0, second=0, microsecond=0)
                    if target > now:
                        next_change = target
                        break
                except ValueError:
                    continue
            
            # 2. 이번 달에 더 이상 없으면 다음 달 1일 오전 3시로 설정
            if not next_change:
                if now.month == 12:
                    next_change = now.replace(year=now.year + 1, month=1, day=1, hour=3, minute=0, second=0, microsecond=0)
                else:
                    next_change = now.replace(month=now.month + 1, day=1, hour=3, minute=0, second=0, microsecond=0)
            
            remaining = next_change - now
            
            days = remaining.days
            hours, rem = divmod(remaining.seconds, 3600)
            minutes, seconds = divmod(rem, 60)
            
            timer_text = f"{days}일 {hours:02d}시간 {minutes:02d}분 {seconds:02d}초"
            self.timer_label.configure(text=timer_text)
        except Exception:
            pass
            
        self.after(1000, self._update_price_timer)

    def update_card_colors(self):
        """테마 변경 시 카드 색상 업데이트"""
        card_colors = self.controller._get_card_colors()
        for card_info in self._menu_cards:
            card = card_info["card"]
            is_hovered = getattr(card, '_is_hovered', False)
            if is_hovered:
                card.configure(fg_color=card_colors["inactive_hover"])
            else:
                card.configure(fg_color=card_colors["inactive"])
