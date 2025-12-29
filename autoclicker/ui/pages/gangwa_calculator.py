import customtkinter as ctk
from autoclicker.version import __version__
from .base import BasePage


class GangwaCalculatorPage(BasePage):
    def setup_ui(self):
        # 타이틀 섹션
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(10, 10))

        ctk.CTkLabel(
            title_frame,
            text="⚔️ 강화 계산기",
            font=ctk.CTkFont(size=22, weight="bold"),
            anchor="w"
        ).pack(side="left")

        # 탭뷰 생성
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # 탭 추가
        self.tabview.add("📌 단일 강화")
        self.tabview.add("📊 누적 강화")

        # 각 탭 설정
        self._setup_single_tab()
        self._setup_range_tab()

        # 하단 푸터
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", pady=(0, 5), padx=25)

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

    def _setup_single_tab(self):
        """단일 강화 계산 탭 설정"""
        tab = self.tabview.tab("📌 단일 강화")
        card_colors = self.controller._get_card_colors()

        scroll_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 설명
        ctk.CTkLabel(
            scroll_frame,
            text="특정 강화 단계에 필요한 재료를 확인합니다",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        ).pack(anchor="w", pady=(0, 15))

        # 강화 단계 선택
        select_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        select_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            select_frame,
            text="목표 강화:",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(side="left", padx=(0, 10))

        self.gangwa_var = ctk.StringVar(value="1")
        gangwa_options = [str(i) for i in range(1, 16)]

        self.gangwa_dropdown = ctk.CTkOptionMenu(
            select_frame,
            variable=self.gangwa_var,
            values=gangwa_options,
            width=100,
            font=ctk.CTkFont(size=14),
            command=self._on_gangwa_change
        )
        self.gangwa_dropdown.pack(side="left")

        ctk.CTkLabel(
            select_frame,
            text="강",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(side="left", padx=(8, 0))

        # 결과 카드
        result_frame = ctk.CTkFrame(
            scroll_frame,
            fg_color=card_colors["inactive"],
            corner_radius=15
        )
        result_frame.pack(fill="x", pady=(10, 10))

        result_content = ctk.CTkFrame(result_frame, fg_color="transparent")
        result_content.pack(fill="both", expand=True, padx=25, pady=20)

        ctk.CTkLabel(
            result_content,
            text="📦 필요 재료",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        ).pack(anchor="w", pady=(0, 12))

        self.low_label = self._create_result_row(result_content, "🟢 하급 라이프스톤", "1개")
        self.medium_label = self._create_result_row(result_content, "🔵 중급 라이프스톤", "0개")
        self.high_label = self._create_result_row(result_content, "🟣 상급 라이프스톤", "0개")

        ctk.CTkFrame(result_content, height=2, fg_color="gray50").pack(fill="x", pady=12)

        ctk.CTkLabel(
            result_content,
            text="💰 필요 재화",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        ).pack(anchor="w", pady=(0, 12))

        self.gold_label = self._create_result_row(result_content, "🪙 골드", "5,000원")
        self.ruby_label = self._create_result_row(result_content, "💎 루비", "0개")

        ctk.CTkFrame(result_content, height=2, fg_color="gray50").pack(fill="x", pady=12)

        # 확률 표시
        prob_frame = ctk.CTkFrame(result_content, fg_color="transparent")
        prob_frame.pack(fill="x")

        ctk.CTkLabel(
            prob_frame,
            text="🎯 강화 확률",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left")

        self.prob_label = ctk.CTkLabel(
            prob_frame,
            text="100%",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#2ecc71"
        )
        self.prob_label.pack(side="right")

    def _setup_range_tab(self):
        """누적 강화 계산 탭 설정"""
        tab = self.tabview.tab("📊 누적 강화")
        card_colors = self.controller._get_card_colors()

        scroll_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 설명
        ctk.CTkLabel(
            scroll_frame,
            text="현재 강화에서 목표까지 필요한 총 재료를 계산합니다",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        ).pack(anchor="w", pady=(0, 15))

        # 범위 선택
        range_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        range_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            range_frame,
            text="현재:",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(side="left", padx=(0, 8))

        self.current_gangwa_var = ctk.StringVar(value="0")
        current_options = [str(i) for i in range(0, 15)]

        self.current_dropdown = ctk.CTkOptionMenu(
            range_frame,
            variable=self.current_gangwa_var,
            values=current_options,
            width=80,
            font=ctk.CTkFont(size=14),
            command=self._on_range_change
        )
        self.current_dropdown.pack(side="left")

        ctk.CTkLabel(
            range_frame,
            text="강",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(side="left", padx=(5, 15))

        ctk.CTkLabel(
            range_frame,
            text="→",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#3b82f6"
        ).pack(side="left", padx=(0, 15))

        ctk.CTkLabel(
            range_frame,
            text="목표:",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(side="left", padx=(0, 8))

        self.target_gangwa_var = ctk.StringVar(value="6")
        target_options = [str(i) for i in range(1, 16)]

        self.target_dropdown = ctk.CTkOptionMenu(
            range_frame,
            variable=self.target_gangwa_var,
            values=target_options,
            width=80,
            font=ctk.CTkFont(size=14),
            command=self._on_range_change
        )
        self.target_dropdown.pack(side="left")

        ctk.CTkLabel(
            range_frame,
            text="강",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(side="left", padx=(5, 0))

        # 범위 설명 라벨
        self.range_desc_label = ctk.CTkLabel(
            scroll_frame,
            text="0강 → 6강 (1~6강 강화 필요)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#3b82f6",
            anchor="w"
        )
        self.range_desc_label.pack(anchor="w", pady=(5, 10))

        # 결과 카드
        result_frame = ctk.CTkFrame(
            scroll_frame,
            fg_color=card_colors["inactive"],
            corner_radius=15
        )
        result_frame.pack(fill="x", pady=(10, 10))

        result_content = ctk.CTkFrame(result_frame, fg_color="transparent")
        result_content.pack(fill="both", expand=True, padx=25, pady=20)

        ctk.CTkLabel(
            result_content,
            text="📦 총 필요 재료",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        ).pack(anchor="w", pady=(0, 12))

        self.total_low_label = self._create_result_row(result_content, "🟢 하급 라이프스톤", "0개")
        self.total_medium_label = self._create_result_row(result_content, "🔵 중급 라이프스톤", "0개")
        self.total_high_label = self._create_result_row(result_content, "🟣 상급 라이프스톤", "0개")

        ctk.CTkFrame(result_content, height=2, fg_color="gray50").pack(fill="x", pady=12)

        ctk.CTkLabel(
            result_content,
            text="💰 총 필요 재화",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        ).pack(anchor="w", pady=(0, 12))

        self.total_gold_label = self._create_result_row(result_content, "🪙 골드", "0원")
        self.total_ruby_label = self._create_result_row(result_content, "💎 루비", "0개")

        ctk.CTkFrame(result_content, height=2, fg_color="gray50").pack(fill="x", pady=12)

        # 기대 확률 표시
        prob_frame = ctk.CTkFrame(result_content, fg_color="transparent")
        prob_frame.pack(fill="x")

        ctk.CTkLabel(
            prob_frame,
            text="🎯 연속 성공 확률",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left")

        self.total_prob_label = ctk.CTkLabel(
            prob_frame,
            text="0%",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#2ecc71"
        )
        self.total_prob_label.pack(side="right")

        # 확률 설명
        self.prob_desc_label = ctk.CTkLabel(
            result_content,
            text="모든 강화를 한 번에 성공할 확률",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="e"
        )
        self.prob_desc_label.pack(anchor="e", pady=(5, 0))

        # 초기 계산
        self._update_range_calculation()

    def _create_result_row(self, parent, label_text, value_text):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=4)

        ctk.CTkLabel(
            row,
            text=label_text,
            font=ctk.CTkFont(size=14),
            anchor="w"
        ).pack(side="left")

        value_label = ctk.CTkLabel(
            row,
            text=value_text,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="e"
        )
        value_label.pack(side="right")

        return value_label

    def _get_gangwa_data(self, gangwa):
        """특정 강화 단계의 필요 재료 반환"""
        low = 0
        medium = 0
        high = 0
        gold = 0
        ruby = 0
        per = 0

        if gangwa == 1:
            low = 1
            gold = 5000
            per = 100
        elif gangwa == 2:
            low = 2
            gold = 25000
            per = 100
        elif gangwa == 3:
            low = 2
            gold = 50000
            per = 80
        elif gangwa == 4:
            low = 3
            medium = 1
            gold = 100000
            per = 80
        elif gangwa == 5:
            low = 3
            medium = 1
            gold = 130000
            per = 70
        elif gangwa == 6:
            low = 4
            medium = 2
            high = 1
            ruby = 5
            gold = 150000
            per = 50
        elif gangwa == 7:
            low = 4
            medium = 2
            high = 1
            ruby = 5
            gold = 170000
            per = 40
        elif gangwa == 8:
            low = 6
            medium = 3
            high = 2
            ruby = 5
            gold = 300000
            per = 30
        elif gangwa == 9:
            low = 6
            medium = 3
            high = 2
            ruby = 5
            gold = 350000
            per = 20
        elif gangwa == 10:
            low = 8
            medium = 4
            high = 3
            ruby = 10
            gold = 500000
            per = 10
        elif gangwa == 11:
            low = 8
            medium = 4
            high = 3
            ruby = 10
            gold = 700000
            per = 5
        elif gangwa == 12:
            low = 8
            medium = 4
            high = 3
            ruby = 10
            gold = 1000000
            per = 3
        elif gangwa == 13:
            low = 10
            medium = 6
            high = 4
            ruby = 30
            gold = 1300000
            per = 2
        elif gangwa == 14:
            low = 10
            medium = 6
            high = 4
            ruby = 30
            gold = 1500000
            per = 1
        elif gangwa == 15:
            low = 10
            medium = 6
            high = 5
            gold = 2000000
            per = 1
            ruby = 30

        return {
            "low": low,
            "medium": medium,
            "high": high,
            "gold": gold,
            "ruby": ruby,
            "per": per
        }

    def _on_gangwa_change(self, value):
        self._update_single_calculation()

    def _on_range_change(self, value):
        self._update_range_calculation()

    def _update_single_calculation(self):
        gangwa = int(self.gangwa_var.get())
        data = self._get_gangwa_data(gangwa)

        self.low_label.configure(text=f"{data['low']}개")
        self.medium_label.configure(text=f"{data['medium']}개")
        self.high_label.configure(text=f"{data['high']}개")
        self.gold_label.configure(text=f"{data['gold']:,}원")
        self.ruby_label.configure(text=f"{data['ruby']}개")
        self.prob_label.configure(text=f"{data['per']}%")

        # 확률에 따른 색상 변경
        if data['per'] >= 80:
            self.prob_label.configure(text_color="#2ecc71")
        elif data['per'] >= 50:
            self.prob_label.configure(text_color="#f39c12")
        elif data['per'] >= 20:
            self.prob_label.configure(text_color="#e67e22")
        else:
            self.prob_label.configure(text_color="#e74c3c")

    def _update_range_calculation(self):
        current = int(self.current_gangwa_var.get())
        target = int(self.target_gangwa_var.get())

        # 유효성 검사
        if current >= target:
            self.range_desc_label.configure(
                text="⚠️ 목표가 현재보다 높아야 합니다",
                text_color="#e74c3c"
            )
            self.total_low_label.configure(text="-")
            self.total_medium_label.configure(text="-")
            self.total_high_label.configure(text="-")
            self.total_gold_label.configure(text="-")
            self.total_ruby_label.configure(text="-")
            self.total_prob_label.configure(text="-", text_color="gray")
            return

        # 범위 설명 업데이트
        self.range_desc_label.configure(
            text=f"{current}강 → {target}강 ({current+1}~{target}강 강화 필요)",
            text_color="#3b82f6"
        )

        # 누적 계산
        total_low = 0
        total_medium = 0
        total_high = 0
        total_gold = 0
        total_ruby = 0
        total_prob = 1.0  # 연속 성공 확률 (곱셈)

        for g in range(current + 1, target + 1):
            data = self._get_gangwa_data(g)
            total_low += data["low"]
            total_medium += data["medium"]
            total_high += data["high"]
            total_gold += data["gold"]
            total_ruby += data["ruby"]
            total_prob *= (data["per"] / 100.0)

        # 확률을 퍼센트로 변환
        total_prob_percent = total_prob * 100

        # UI 업데이트
        self.total_low_label.configure(text=f"{total_low}개")
        self.total_medium_label.configure(text=f"{total_medium}개")
        self.total_high_label.configure(text=f"{total_high}개")
        self.total_gold_label.configure(text=f"{total_gold:,}원")
        self.total_ruby_label.configure(text=f"{total_ruby}개")

        # 확률 표시 (소수점 2자리)
        if total_prob_percent >= 1:
            self.total_prob_label.configure(text=f"{total_prob_percent:.1f}%")
        elif total_prob_percent >= 0.01:
            self.total_prob_label.configure(text=f"{total_prob_percent:.2f}%")
        else:
            self.total_prob_label.configure(text=f"{total_prob_percent:.4f}%")

        # 확률에 따른 색상 변경
        if total_prob_percent >= 50:
            self.total_prob_label.configure(text_color="#2ecc71")
        elif total_prob_percent >= 20:
            self.total_prob_label.configure(text_color="#f39c12")
        elif total_prob_percent >= 5:
            self.total_prob_label.configure(text_color="#e67e22")
        else:
            self.total_prob_label.configure(text_color="#e74c3c")
