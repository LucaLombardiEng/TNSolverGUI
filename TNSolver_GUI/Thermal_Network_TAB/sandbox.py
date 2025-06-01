import tkinter as tk # Use tk alias for clarity

# Mock gUtility for this isolated test
class MockGUtility:
    def __init__(self):
        self.font = "Helvetica"
        self.font_size = 10

gUtility = MockGUtility()
font = gUtility.font
font_size = gUtility.font_size


class TestBasicSettings(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self._basic_setting_frame = tk.LabelFrame(self, text="Basic Settings", padx=10, pady=10)
        self._basic_setting_frame.pack(side='left', pady=10, expand=True, fill='both', anchor='n')

        # Main structural frames with distinct colors and borders
        self._top_frame = tk.Frame(self._basic_setting_frame, bg='lightblue', bd=3, relief='solid')
        self._central_frame = tk.Frame(self._basic_setting_frame, bg='lightgreen', bd=3, relief='solid')
        self._bottom_frame = tk.Frame(self._basic_setting_frame, bg='lightcoral', bd=3, relief='solid')

        # Pack them to stack vertically
        self._top_frame.pack(side='top', fill='both', expand=True, pady=2)
        self._central_frame.pack(side='top', fill='both', expand=True, pady=2)
        self._bottom_frame.pack(side='top', fill='both', expand=True, pady=2)

        # Add some visible content to each frame to ensure they have a size
        tk.Label(self._top_frame, text="TOP FRAME", font=(font, font_size * 2), bg='lightblue').pack(pady=20)
        tk.Label(self._central_frame, text="CENTRAL FRAME", font=(font, font_size * 2), bg='lightgreen').pack(pady=20)
        tk.Label(self._bottom_frame, text="BOTTOM FRAME", font=(font, font_size * 2), bg='lightcoral').pack(pady=20)


if __name__ == '__main__':
    win = tk.Tk()
    win.title('Isolated Pack Test')

    test_frame = TestBasicSettings(win)
    test_frame.pack(padx=10, pady=10, fill='both', expand=True)

    win.mainloop()