#
# Graphical Utility to manage the thermal elements
#
from tkinter import Tk
from tkinter.font import Font

# from thermal_network import GraphicWindow
import gUtility
import math
import numpy as np

node_attributes = ('node_ID', 'node_type', 'node_label', 'node_comment', 'node_material', 'node_volume', 'node_density',
                   'node_Cp', 'node_area', 'node_temperature', 'node_heat_flux', 'node_volumetric_power', 'node_power',
                   'node_thermostatic_node', 'node_temp_on', 'node_temp_off', 'ctrX', 'ctrY', 'elm_list_in',
                   'elm_list_out', 'color')


class ThermalNode:
    def __init__(self, canvas, node_ID, node_type):
        """ physical properties """
        self.node_ID = node_ID
        self.node_type = node_type
        self.node_label = 'node_' + str(self.node_ID)
        self.node_comment = 'air node'
        self.node_material = 'air'
        self.node_volume = [0, f'm\N{SUPERSCRIPT THREE}']
        self.node_density = [0, f'kg/m\N{SUPERSCRIPT THREE}']
        self.node_Cp = [0, f'J/kg·K']
        self.node_area = [0, f'm\N{SUPERSCRIPT TWO}']
        self.node_temperature = [20, f'°C']
        self.node_heat_flux = [0, f'W/m\N{SUPERSCRIPT TWO}']
        self.node_volumetric_power = [0, f'W/m\N{SUPERSCRIPT THREE}']
        self.node_power = [0, f'W']
        self.node_thermostatic_node = None
        self.node_temp_on = [20, f'°C']
        self.node_temp_on = [20, f'°C']
        self.node_temp_off = [20, f'°C']
        self.node_solution = None
        """ graphical properties """
        self.can = canvas
        self.font = Font(root=self.can, font=gUtility.font)  # create font object
        self.font_size = gUtility.font_size  # keep track of exact font size which is rounded in the zoom
        self.g_body = None
        self.g_ID = None
        self.g_solution = None
        self.elm_list_in = []
        self.elm_list_out = []
        self.ctrX = None
        self.ctrY = None
        self.startX = None
        self.startY = None
        self.endX = None
        self.endY = None
        self.color = None

    @staticmethod
    def _draw_regular_polygon(center, radius, n, angle):
        angle -= (math.pi / n)
        coord_list = [[center[0] + radius * math.sin((2 * math.pi / n) * i - angle),
                       center[1] + radius * math.cos((2 * math.pi / n) * i - angle)] for i in range(n)]
        return coord_list

    def draw_node(self, x, y, *arg):
        """
        Draw the thermal node nodeID in the canvas can at the coordinate (x, y)
        x: coordinate x of the node
        y: coordinate y of the node
        *arg: tuple of argument containing the time for the solution. if not present the initial condition will
               not be printed
        """

        self.ctrX = x
        self.ctrY = y
        self.startX = self.ctrX - gUtility.nodesize / 2
        self.startY = self.ctrY - gUtility.nodesize / 2
        self.endX = self.ctrX + gUtility.nodesize / 2
        self.endY = self.ctrY + gUtility.nodesize / 2
        self.color = gUtility.get_node_color(self.node_type)
        if self.g_body is None:  # check if the node is already drawn
            if self.node_type == "Internal Node":
                self.g_body = self.can.create_oval(self.startX,
                                                   self.startY,
                                                   self.endX,
                                                   self.endY,
                                                   width=1,
                                                   fill="black",
                                                   outline=self.color,
                                                   tags=("drag", "node", self.node_ID, "int_node_body"))
            else:
                coord_list = self._draw_regular_polygon([self.ctrX, self.ctrY],
                                                        gUtility.nodesize / 2, 8, 0)
                self.g_body = self.can.create_polygon(coord_list,
                                                      width=1,
                                                      fill="black",
                                                      outline=self.color,
                                                      tags=("drag", "node", self.node_ID, "node_body"))

            self.g_ID = self.can.create_text(self.ctrX, self.ctrY, text=self.node_ID, font=(self.font, self.font_size),
                                             fill=self.color, tags=("drag", "node", self.node_ID, "text"))
        else:  # the node is already in the graphical window
            if self.node_type == "Internal Node":
                self.can.coords(self.g_body,
                                self.startX,
                                self.startY,
                                self.endX,
                                self.endY)
            else:
                coord_list = self._draw_regular_polygon([self.ctrX, self.ctrY], gUtility.nodesize / 2, 8, 0)
                # Flatten the coordinate list before passing to coords
                flat_coords = [coord for sublist in coord_list for coord in sublist]
                self.can.coords(self.g_body, *flat_coords)
            self.can.coords(self.g_ID, self.ctrX, self.ctrY)

        if arg and self.node_solution is not None:
            time_value = float(arg[0])
            if len(self.node_solution) == 2:
                solution = self.node_solution[1]
                solution = 'T= ' + str(round(solution, gUtility.digits)) + '°C'
            else:
                index = np.where(self.node_solution[:, 0] == time_value)[0]
                solution = self.node_solution[index[0], 1]
                solution = 'T= ' + str(round(solution, gUtility.digits)) + '°C'
            if self.g_solution is None:  # the solution is not yet in the graphical window
                self.g_solution = self.can.create_text(self.ctrX,
                                                       self.ctrY + 25,
                                                       text=solution,
                                                       font=(self.font, self.font_size),
                                                       fill=self.color,
                                                       tags=("drag", "node", self.node_ID, "text"))
            else:
                self.can.itemconfig(self.g_solution, text=solution)
                self.can.coords(self.g_solution, self.ctrX, self.ctrY + 25)

    def delete_node(self):
        # Delete permanently the thermal node in the canvas
        self.can.delete(self.g_body)
        self.can.delete(self.g_ID)
        if self.g_solution is not None:
            self.can.delete(self.g_solution)

    def move_node(self, x, y):
        dx = x - self.ctrX
        dy = y - self.ctrY
        self.can.move(self.g_body, dx, dy)
        self.can.move(self.g_ID, dx, dy)
        if self.g_solution is not None:
            self.can.move(self.g_solution, dx, dy)
        self.ctrX = x
        self.ctrY = y

    def serialize(self):
        serialized_node = {"ID": self.node_ID,
                           "type": self.node_type,
                           "label": self.node_label,
                           "comment": self.node_comment,
                           "material": self.node_material,
                           "volume": self.node_volume,
                           "density": self.node_density,
                           "specific Heat": self.node_Cp,
                           "area": self.node_area,
                           "temperature": self.node_temperature,
                           "heat flux": self.node_heat_flux,
                           "volumetric power": self.node_volumetric_power,
                           "power": self.node_power,
                           "solution": self.node_solution,
                           "thermostatic node id": self.node_thermostatic_node,
                           "temperature on": self.node_temp_on,
                           "temperature off": self.node_temp_off,
                           "inlet element list": self.elm_list_in,
                           "exit element list": self.elm_list_out,
                           "center X": self.ctrX,
                           "center Y": self.ctrY
                           }
        return serialized_node

    def node_selected_color(self):
        self.can.itemconfig(self.g_body, outline="gray70")
        self.can.itemconfig(self.g_ID, fill="gray70")
        if self.g_solution is not None:
            self.can.itemconfig(self.g_solution, fill="gray70")

    def node_unselected_color(self):
        self.can.itemconfig(self.g_body, outline=self.color)
        self.can.itemconfig(self.g_ID, fill=self.color)
        if self.g_solution is not None:
            self.can.itemconfig(self.g_solution, fill=self.color)

    def update_solution(self, time):
        index = np.where(self.node_solution[:, 0] == float(time))
        value = self.node_solution[index[0][0], 1]
        value = 'T= ' + str(np.round(value, gUtility.digits)) + '°C'
        self.can.itemconfig(self.g_solution, text=value)

