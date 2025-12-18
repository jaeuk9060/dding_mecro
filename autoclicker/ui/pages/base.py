import customtkinter as ctk

class BasePage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.setup_ui()

    def setup_ui(self):
        """UI 구성요소를 생성하는 메서드. 하위 클래스에서 구현합니다."""
        pass

    def on_show(self):
        """페이지가 표시될 때 호출되는 hook."""
        pass

