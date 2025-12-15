"""
클릭 로직 모듈
"""
import time
import random
import threading
from pynput.mouse import Button, Controller as MouseController


class Clicker:
    """자동 클릭 로직을 담당하는 클래스"""
    
    def __init__(self, mouse: MouseController, stop_event: threading.Event):
        self.mouse = mouse
        self._stop_event = stop_event
    
    def click_loop(self, button: Button, interval_sec: float, variance: float = 0.0, status_callback=None, finish_callback=None):
        """
        반복 클릭 모드:
        드리프트 보정형 스케줄로 next_tick 기준으로 주기를 유지
        랜덤 변동값을 적용하여 자연스러운 클릭 간격 생성
        
        Args:
            button: 클릭할 버튼 (Button.left 또는 Button.right)
            interval_sec: 클릭 간격 (초)
            variance: 랜덤 변동값 (±초)
            status_callback: 상태 업데이트 콜백 함수
            finish_callback: 완료 시 호출할 콜백 함수
        """
        try:
            next_tick = time.perf_counter()
            while not self._stop_event.is_set():
                now = time.perf_counter()
                remain = next_tick - now
                if remain > 0:
                    if remain > 0.005:
                        time.sleep(remain - 0.001)
                    continue

                # 클릭 1회
                self.mouse.click(button)

                # 랜덤 변동 적용: 기본 간격 ± 변동값
                random_offset = random.uniform(-variance, variance)
                actual_interval = interval_sec + random_offset
                
                # 음수 간격 방지
                if actual_interval < 0.0001:
                    actual_interval = 0.0001

                # 다음 tick 예약
                next_tick += actual_interval

                # next_tick이 너무 뒤처지면 현재 기준으로 재정렬
                if (time.perf_counter() - next_tick) > (interval_sec * 3):
                    next_tick = time.perf_counter() + interval_sec

        except Exception as e:
            if status_callback:
                status_callback(f"⚠️ 클릭 루프 오류: {e}")
        finally:
            if finish_callback:
                finish_callback()

    def hold_loop(self, button: Button, status_callback=None, finish_callback=None):
        """
        꾹누르기 모드:
        버튼을 누른 상태 유지, 중지 시 뗌
        
        Args:
            button: 누를 버튼 (Button.left 또는 Button.right)
            status_callback: 상태 업데이트 콜백 함수
            finish_callback: 완료 시 호출할 콜백 함수
        """
        try:
            # 버튼 누르기
            self.mouse.press(button)
            
            # 중지 신호가 올 때까지 대기
            while not self._stop_event.is_set():
                time.sleep(0.05)

        except Exception as e:
            if status_callback:
                status_callback(f"⚠️ 꾹누르기 오류: {e}")
        finally:
            # 버튼 떼기
            try:
                self.mouse.release(button)
            except Exception:
                pass
            if finish_callback:
                finish_callback()
