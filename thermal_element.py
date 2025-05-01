#
# Graphical Utility to manage the thermal elements
#
from tkinter import Tk, Canvas, Label
from tkinter.font import Font
import gUtility
import numpy as np
# uncomment during the class test
# from thermal_node import ThermalNode
# from thermal_network import GraphicWindow

elm_attributes = ('elmID', 'elmType', 'elmSubType', 'label', 'comment', 'material', 'area', 'thermal_conductivity',
                  'velocity', 'characteristic_length', 'angle_theta', 'radius', 'inner_radius', 'outer_radius',
                  'height', 'width', 'convection_htc', 'x_begin', 'x_end', 'emissivity', 'exchange_factor_12',
                  'exchange_factor_21', 'ctrX', 'ctrY', 'nodeIn', 'nodeOut', 'color')


class ThermalElm:
    def __init__(self, can, elmID, elmType, elmSubType):
        """ physical properties """
        self.elmID = elmID
        self.elmType = elmType
        self.elmSubType = elmSubType
        self.label = 'element_' + str(self.elmID)
        self.comment = elmSubType
        self.material = 'air'
        self.area = [1, f'm\N{SUPERSCRIPT TWO}']
        self.thermal_conductivity = [1, f'W/m·K']
        self.velocity = [1, f'm/s']
        self.characteristic_length = [1, f'm']
        self.angle_theta = [1, f'rad']
        self.radius = [1, f'm']
        self.inner_radius = [1, f'm']
        self.outer_radius = [2, f'm']
        self.height = [1, f'm']
        self.width = [1, f'm']
        self.convection_htc = [1, f'W/m\N{SUPERSCRIPT TWO}·K']
        self.x_begin = [0, f'm']
        self.x_end = [1, f'm']
        self.emissivity = [1, '']
        self.exchange_factor_12 = [0, '']
        self.exchange_factor_21 = [0, '']
        self.solution = None
        """ graphical properties """
        self.can = can
        self.font = Font(root=self.can, font=gUtility.font)  # create font object
        self.font_size = gUtility.font_size  # keep track of exact font size which is rounded in the zoom
        self.g_code = None
        self.g_ID = None
        self.g_elm = None
        self.g_conIn = None
        self.g_conOut = None
        self.g_solution = None
        self.ctrX = None
        self.ctrY = None
        self.color = None
        self.startX = None
        self.startY = None
        self.endX = None
        self.endY = None
        self.nodeIn = None
        self.nodeOut = None

    def draw_elm(self, x, y, *arg):
        """
        Draw the thermal element elmID in the canvas can at the coordinate (x, y)
        x: coordinate x of the node
        y: coordinate y of the node
        *arg: tuple of argument containing the time for the solution. if not present the initial condition will
              not be printed
        """
        self.ctrX = x
        self.ctrY = y
        self.startX = self.ctrX - gUtility.elmsize / 2
        self.startY = self.ctrY - gUtility.elmsize / 2
        self.endX = self.ctrX + gUtility.elmsize / 2
        self.endY = self.ctrY + gUtility.elmsize / 2
        self.color = gUtility.get_elm_color(self.elmType)

        if self.g_elm is None:  # check if the element is already drawn
            self.g_elm = self.can.create_rectangle(self.startX,
                                                   self.startY,
                                                   self.endX,
                                                   self.endY,
                                                   width=1,
                                                   fill="black",
                                                   outline=self.color,
                                                   tags=("drag", "elm", self.elmID, "elm_body"))
            self.g_ID = self.can.create_text(self.ctrX,
                                             self.ctrY,
                                             text=self.elmID,
                                             font=(self.font, self.font_size),
                                             fill=self.color,
                                             tags=("drag", "elm", self.elmID, "text"))
            self.g_code = self.can.create_text(self.ctrX,
                                               self.endY + 10,
                                               text=self.elmSubType,
                                               font=(self.font, self.font_size),
                                               fill=self.color,
                                               tags=("drag", "elm", self.elmID, "text"))
        else:  # the element is already in the graphical window
            self.can.coords(self.g_elm,
                            self.startX,
                            self.startY,
                            self.endX,
                            self.endY)

        if arg and self.solution is not None:
            time_value = float(arg[0])
            if len(self.solution) == 2:
                solution = self.solution[1]
                solution = 'Q= ' + str(round(solution, gUtility.digits)) + 'W'
            else:
                index = np.where(self.solution[:, 0] == time_value)[0]
                solution = self.solution[index[0], 1]
                solution = 'Q= ' + str(round(solution, gUtility.digits)) + 'W'
            if self.g_solution is None:  # the solution is not yet in the graphical window
                self.g_solution = self.can.create_text(self.ctrX,
                                                       self.ctrY + 40,
                                                       text=solution,
                                                       font=(self.font, self.font_size),
                                                       fill=self.color,
                                                       tags=("drag", "elm", self.elmID, "text"))
            else:
                self.can.itemconfig(self.g_solution, text=solution)
                self.can.coords(self.g_solution, self.ctrX, self.ctrY + 40)

    def delete_elm(self):
        # Delete permanently the thermal element elmID in the canvas can
        self.can.delete(self.g_elm)
        self.can.delete(self.g_ID)
        self.can.delete(self.g_code)
        self.can.delete(self.g_conIn)
        self.can.delete(self.g_conOut)
        if self.g_solution is not None:
            self.can.delete(self.g_solution)

    def move_elm(self, x, y):
        dx = x - self.ctrX
        dy = y - self.ctrY
        self.elm_selected_color()
        self.can.move(self.g_elm, dx, dy)
        self.can.move(self.g_ID, dx, dy)
        self.can.move(self.g_code, dx, dy)
        if self.g_solution is not None:
            self.can.move(self.g_solution, dx, dy)
        self.ctrX = x
        self.ctrY = y
        if self.g_conIn:
            x1 = self.can.coords(self.g_conIn)[2]
            y1 = self.can.coords(self.g_conIn)[3]
            self.update_g_conIn(x1, y1)
        if self.g_conOut:
            x1 = self.can.coords(self.g_conOut)[2]
            y1 = self.can.coords(self.g_conOut)[3]
            self.update_g_conOut(x1, y1)
        self.elm_unselected_color()

    def update_g_conIn(self, x1, y1):
        self.can.coords(self.g_conIn, self.ctrX, self.ctrY, x1, y1)

    def update_g_conOut(self, x1, y1):
        self.can.coords(self.g_conOut, self.ctrX, self.ctrY, x1, y1)

    def draw_connector_in(self, x, y, node_in):
        self.nodeIn = node_in
        self.g_conIn = self.can.create_line(self.ctrX, self.ctrY, x, y, fill=self.color,
                                            tags=("drag", "connector_in", self.elmID, node_in))
        self.can.tag_lower("connector_in")

    def draw_connector_out(self, x, y, node_out):
        self.nodeOut = node_out
        self.g_conOut = self.can.create_line(self.ctrX, self.ctrY, x, y, fill=self.color,
                                             tags=("drag", "connector_out", self.elmID, node_out))
        self.can.tag_lower("connector_out")

    def elm_selected_color(self):
        self.can.itemconfig(self.g_elm, outline="gray70")
        self.can.itemconfig(self.g_ID, fill="gray70")
        self.can.itemconfig(self.g_code, fill="gray70")
        self.can.itemconfig(self.g_conIn, fill="gray70")
        self.can.itemconfig(self.g_conOut, fill="gray70")
        if self.g_solution is not None:
            self.can.itemconfig(self.g_solution, fill="gray70")

    def elm_unselected_color(self):
        self.can.itemconfig(self.g_elm, outline=self.color)
        self.can.itemconfig(self.g_ID, fill=self.color)
        self.can.itemconfig(self.g_code, fill=self.color)
        self.can.itemconfig(self.g_conIn, fill=self.color)
        self.can.itemconfig(self.g_conOut, fill=self.color)
        if self.g_solution is not None:
            self.can.itemconfig(self.g_solution, fill=self.color)

    def serialize(self):
        serialized_elm = {"ID": self.elmID,
                          "type": self.elmType,
                          "subtype": self.elmSubType,
                          "label": self.label,
                          "comment": self.comment,
                          "material": self.material,
                          "area": self.area,
                          "thermal conductivity": self.thermal_conductivity,
                          "velocity": self.velocity,
                          "characteristic length": self.characteristic_length,
                          "angle theta": self.angle_theta,
                          "radius": self.radius,
                          "inner radius": self.inner_radius,
                          "outer radius": self.outer_radius,
                          "height": self.height,
                          "width": self.width,
                          "convection htc": self.convection_htc,
                          "x begin": self.x_begin,
                          "x end": self.x_end,
                          "emissivity": self.emissivity,
                          "exchange factor 12": self.exchange_factor_12,
                          "exchange factor 21": self.exchange_factor_21,
                          "center X": self.ctrX,
                          "center Y": self.ctrY,
                          "inlet node id": self.nodeIn,
                          "exit node id": self.nodeOut,
                          "solution": self.solution
                          }
        return serialized_elm

    def update_solution(self, time):
        index_ = np.where(self.solution[:, 0] == float(time))
        value = self.solution[index_[0][0], 1]
        value = 'Q= ' + str(np.round(value, gUtility.digits)) + 'W'
        self.can.itemconfig(self.g_solution, text=value)


