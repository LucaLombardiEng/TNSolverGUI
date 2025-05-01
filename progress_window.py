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

        # self._clear_button = Button(self._frame_terminal, text="Clear Text", command=self.clear_text)
        # self._clear_button.pack(expand=1, fill='both', anchor='s')

    def write_text(self, text):
        self.terminal.insert("end", text)
        self.terminal.see("end")

    def clear_text(self):
        self.terminal.delete(1.0, "end")


def main():

    win = Tk()
    win.title('Test of a Terminal Widget')

    a = Label(win, text="and now something completely different...")
    a.grid(row=1, column=1)

    box = Terminal(win)
    box.grid(row=1, column=2)

    for i in range(26):
        box.write_text("String number: "+str(i)+"\n")



    win.mainloop()


if __name__ == '__main__':
    main()
