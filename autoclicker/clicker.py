import time
import random
import threading
from pynput.mouse import Button, Controller as MouseController


class Clicker:
    
    def __init__(self, mouse: MouseController, stop_event: threading.Event):
        self.mouse = mouse
        self._stop_event = stop_event
    
    def click_loop(self, button: Button, interval_sec: float, variance: float = 0.0, status_callback=None, finish_callback=None):
        try:
            next_tick = time.perf_counter()
            while not self._stop_event.is_set():
                now = time.perf_counter()
                remain = next_tick - now
                if remain > 0:
                    if remain > 0.005:
                        time.sleep(remain - 0.001)
                    continue

                self.mouse.click(button)

                random_offset = random.uniform(-variance, variance)
                actual_interval = interval_sec + random_offset
                
                if actual_interval < 0.0001:
                    actual_interval = 0.0001

                next_tick += actual_interval

                if (time.perf_counter() - next_tick) > (interval_sec * 3):
                    next_tick = time.perf_counter() + interval_sec

        except Exception as e:
            if status_callback:
                status_callback(f"⚠️ 클릭 루프 오류: {e}")
        finally:
            if finish_callback:
                finish_callback()

    def hold_loop(self, button: Button, status_callback=None, finish_callback=None):
        try:
            self.mouse.press(button)
            
            while not self._stop_event.is_set():
                time.sleep(0.05)

        except Exception as e:
            if status_callback:
                status_callback(f"⚠️ 꾹누르기 오류: {e}")
        finally:
            try:
                self.mouse.release(button)
            except Exception:
                pass
            if finish_callback:
                finish_callback()