# -------------------------------------------------------------------------------------------------------------

def clicked(event):
    clicked_id = event.widget.find_withtag('current')[0]
    elm_tag = event.widget.gettags(clicked_id)
    elms = event.widget.find_withtag(elm_tag)
    # lastx, lasty = event.x, event.y
    print("tag = ", clicked_id)
    print("tags", elm_tag)
    print("elm ensemble", elms)


def drag(event, listElm):
    clicked_id = event.widget.find_withtag('current')[0]
    elm_tag = event.widget.gettags(clicked_id)[2]
    listElm[int(elm_tag)].move_node(event.x, event.y)


def main():
    win = Tk()
    win.title('Test of Graphic elements')

    test_board = Canvas(win, width=500, height=500, bg="black")
    # test_board = GraphicWindow(win)
    test_board.grid(row=1, column=1)

    # define the elements in a dictionary for a fast search
    listNode = {100: ThermalNode(test_board.th_canvas, 100, "Temperature"),
                2: ThermalNode(test_board.th_canvas, 2, "Heat Flux"),
                3: ThermalNode(test_board.th_canvas, 3, "Internal Node"),
                4: ThermalNode(test_board.th_canvas, 4, "Internal Node")}

    # draw a conduction element

    for index in listNode:
        x = 100 + (index - 1) * 70
        if x < 500:
            listNode[index].draw_node(x, 50)
        else:
            x = 250
            listNode[index].draw_node(x, 85)

    test_board.th_canvas.tag_bind("drag", "<Button-1>", clicked)
    test_board.th_canvas.tag_bind("drag", "<B1-Motion>", lambda e: drag(e, listNode))
    test_board.th_canvas.bind("<ButtonPress-2>", test_board.move_start)
    test_board.th_canvas.bind("<B2-Motion>", test_board.move_move)
    test_board.th_canvas.bind("<MouseWheel>", test_board.zoomer)

    win.mainloop()


if __name__ == '__main__':
    main()