"""--------------------------------------------------------------------------------------------------------------"""


def clicked(event):
    clicked_id = event.widget.find_withtag('current')[0]
    item_id = event.widget.gettags(clicked_id)[2]
    if event.widget.gettags(clicked_id)[1] == "elm":
        print("Elm selected: ", item_id)
        print("Center X: ", listElm[int(item_id)].ctrX)
        print("Center Y: ", listElm[int(item_id)].ctrY)
        print("Elm Type: ", listElm[int(item_id)].elmType)
        print("Elm code: ", listElm[int(item_id)].elmSubType)
        print("Elm color: ", listElm[int(item_id)].color)
        print("Node In: ", listElm[int(item_id)].nodeIn)
        print("Node Out: ", listElm[int(item_id)].nodeOut)


def connect_elm(event):
    global follow_line, elm_id, node_id, start_vector
    clicked_id = event.widget.find_withtag('current')[0]
    print("board ID elem selected: ", clicked_id)
    if event.widget.gettags(clicked_id)[1] == "elm":
        elm_id = event.widget.gettags(clicked_id)[2]
        print("ID elem selected: ", elm_id)
        # check if the out connection is done
        if listElm[int(elm_id)].g_conOut is None:
            start_vector = [listElm[int(elm_id)].ctrX, listElm[int(elm_id)].ctrY]
            follow_line = True
        else:
            pass
    elif event.widget.gettags(clicked_id)[1] == "node" and elm_id:
        node_id = event.widget.gettags(clicked_id)[2]
        follow_line = False
        test_board.th_canvas.delete('connection_line')
        x = listNode[int(node_id)].ctrX
        y = listNode[int(node_id)].ctrY
        if listElm[int(elm_id)].g_conIn is None:
            listElm[int(elm_id)].draw_connector_in(x, y, node_id)
        else:
            listElm[int(elm_id)].draw_connector_out(x, y, node_id)
        elm_id = None
        node_id = None
    elif event.widget.gettags(clicked_id)[1] == "connector_in":
        elm_id = event.widget.gettags(clicked_id)[2]
        listElm[int(elm_id)].g_conIn = None
        start_vector = [listElm[int(elm_id)].ctrX, listElm[int(elm_id)].ctrY]
        test_board.th_canvas.delete(clicked_id)
        follow_line = True
    elif event.widget.gettags(clicked_id)[1] == "connector_out":
        elm_id = event.widget.gettags(clicked_id)[2]
        listElm[int(elm_id)].g_conOut = None
        start_vector = [listElm[int(elm_id)].ctrX, listElm[int(elm_id)].ctrY]
        test_board.th_canvas.delete(clicked_id)
        follow_line = True
    else:
        pass


