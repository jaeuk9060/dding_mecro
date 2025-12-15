"""
손처럼 클릭 - 메인 진입점
프로젝트 구조:
  - autoclicker/: 패키지 루트
    - config.py: 설정 파일 관리
    - clicker.py: 클릭 로직
    - updater.py: 업데이트 모듈
    - ui/app.py: GUI 애플리케이션
  - main.py: 진입점 (이 파일)
"""

from autoclicker.ui import AutoClickerApp


def main():
    """애플리케이션 진입점"""
    app = AutoClickerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
