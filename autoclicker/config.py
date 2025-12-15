"""설정 파일 관리 모듈."""

from pathlib import Path
import json

# 패키지 루트 기준 설정 파일 경로
BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.json"

# 기본 설정
DEFAULT_CONFIG = {
    "hotkey_start": "F6",
    "hotkey_stop": "F7",
    "click_interval": "0.1",
    "click_type": "좌클릭",
    "click_mode": "반복",
    "random_variance": "0.03",
    "random_variance_enabled": True,
    "github_repo": "",  # GitHub 저장소 정보 (예: "username/repo-name")
}


def load_config():
    """설정 파일을 로드하고 누락된 키를 기본값으로 채움."""
    if CONFIG_FILE.exists():
        try:
            with CONFIG_FILE.open("r", encoding="utf-8") as f:
                config = json.load(f)
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(config):
    """설정 파일 저장."""
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with CONFIG_FILE.open("w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
