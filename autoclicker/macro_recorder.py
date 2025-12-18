"""
매크로 녹화 및 재생 모듈
"""
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
    """매크로 동작 하나를 나타내는 데이터 클래스"""
    action_type: Literal["key_press", "key_release", "mouse_click", "mouse_press", "mouse_release", "mouse_move", "mouse_scroll"]
    timestamp: float  # 녹화 시작으로부터의 시간 (초)
    
    # 키보드 관련
    key: Optional[str] = None
    
    # 마우스 관련
    x: Optional[int] = None
    y: Optional[int] = None
    button: Optional[str] = None  # "left", "right", "middle"
    scroll_dx: Optional[int] = None
    scroll_dy: Optional[int] = None
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "MacroAction":
        """딕셔너리에서 생성"""
        return cls(**data)


def save_macro_to_file(actions: List[MacroAction], filepath: str) -> Tuple[bool, str]:
    """
    매크로를 파일로 저장
    
    Args:
        actions: 저장할 매크로 동작 목록
        filepath: 저장할 파일 경로
    
    Returns:
        (성공 여부, 메시지)
    """
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
    """
    파일에서 매크로 불러오기
    
    Args:
        filepath: 불러올 파일 경로
    
    Returns:
        (매크로 동작 목록, 성공 여부, 메시지)
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 버전 체크 (향후 호환성을 위해)
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
    """매크로 녹화 클래스"""
    
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
        
        # 녹화 단축키 필터링 (녹화 단축키 자체는 녹화하지 않음)
        self._record_hotkey: str = "F8"
    
    def set_record_target(self, target: str):
        """녹화 대상 설정 (키보드, 마우스, 키보드+마우스)"""
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
        """녹화 단축키 설정 (이 키는 녹화에서 제외)"""
        self._record_hotkey = hotkey.lower()
    
    def set_action_callback(self, callback: Callable[[int], None]):
        """동작 녹화 시 호출될 콜백 설정"""
        self._on_action_recorded = callback
    
    def start_recording(self):
        """녹화 시작"""
        if self._recording:
            return
        
        self._actions = []
        self._recording = True
        self._start_time = time.perf_counter()
        
        # 키보드 리스너
        if self._record_keyboard:
            self._keyboard_listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            self._keyboard_listener.start()
        
        # 마우스 리스너
        if self._record_mouse:
            self._mouse_listener = mouse.Listener(
                on_click=self._on_mouse_click,
                on_scroll=self._on_mouse_scroll
            )
            self._mouse_listener.start()
    
    def stop_recording(self) -> int:
        """녹화 중지, 녹화된 동작 수 반환"""
        if not self._recording:
            return len(self._actions)
        
        self._recording = False
        
        # 리스너 중지
        if self._keyboard_listener:
            self._keyboard_listener.stop()
            self._keyboard_listener = None
        
        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener = None
        
        return len(self._actions)
    
    def clear(self):
        """녹화된 매크로 초기화"""
        self._actions = []
    
    def get_actions(self) -> List[MacroAction]:
        """녹화된 동작 목록 반환"""
        return self._actions.copy()
    
    def get_action_count(self) -> int:
        """녹화된 동작 수 반환"""
        return len(self._actions)
    
    def _get_timestamp(self) -> float:
        """현재 타임스탬프 계산"""
        return time.perf_counter() - self._start_time
    
    def _key_to_string(self, key) -> str:
        """pynput 키를 문자열로 변환"""
        try:
            # 일반 문자 키
            return key.char
        except AttributeError:
            # 특수 키 (Key.space, Key.enter 등)
            return str(key)
    
    def _on_key_press(self, key):
        """키 누름 이벤트 처리"""
        if not self._recording:
            return
        
        key_str = self._key_to_string(key)
        
        # 녹화 단축키는 제외
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
        """키 뗌 이벤트 처리"""
        if not self._recording:
            return
        
        key_str = self._key_to_string(key)
        
        # 녹화 단축키는 제외
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
        """마우스 클릭 이벤트 처리"""
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
        """마우스 스크롤 이벤트 처리"""
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
    """매크로 재생 클래스"""
    
    def __init__(self):
        self._mouse = MouseController()
        self._keyboard = KeyboardController()
        self._playing = False
        self._stop_event = threading.Event()
        self._play_thread: Optional[threading.Thread] = None
        
        # 콜백
        self._on_status_update: Optional[Callable[[str], None]] = None
        self._on_finish: Optional[Callable[[], None]] = None
    
    def set_callbacks(self, 
                      status_callback: Optional[Callable[[str], None]] = None,
                      finish_callback: Optional[Callable[[], None]] = None):
        """콜백 설정"""
        self._on_status_update = status_callback
        self._on_finish = finish_callback
    
    def play(self, actions: List[MacroAction], repeat_mode: str = "1회", 
             repeat_count: int = 1, speed: float = 1.0):
        """
        매크로 재생
        
        Args:
            actions: 재생할 동작 목록
            repeat_mode: "1회", "반복", "무한"
            repeat_count: 반복 모드일 때 반복 횟수
            speed: 재생 속도 (1.0 = 원래 속도, 2.0 = 2배속)
        """
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
        """재생 중지"""
        self._stop_event.set()
        self._playing = False
    
    def is_playing(self) -> bool:
        """재생 중인지 확인"""
        return self._playing
    
    def _play_loop(self, actions: List[MacroAction], repeat_mode: str, 
                   repeat_count: int, speed: float):
        """재생 루프"""
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
            else:  # 1회
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
        """매크로 한 번 재생"""
        if not actions:
            return
        
        start_time = time.perf_counter()
        
        for action in actions:
            if self._stop_event.is_set():
                return
            
            # 대기 시간 계산 (속도 적용)
            target_time = action.timestamp / speed
            current_time = time.perf_counter() - start_time
            wait_time = target_time - current_time
            
            if wait_time > 0:
                # 작은 간격으로 나눠서 대기 (중지 신호 확인용)
                while wait_time > 0 and not self._stop_event.is_set():
                    sleep_time = min(wait_time, 0.01)
                    time.sleep(sleep_time)
                    wait_time -= sleep_time
            
            if self._stop_event.is_set():
                return
            
            # 동작 실행
            self._execute_action(action)
    
    def _execute_action(self, action: MacroAction):
        """단일 동작 실행"""
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
            pass  # 개별 동작 실패는 무시
    
    def _press_key(self, key_str: str):
        """키 누름"""
        key = self._string_to_key(key_str)
        if key is not None:
            self._keyboard.press(key)
    
    def _release_key(self, key_str: str):
        """키 뗌"""
        key = self._string_to_key(key_str)
        if key is not None:
            self._keyboard.release(key)
    
    def _string_to_key(self, key_str: str):
        """문자열을 pynput 키로 변환"""
        if key_str is None:
            return None
        
        # Key.xxx 형식 처리
        if key_str.startswith("Key."):
            key_name = key_str[4:]  # "Key." 제거
            try:
                return getattr(Key, key_name)
            except AttributeError:
                return None
        
        # 일반 문자
        if len(key_str) == 1:
            return key_str
        
        return None
    
    def _get_mouse_button(self, button_str: str) -> MouseButton:
        """문자열을 마우스 버튼으로 변환"""
        if button_str == "right":
            return MouseButton.right
        elif button_str == "middle":
            return MouseButton.middle
        return MouseButton.left

