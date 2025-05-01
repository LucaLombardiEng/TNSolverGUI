from tkinter import Tk, LabelFrame, Label, Frame, Canvas, Scrollbar, VERTICAL, HORIZONTAL
from tkinter.font import Font
import random
import gUtility

"""
    Graphic Frame in the GUI for the TNSolver
    
    Luca Lombardi
    Rev 0: First Draft

    next steps:
    scrolling
    panning
    zooming
    background
"""


class GraphicWindow(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)

        self.title = None
        # self._board = LabelFrame(self, width=400, height=600, padx=5, pady=0)
        self._board = LabelFrame(self, padx=5, pady=0)
        self.font = Font(self, gUtility.font)  # create font object
        self.font_size = gUtility.font_size  # keep track of exact font size which is rounded in the zoom
        # Prepare the canvas and the scroll bars
        self.th_canvas = Canvas(self._board, width=1300, height=630, bg="black")
        # self.th_canvas = Canvas(self._board, height=570, bg="black")
        self.xsb = Scrollbar(self._board, orient="horizontal", command=self.th_canvas.xview)
        self.ysb = Scrollbar(self._board, orient="vertical", command=self.th_canvas.yview)
        self.th_canvas.configure(yscrollcommand=self.ysb.set, xscrollcommand=self.xsb.set)
        self.th_canvas.configure(scrollregion=(0, 0, 1300, 630))
        self.ysb.pack(side='right', expand=1, fill='y', pady=self.xsb.winfo_height())
        self.xsb.pack(side='bottom', expand=1, fill='x', padx=self.ysb.winfo_width())
        self.th_canvas.pack(expand=1, fill='both', anchor='nw')
        self._board.pack(side='left', pady=10, expand=1, fill='x', anchor='n')
        self.zoom_level = 100
        self.offset = [0, 0]

    def naming(self, title):
        self.title = title
        self._board.configure(text=self.title)

    def move_start(self, event):
        self.th_canvas.scan_mark(event.x, event.y)

    def move_move(self, event):
        self.th_canvas.scan_dragto(event.x, event.y, gain=1)

    def offset_calc(self, event):
        self.offset = [self.th_canvas.canvasx(0), self.th_canvas.canvasy(0)]
        # print('X total offset:' + str(self.offset[0]) + ' - Y total offset:' + str(self.offset[1]))
        # print('coordinates obj 1: ' + str(self.th_canvas.coords('object-1')))
        # print('---------------------------------------------------')

    def print_coord(self, event):
        abs_x = self.th_canvas.canvasx(event.x)
        abs_y = self.th_canvas.canvasy(event.y)
        print('screen coordinates:'+str(event.x)+', '+str(event.y))
        print('Canvas coordinates:' + str(abs_x) + ', ' + str(abs_y))

    def zoom(self, event):
        zoom_factor = 1
        step = 1 if event.delta > 0 else -1
        if (event.delta > 0 and self.zoom_level < 400) or (event.delta < 0 and self.zoom_level > 10):
            zoom_factor = 1 + step / self.zoom_level
            print('Zoom Factor: ' + str(zoom_factor))
            self.zoom_level += step
            print('Zoom level: ' + str(self.zoom_level))
            self.font_size *= zoom_factor
            # self.th_canvas.scale("all", 0, 0, zoom_factor, zoom_factor)
            self.th_canvas.scale("all",
                                 event.x + self.th_canvas.canvasx(0),
                                 event.y + self.th_canvas.canvasy(0),
                                 zoom_factor,
                                 zoom_factor)
            self.th_canvas.configure(scrollregion=self.th_canvas.bbox("all"))
            self.font.configure(size=int(self.font_size))  # update font size
            self.th_canvas.itemconfig("text", font=self.font)
            gUtility.nodesize *= zoom_factor
            gUtility.elmsize *= zoom_factor
            gUtility.font_size = int(self.font_size)
            print('Font size: ' + str(gUtility.font_size))
            self.offset = [self.th_canvas.canvasx(0), self.th_canvas.canvasy(0)]
            print('X total offset:' + str(self.offset[0]) + ' - Y total offset:' + str(self.offset[1]))
            print('coordinates obj 1: ' + str(self.th_canvas.coords('object-1')))
            print('---------------------------------------------------')
        return zoom_factor


if __name__ == '__main__':
    win = Tk()
    win.title('Test of Graphical Board Widget')

    test_board = GraphicWindow(win)
    test_board.naming("Thermal Network Graphic Tree")
    test_board.pack(padx=10)

    for n in range(5):
        x0 = random.randint(0, 900)
        y0 = random.randint(50, 900)
        x1 = x0 + random.randint(50, 100)
        y1 = y0 + random.randint(50, 100)
        color = ("red", "orange", "yellow", "green", "blue")[random.randint(0, 4)]
        my_tag = 'object-' + str(n)
        print(my_tag)
        test_board.th_canvas.create_rectangle(x0, y0, x1, y1, outline="black", fill=color, activefill="black",
                                              tags=my_tag)
        test_board.th_canvas.create_text((x0 + x1) * 0.5, (y0 + y1) * 0.5, anchor="nw", fill="white",
                                         font=test_board.font,
                                         text=str(n))

    # let's place a small item on the SE corner to prevent the automatic resizing of the canvas
    test_board.th_canvas.create_rectangle(9999, 9999, 10000, 10000, outline="black", fill="black",
                                          activefill="black",
                                          tags=str('SE - angle'))
    # let's place a rectangle with the size of the canvas.
    test_board.th_canvas.create_rectangle(0, 0, 10000, 10000, outline="white", tags=str('canvas frame'))
    test_board.th_canvas.create_text(50, 10, anchor="nw", fill="white", font=test_board.font,
                                     text="Click and drag to move the canvas\nScroll to zoom.")

    test_board.th_canvas.bind("<ButtonPress-2>", test_board.move_start)
    test_board.th_canvas.bind("<B2-Motion>", test_board.move_move)
    test_board.th_canvas.bind("<ButtonRelease-2>", test_board.offset_calc)
    test_board.th_canvas.bind("<ButtonRelease-1>", test_board.print_coord)
    test_board.th_canvas.bind("<MouseWheel>", test_board.zoom)

    win.mainloop()


