import time
import threading
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Callable, Optional, Literal, Tuple
from pynput import mouse, keyboard
from pynput.mouse import Button as MouseButton, Controller as MouseController
from pynput.keyboard import Key, Controller as KeyboardController


@dataclass
class MacroAction:
    action_type: Literal["key_press", "key_release", "mouse_click", "mouse_press", "mouse_release", "mouse_move", "mouse_scroll"]
    timestamp: float
    
    key: Optional[str] = None
    
    x: Optional[int] = None
    y: Optional[int] = None
    button: Optional[str] = None
    scroll_dx: Optional[int] = None
    scroll_dy: Optional[int] = None
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "MacroAction":
        return cls(**data)


def save_macro_to_file(actions: List[MacroAction], filepath: str) -> Tuple[bool, str]:
    try:
        data = {
            "version": "1.0",
            "action_count": len(actions),
            "actions": [action.to_dict() for action in actions]
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return True, f"매크로가 저장되었습니다: {Path(filepath).name}"
    except Exception as e:
        return False, f"저장 실패: {str(e)}"


def load_macro_from_file(filepath: str) -> Tuple[List[MacroAction], bool, str]:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        version = data.get("version", "1.0")
        
        actions = [MacroAction.from_dict(action_data) for action_data in data.get("actions", [])]
        
        return actions, True, f"매크로를 불러왔습니다: {len(actions)}개 동작"
    except json.JSONDecodeError:
        return [], False, "잘못된 매크로 파일 형식입니다"
    except FileNotFoundError:
        return [], False, "파일을 찾을 수 없습니다"
    except Exception as e:
        return [], False, f"불러오기 실패: {str(e)}"


class MacroRecorder:
    
    def __init__(self):
        self._actions: List[MacroAction] = []
        self._recording = False
        self._start_time: float = 0
        self._record_keyboard = True
        self._record_mouse = True
        
        self._keyboard_listener: Optional[keyboard.Listener] = None
        self._mouse_listener: Optional[mouse.Listener] = None
        
        # 콜백
        self._on_action_recorded: Optional[Callable[[int], None]] = None
        
        self._record_hotkey: str = "F8"
    
    def set_record_target(self, target: str):
        if target == "키보드":
            self._record_keyboard = True
            self._record_mouse = False
        elif target == "마우스":
            self._record_keyboard = False
            self._record_mouse = True
        else:  # 키보드+마우스
            self._record_keyboard = True
            self._record_mouse = True
    
    def set_record_hotkey(self, hotkey: str):
        self._record_hotkey = hotkey.lower()
    
    def set_action_callback(self, callback: Callable[[int], None]):
        self._on_action_recorded = callback
    
    def start_recording(self):
        if self._recording:
            return
        
        self._actions = []
        self._recording = True
        self._start_time = time.perf_counter()
        
        if self._record_keyboard:
            self._keyboard_listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            self._keyboard_listener.start()
        
        if self._record_mouse:
            self._mouse_listener = mouse.Listener(
                on_click=self._on_mouse_click,
                on_scroll=self._on_mouse_scroll
            )
            self._mouse_listener.start()
    
    def stop_recording(self) -> int:
        if not self._recording:
            return len(self._actions)
        
        self._recording = False
        
        if self._keyboard_listener:
            self._keyboard_listener.stop()
            self._keyboard_listener = None
        
        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener = None
        
        return len(self._actions)
    
    def clear(self):
        self._actions = []
    
    def get_actions(self) -> List[MacroAction]:
        return self._actions.copy()
    
    def get_action_count(self) -> int:
        return len(self._actions)
    
    def _get_timestamp(self) -> float:
        return time.perf_counter() - self._start_time
    
    def _key_to_string(self, key) -> str:
        try:
            return key.char
        except AttributeError:
            return str(key)
    
    def _on_key_press(self, key):
        if not self._recording:
            return
        
        key_str = self._key_to_string(key)
        
        if key_str.lower().replace("key.", "") == self._record_hotkey.lower():
            return
        
        action = MacroAction(
            action_type="key_press",
            timestamp=self._get_timestamp(),
            key=key_str
        )
        self._actions.append(action)
        
        if self._on_action_recorded:
            self._on_action_recorded(len(self._actions))
    
    def _on_key_release(self, key):
        if not self._recording:
            return
        
        key_str = self._key_to_string(key)
        
        if key_str.lower().replace("key.", "") == self._record_hotkey.lower():
            return
        
        action = MacroAction(
            action_type="key_release",
            timestamp=self._get_timestamp(),
            key=key_str
        )
        self._actions.append(action)
        
        if self._on_action_recorded:
            self._on_action_recorded(len(self._actions))
    
    def _on_mouse_click(self, x, y, button, pressed):
        if not self._recording:
            return
        
        button_str = "left" if button == MouseButton.left else ("right" if button == MouseButton.right else "middle")
        
        action = MacroAction(
            action_type="mouse_press" if pressed else "mouse_release",
            timestamp=self._get_timestamp(),
            x=x,
            y=y,
            button=button_str
        )
        self._actions.append(action)
        
        if self._on_action_recorded:
            self._on_action_recorded(len(self._actions))
    
    def _on_mouse_scroll(self, x, y, dx, dy):
        if not self._recording:
            return
        
        action = MacroAction(
            action_type="mouse_scroll",
            timestamp=self._get_timestamp(),
            x=x,
            y=y,
            scroll_dx=dx,
            scroll_dy=dy
        )
        self._actions.append(action)
        
        if self._on_action_recorded:
            self._on_action_recorded(len(self._actions))


class MacroPlayer:
    
    def __init__(self):
        self._mouse = MouseController()
        self._keyboard = KeyboardController()
        self._playing = False
        self._stop_event = threading.Event()
        self._play_thread: Optional[threading.Thread] = None
        
        self._on_status_update: Optional[Callable[[str], None]] = None
        self._on_finish: Optional[Callable[[], None]] = None
    
    def set_callbacks(self, 
                      status_callback: Optional[Callable[[str], None]] = None,
                      finish_callback: Optional[Callable[[], None]] = None):
        self._on_status_update = status_callback
        self._on_finish = finish_callback
    
    def play(self, actions: List[MacroAction], repeat_mode: str = "1회", 
             repeat_count: int = 1, speed: float = 1.0):
        if self._playing or not actions:
            return
        
        self._playing = True
        self._stop_event.clear()
        
        self._play_thread = threading.Thread(
            target=self._play_loop,
            args=(actions, repeat_mode, repeat_count, speed),
            daemon=True
        )
        self._play_thread.start()
    
    def stop(self):
        self._stop_event.set()
        self._playing = False
    
    def is_playing(self) -> bool:
        return self._playing
    
    def _play_loop(self, actions: List[MacroAction], repeat_mode: str, 
                   repeat_count: int, speed: float):
        try:
            if repeat_mode == "무한":
                iteration = 0
                while not self._stop_event.is_set():
                    iteration += 1
                    if self._on_status_update:
                        self._on_status_update(f"▶️ 재생 중... (무한 반복 #{iteration})")
                    self._play_once(actions, speed)
            elif repeat_mode == "반복":
                for i in range(repeat_count):
                    if self._stop_event.is_set():
                        break
                    if self._on_status_update:
                        self._on_status_update(f"▶️ 재생 중... ({i+1}/{repeat_count})")
                    self._play_once(actions, speed)
            else:
                if self._on_status_update:
                    self._on_status_update("▶️ 재생 중...")
                self._play_once(actions, speed)
        except Exception as e:
            if self._on_status_update:
                self._on_status_update(f"⚠️ 재생 오류: {e}")
        finally:
            self._playing = False
            if self._on_finish:
                self._on_finish()
    
    def _play_once(self, actions: List[MacroAction], speed: float):
        if not actions:
            return
        
        start_time = time.perf_counter()
        
        for action in actions:
            if self._stop_event.is_set():
                return
            
            target_time = action.timestamp / speed
            current_time = time.perf_counter() - start_time
            wait_time = target_time - current_time
            
            if wait_time > 0:
                while wait_time > 0 and not self._stop_event.is_set():
                    sleep_time = min(wait_time, 0.01)
                    time.sleep(sleep_time)
                    wait_time -= sleep_time
            
            if self._stop_event.is_set():
                return
            
            self._execute_action(action)
    
    def _execute_action(self, action: MacroAction):
        try:
            if action.action_type == "key_press":
                self._press_key(action.key)
            elif action.action_type == "key_release":
                self._release_key(action.key)
            elif action.action_type == "mouse_press":
                self._mouse.position = (action.x, action.y)
                button = self._get_mouse_button(action.button)
                self._mouse.press(button)
            elif action.action_type == "mouse_release":
                self._mouse.position = (action.x, action.y)
                button = self._get_mouse_button(action.button)
                self._mouse.release(button)
            elif action.action_type == "mouse_scroll":
                self._mouse.position = (action.x, action.y)
                self._mouse.scroll(action.scroll_dx, action.scroll_dy)
        except Exception:
            pass
    
    def _press_key(self, key_str: str):
        key = self._string_to_key(key_str)
        if key is not None:
            self._keyboard.press(key)
    
    def _release_key(self, key_str: str):
        key = self._string_to_key(key_str)
        if key is not None:
            self._keyboard.release(key)
    
    def _string_to_key(self, key_str: str):
        if key_str is None:
            return None
        
        if key_str.startswith("Key."):
            key_name = key_str[4:]
            try:
                return getattr(Key, key_name)
            except AttributeError:
                return None
        
        if len(key_str) == 1:
            return key_str
        
        return None
    
    def _get_mouse_button(self, button_str: str) -> MouseButton:
        if button_str == "right":
            return MouseButton.right
        elif button_str == "middle":
            return MouseButton.middle
        return MouseButton.left