def drag(event):
    clicked_id = event.widget.find_withtag('current')[0]
    if event.widget.gettags(clicked_id)[1] == "elm":
        elm_tag = event.widget.gettags(clicked_id)[2]
        listElm[int(elm_tag)].move_elm(event.x, event.y)
    else:
        pass


def on_move(event):
    global follow_line, elm_id, start_vector
    if elm_id is not None and follow_line:
        print(start_vector, event.x, event.y)
        draw_line(start_vector[0], start_vector[1], event.x, event.y)


def draw_line(x1, y1, x2, y2):
    test_board.th_canvas.delete('connection_line')  # Delete previous line before drawing a new one
    test_board.th_canvas.create_line(x1, y1, x2, y2, fill="red", tag="connection_line")
    test_board.th_canvas.tag_lower("connection_line")


if __name__ == '__main__':
    win = Tk()
    win.title('Test of Graphic elements')

    test_board = GraphicWindow(win)
    test_board.grid(row=1, column=1)
    label_1 = Label(win, text="use right button to connect an element")
    label_1.grid(row=2, column=1)

    # define the elements in a dictionary for a fast search
    listElm = {1: ThermalElm(test_board.th_canvas, 1, "Conduction", "cond.lin"),
               2: ThermalElm(test_board.th_canvas, 2, "Convection", "conv.1004"),
               3: ThermalElm(test_board.th_canvas, 3, "Radiation", "rad.111"),
               4: ThermalElm(test_board.th_canvas, 4, "boh", "err"),
               5: ThermalElm(test_board.th_canvas, 5, "Conduction", "Selected")}

    # draw a conduction element
    for index in listElm:
        listElm[index].draw_elm(100 + (index - 1) * 70, 50)

    listElm[1].move_elm(100, 100)
    listElm[5].elm_selected_color()

    # define the elements in a dictionary for a fast search
    listNode = {100: ThermalNode(test_board.th_canvas, 100, "Temperature"),
                2: ThermalNode(test_board.th_canvas, 2, "Heat Flux"),
                3: ThermalNode(test_board.th_canvas, 3, "Internal Node"),
                4: ThermalNode(test_board.th_canvas, 4, "Internal Node")}

    # draw a conduction element
    for index in listNode:
        x = 100 + (index - 1) * 70
        if x < 500:
            listNode[index].draw_node(x, 300)
        else:
            x = 250
            listNode[index].draw_node(x, 400)

    # global follow_line, elm_id, start_vector
    follow_line = False
    elm_id = None
    node_id = None
    start_vector = []

    test_board.th_canvas.bind("<Motion>", lambda e: on_move)
    test_board.th_canvas.tag_bind("drag", "<Button-1>", lambda e: clicked(e))
    test_board.th_canvas.tag_bind("drag", "<B1-Motion>", lambda e: drag(e))
    test_board.th_canvas.tag_bind("drag", "<ButtonRelease-3>", lambda e: connect_elm(e))
    test_board.th_canvas.bind("<ButtonPress-2>", test_board.move_start)
    test_board.th_canvas.bind("<B2-Motion>", test_board.move_move)
    test_board.th_canvas.bind("<MouseWheel>", test_board.zoomer)

    win.mainloop()
