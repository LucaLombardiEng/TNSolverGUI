"""
    Thermal Solver Network - Progress Terminal
    This class permits the communication of the events with the user avoiding pop-ups and maintaining the
    journal of the messages

    Luca Lombardi
    Rev 0: First Draft
    Rev 1: 2026 Sep 02 Update to handle message levels (Info, Success, Warning, Error) with color coding
           to improve readability

    To Do:


"""

from tkinter import Tk, LabelFrame, Frame, Text, Button, Label, Scrollbar


class Terminal(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)

        self._frame_terminal = LabelFrame(self, text="Progress report terminal", width=2000, height=200, padx=10,
                                          pady=5)
        self._frame_terminal.pack(expand=1, fill='both', anchor='sw')
        self.terminal = Text(self._frame_terminal, height=15, width=162)
        self.terminal.pack(side='left', anchor='nw')
        self._y_sidebar = Scrollbar(self._frame_terminal, orient="vertical", command=self.terminal.yview)
        self._y_sidebar.pack(side='right', fill='y')
        self.terminal.configure(yscrollcommand=self._y_sidebar.set)

        # Configure color tags for log levels
        self.terminal.tag_config("INFO", foreground="black")
        self.terminal.tag_config("SUCCESS", foreground="green")
        self.terminal.tag_config("WARNING", foreground="darkorange")
        self.terminal.tag_config("ERROR", foreground="red")

    def write_text(self, text, level="INFO"):
        """
        Writes text to terminal. Compatible with string-only calls write_text(msg)
        and leveled calls write_text(msg, "SUCCESS").
        """
        if level.upper() in ["INFO", "SUCCESS", "WARNING", "ERROR"]:
            tag = level.upper()
        else:
            "INFO"

        # Ensure trailing newline if omitted
        if not text.endswith("\n"):
            text += "\n"

        self.terminal.config(state="normal")
        self.terminal.insert("end", text, tag)
        self.terminal.see("end")

    def clear_text(self):
        self.terminal.config(state="normal")
        self.terminal.delete(1.0, "end")
        self.terminal.config(state="disabled")


# -----------------------------------------------------------
#   Code Testing
# -----------------------------------------------------------
def main():
    win = Tk()
    win.title('Test of a Terminal Widget')

    a = Label(win, text="and now something completely different...")
    a.grid(row=1, column=1)

    box = Terminal(win)
    box.grid(row=1, column=2)

    for i in range(26):
        box.write_text("String number: " + str(i) + "\n")

    win.mainloop()


if __name__ == '__main__':
    main()
