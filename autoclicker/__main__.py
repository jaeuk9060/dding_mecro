"""
손처럼 클릭 - 패키지 메인 진입점
python -m autoclicker로 실행 가능
"""

from autoclicker.ui import AutoClickerApp


def main():
    """애플리케이션 진입점"""
    app = AutoClickerApp()
    app.mainloop()


if __name__ == "__main__":
    main()

