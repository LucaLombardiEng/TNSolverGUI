"""
    Thermal Solver Network - Progress Terminal
    This class permits the communication of the events with the user avoiding pop-ups and maintaining the
    journal of the messages

    Luca Lombardi
    Rev 0: First Draft
    Rev 1: 2026 Sep 02 Update to handle message levels (Info, Success, Warning, Error) with color coding
           to improve readability
    Rev 2: 2026 Oct 06 Class LogManager added to maintain log history and broadcasts to all active Terminal widgets.
"""

from tkinter import Tk, LabelFrame, Frame, Text, Scrollbar


class LogManager:
    """Central hub that maintains log history and broadcasts to all active Terminal widgets."""
    def __init__(self):
        self.history = []
        self.terminals = []

    def register(self, terminal_widget):
        # Prevent registering None objects if a tab initializes out of order
        if terminal_widget is None:
            return

        if terminal_widget not in self.terminals:
            self.terminals.append(terminal_widget)
            # Immediately dump the existing history into the newly registered terminal
            for text, level in self.history:
                terminal_widget.write_text(text, level)

    def write_text(self, text, level="INFO"):
        self.history.append((text, level))

        valid_terminals = []
        for t in self.terminals:
            # Check that the terminal exists and hasn't been destroyed by closing a tab
            if t is not None and t.winfo_exists():
                t.write_text(text, level)
                valid_terminals.append(t)

        # Self-clean the list of any invalid or destroyed terminals
        self.terminals = valid_terminals

    def clear_text(self):
        self.history.clear()

        valid_terminals = []
        for t in self.terminals:
            if t is not None and t.winfo_exists():
                t.clear_text()
                valid_terminals.append(t)

        self.terminals = valid_terminals


class Terminal(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)

        self._frame_terminal = LabelFrame(self, text="Progress report terminal", width=2000, height=200, padx=10, pady=5)
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

        # Initialize terminal state as read-only
        self.terminal.config(state="disabled")

    def write_text(self, text, level="INFO"):
        """
        Writes text to terminal. Safely handles inputs from LogManager or direct calls.
        """
        # Ensure a valid tag is assigned, defaulting to INFO if unknown
        tag = level.upper() if level.upper() in ["INFO", "SUCCESS", "WARNING", "ERROR"] else "INFO"

        # Ensure trailing newline if omitted
        if not text.endswith("\n"):
            text += "\n"

        # Temporarily unlock the widget to insert text, then lock it back
        self.terminal.config(state="normal")
        self.terminal.insert("end", text, tag)
        self.terminal.see("end")
        self.terminal.config(state="disabled")

    def clear_text(self):
        self.terminal.config(state="normal")
        self.terminal.delete("1.0", "end")
        self.terminal.config(state="disabled")


# -----------------------------------------------------------
#   Code Testing
# -----------------------------------------------------------
if __name__ == '__main__':
    win = Tk()
    win.title('Test of a Terminal Widget')

    box = Terminal(win)
    box.grid(row=1, column=1)

    # Test Standard Prints
    for i in range(5):
        box.write_text(f"Standard log entry number: {i}")

    # Test Color Coding
    box.write_text("Operation completed successfully.", "SUCCESS")
    box.write_text("This is a warning message.", "WARNING")
    box.write_text("A critical error occurred.", "ERROR")
    box.write_text("Fallback tag test.", "UNKNOWN_TAG") # Safely falls back to INFO

    win.mainloop()