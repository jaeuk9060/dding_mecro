from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.json"

DEFAULT_CONFIG = {
    "hotkey_start": "F6",
    "hotkey_stop": "F7",
    "click_interval": "0.1",
    "click_type": "좌클릭",
    "click_mode": "반복",
    "random_variance": "0.03",
    "random_variance_enabled": True,
    "appearance_mode": "dark",
    "github_repo": "",
    "hotkey_macro_record": "F8",
    "hotkey_macro_start": "F9",
    "hotkey_macro_stop": "F10",
    "macro_target": "키보드+마우스",
    "macro_repeat_mode": "1회",
    "macro_repeat_count": "10",
    "macro_speed": "1x",
}


def load_config():
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
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with CONFIG_FILE.open("w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
