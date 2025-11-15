"""
    Class ThermalNetwork
    It is the GUI that permits the interaction with the thermal network.
    The nodes and elements can be dragged and dropped in the graphical area, connected, reconnected, deleted amd edited.

    Luca Lombardi
    Rev 0: First Draft

    next steps:
     - drag the entire network, activate the CTRL+A?
     - renumber,
     - zoom in/out: implement the autoscroll to give the feeling of a continuous zoom centered to the mouse pointer
     - CTRL+f fit the graphic area

"""
from tkinter import Tk, Frame, Menu, PanedWindow, VERTICAL, HORIZONTAL, BOTH, messagebox
from tkinter.font import Font
import numpy as np

from TNSolver_GUI.Thermal_Network_TAB.graphic_frame import GraphicWindow
from TNSolver_GUI.Thermal_Network_TAB.progress_window import Terminal
from TNSolver_GUI.Thermal_Network_TAB.thermal_library import ThermalLibrary
from TNSolver_GUI.Thermal_Network_TAB.thermal_element import ThermalElm, elm_attributes
from TNSolver_GUI.Thermal_Network_TAB.thermal_node import ThermalNode, node_attributes
from TNSolver_GUI.Thermal_Network_TAB.property_editor import PropertyEditor
from TNSolver_GUI.Thermal_Network_TAB.solver_settings import SolverSetting
from TNSolver_GUI.Thermal_Network_TAB.graphic_plots import FunctionPlotter
from TNSolver_GUI.Thermal_Network_TAB.time_slider import ScaleFrame
from TNSolver_code.utility_functions import verdate
from TNSolver_GUI.Thermal_Network_TAB import gUtility


class ThermalNetwork(Frame):

    def __init__(self, parent, functions_dict):
        Frame.__init__(self, parent)
        # initialize variables
        self.functions_dict = functions_dict
        self.start_vector = []
        self.selected_elm = None
        self.selected_node = None
        self.drag_window = None
        self.item_code = None
        self.main_Panned_Window = None
        self.left_Panned_Window = None
        self.central_Panned_Window = None
        self.right_Panned_Window = None
        self.leftFrame = None
        self.centralFrame = None
        self.rightFrame = None
        self.solution_Frame = None
        self.slider_Frame = None
        self.bottomFrame = None
        self.plotFrame = None
        self.container = parent
        self.follow_line = False
        self.item_selection = {"node": [], "elm": []}
        self.elm_dict_copy = {}
        self.node_dict_copy = {}
        self.copied_shapes = []
        self.xg = [0.0, 0.0]  # [original xg, current xg] it will be used to track the final displacement of the copy
        self.yg = [0.0, 0.0]  # [original yg, current yg] it will be used to track the final displacement of the copy
        self.background = None

        # dictionary of the nodes and elements of the thermal network
        self.node_dict = {}
        self.elm_dict = {}

        self.font = Font(self, font=gUtility.font)  # create font object
        self.font_size = gUtility.font_size  # keep track of exact font size which is rounded in the zoom

        self.setup()
        self.welcome_message()

        self.RightMenu = Menu(self.centralFrame.th_canvas, tearoff=False)
        self.RightMenu.add_command(label="Select", command=self.Select)
        self.RightMenu.add_command(label="Copy", command=self.Copy)
        self.RightMenu.add_command(label="Paste", command=self.paste)
        self.RightMenu.add_separator()
        self.RightMenu.add_command(label="Delete", command=self.Delete)
        self.RightMenu.add_separator()
        self.RightMenu.add_command(label="Renumber", command=self.Renumber)

    def welcome_message(self):
        self.bottomFrame.write_text('TNSolver GUI\n'+verdate()+'\n')

    def right_menu_popup(self, event):
        self.RightMenu.tk_popup(event.x_root, event.y_root)

    def Select(self):
        pass

    def deselectAll(self):
        self.centralFrame.th_canvas.unbind("<Motion>")
        for n in self.item_selection["node"]:
            self.node_dict[n].node_unselected_color()
        for e in self.item_selection["elm"]:
            self.elm_dict[e].elm_unselected_color()
        self.item_selection['node'].clear()
        self.item_selection['elm'].clear()
        self.elm_dict_copy = {}
        self.node_dict_copy = {}
        self.copied_shapes.clear()
        self.selected_elm = None
        self.selected_node = None
        self.xg = [0.0, 0.0]
        self.yg = [0.0, 0.0]
        self.bind_events()

    def Copy(self):
        """
        The logic is the following:
            step 1: check if the selection is empty.
            step 2: unbind all the unnecessary events
            step 3: for each element in the selected list include the in - out nodes in the node list
            step 4: create a temporary node and element list
            step 5: calculate the center of gravity of the selection, and the distance of the farthest element
            step 6: draw the ghosts of the copied elements and append the references of the geometries in a list
        """

        nothing_to_copy = True
        graph, offset = self.graph_area()
        tot_offset = [offset[0] + self.centralFrame.offset[0], offset[1] + self.centralFrame.offset[1]]
        if len(self.item_selection["elm"]) != 0:
            for e in self.item_selection["elm"]:
                node_in = self.elm_dict[e].nodeIn
                node_out = self.elm_dict[e].nodeOut
                if node_in not in self.item_selection["node"]:
                    self.item_selection["node"].append(node_in)
                if node_out not in self.item_selection["node"]:
                    self.item_selection["node"].append(node_out)
            nothing_to_copy = False

        if len(self.item_selection["node"]) == 0:
            nothing_to_copy = True

        if nothing_to_copy:
            messagebox.showerror(title='Copy', message='Nothing to copy!')
        else:
            self.unbind_events()  # unbind other events, max focus on the copy
            node_translation = {}  # temporary node dictionary between the old and new node
            elm_translation = {}  # temporary element dictionary between the old and new elements
            self.elm_dict_copy = {}
            self.node_dict_copy = {}
            self.copied_shapes = []
            last_node = list(self.node_dict)[-1]
            last_elm = list(self.elm_dict)[-1]
            self.xg = [0.0, 0.0]  # center of gravity of the copied items
            self.yg = [0.0, 0.0]
            for e in self.item_selection["elm"]:
                last_elm += 1
                self.elm_dict_copy[last_elm] = ThermalElm(self.centralFrame.th_canvas, last_elm, None, None)
                elm_translation[e] = last_elm  # search the new copy element ID
                elm_translation[-last_elm] = e  # search the copied element ID
                for attr in elm_attributes[1:]:  # skip elmID
                    setattr(self.elm_dict_copy[last_elm], attr, getattr(self.elm_dict[e], attr))
                self.xg[0] += self.elm_dict_copy[last_elm].ctrX
                self.yg[0] += self.elm_dict_copy[last_elm].ctrY
            for n in self.item_selection["node"]:
                last_node += 1
                self.node_dict_copy[last_node] = ThermalNode(self.centralFrame.th_canvas, last_node, None)
                node_translation[n] = last_node  # search the new copy node ID
                node_translation[-last_node] = n  # search the copied node ID
                for attr in node_attributes[1:]:  # skip node_ID
                    setattr(self.node_dict_copy[last_node], attr, getattr(self.node_dict[n], attr))
                self.xg[0] += self.node_dict_copy[last_node].ctrX
                self.yg[0] += self.node_dict_copy[last_node].ctrY
            # calculate the center of gravity of the copies
            self.xg[0] = self.xg[0] / (len(self.elm_dict_copy)+len(self.node_dict_copy))
            self.yg[0] = self.yg[0] / (len(self.elm_dict_copy) + len(self.node_dict_copy))
            # draw the copied items
            for n_key in self.node_dict_copy:
                x = self.node_dict_copy[n_key].ctrX
                y = self.node_dict_copy[n_key].ctrY
                self.node_dict_copy[n_key].draw_node(x, y)
                self.node_dict_copy[n_key].node_selected_color()

                elm_list = []
                for elmID in self.node_dict_copy[n_key].elm_list_in:
                    if elmID in elm_translation:
                        elm_list.append(elm_translation[elmID])
                self.node_dict_copy[n_key].elm_list_in = list.copy(elm_list)
                elm_list.clear()

                for elmID in self.node_dict_copy[n_key].elm_list_out:
                    if elmID in elm_translation:
                        elm_list.append(elm_translation[elmID])
                self.node_dict_copy[n_key].elm_list_out = list.copy(elm_list)
                elm_list.clear()

                self.copied_shapes.append(self.node_dict_copy[n_key].g_body)
                self.copied_shapes.append(self.node_dict_copy[n_key].g_ID)
            for e_key in self.elm_dict_copy:
                x = self.elm_dict_copy[e_key].ctrX
                y = self.elm_dict_copy[e_key].ctrY
                self.elm_dict_copy[e_key].draw_elm(x, y)

                node_in = node_translation[self.elm_dict_copy[e_key].nodeIn]
                x = self.node_dict_copy[node_in].ctrX
                y = self.node_dict_copy[node_in].ctrY
                self.elm_dict_copy[e_key].nodeIn = node_in
                self.elm_dict_copy[e_key].draw_connector_in(x, y, node_in)

                node_out = node_translation[self.elm_dict_copy[e_key].nodeOut]
                x = self.node_dict_copy[node_out].ctrX
                y = self.node_dict_copy[node_out].ctrY
                self.elm_dict_copy[e_key].nodeOut = node_out
                self.elm_dict_copy[e_key].draw_connector_out(x, y, node_out)

                self.elm_dict_copy[e_key].elm_selected_color()

                self.copied_shapes.append(self.elm_dict_copy[e_key].g_ID)
                self.copied_shapes.append(self.elm_dict_copy[e_key].g_elm)
                self.copied_shapes.append(self.elm_dict_copy[e_key].g_code)
                self.copied_shapes.append(self.elm_dict_copy[e_key].g_conIn)
                self.copied_shapes.append(self.elm_dict_copy[e_key].g_conOut)
            # change back the color of the selected items
            for e in self.item_selection["elm"]:
                self.elm_dict[e].elm_unselected_color()
            for n in self.item_selection["node"]:
                self.node_dict[n].node_unselected_color()
            # clear the item selected array
            self.item_selection['node'].clear()
            self.item_selection['elm'].clear()
            # Move the center of gravity of the copy to the cursor location

            # activate bind for mouse moving
            self.xg[1] = self.xg[0]
            self.yg[1] = self.yg[0]
            # self.centralFrame.th_canvas.bind("<ButtonRelease-1>", self.paste())
            self.centralFrame.th_canvas.bind("<Motion>", lambda event: self.move_copy(event))

    def move_copy(self, event):
        dx = event.x - self.xg[1]  # + self.centralFrame.offset[0]
        dy = event.y - self.yg[1]  # + self.centralFrame.offset[1]
        for i, shape in enumerate(self.copied_shapes):
            self.centralFrame.th_canvas.move(shape, dx, dy)
        self.xg[1] = event.x
        self.yg[1] = event.y

    def paste(self):
        # the coordinates of the copied items is updated
        # the copied entities are merged in the main dictionary
        # the bind events are restored
        self.centralFrame.th_canvas.unbind("<ButtonRelease-1>")
        self.centralFrame.th_canvas.bind("<Motion>")
        delta_x = self.xg[1] - self.xg[0]
        delta_y = self.yg[1] - self.yg[0]
        for n in self.node_dict_copy:
            self.node_dict[n] = self.node_dict_copy[n]
            self.node_dict[n].ctrX += delta_x
            self.node_dict[n].ctrY += delta_y
            self.node_dict[n].node_unselected_color()
        for e in self.elm_dict_copy:
            self.elm_dict[e] = self.elm_dict_copy[e]
            self.elm_dict[e].ctrX += delta_x
            self.elm_dict[e].ctrY += delta_y
            self.elm_dict[e].elm_unselected_color()
        self.node_dict_copy.clear()
        self.elm_dict_copy.clear()
        self.centralFrame.th_canvas.unbind("<Motion>")
        self.bind_events()

    def Delete(self):
        """
        The logic is the following:
            step 1: delete all the elements in the selection.
            step 2: delete the orphan nodes (means not connected to any element). The nodes with a parent element
                    will survive, a warning message is displayed.
            step 3: re-color the survived nodes as de-selected.
        """
        nothing_to_delete = True

        if len(self.item_selection["elm"]) != 0:
            for e in self.item_selection["elm"]:
                node_in = self.elm_dict[e].nodeIn
                node_out = self.elm_dict[e].nodeOut
                self.elm_dict[e].delete_elm()
                del self.elm_dict[e]
                self.node_dict[node_in].elm_list_in.remove(e)
                self.node_dict[node_out].elm_list_out.remove(e)
            self.item_selection["elm"] = []
            nothing_to_delete = False

        if len(self.item_selection["node"]) != 0:
            # check if any element is attached to the node
            for n in self.item_selection["node"]:
                if len(self.node_dict[n].elm_list_in) == 0 and len(self.node_dict[n].elm_list_out) == 0:
                    self.node_dict[n].delete_node()
                    del self.node_dict[n]
                    self.item_selection["node"].remove(n)
            if len(self.item_selection["node"]) != 0:
                messagebox.showerror(title='Delete node', message='There are connected node in the selection!')
                for n in self.item_selection["node"]:
                    self.node_dict[n].node_unselected_color()
                    self.item_selection["node"].remove(n)
            self.item_selection["node"] = []
            nothing_to_delete = False

        if nothing_to_delete:
            messagebox.showerror(title='Delete', message='Nothing to delete!')

    def get_nodes(self):
        serialized_nodes = {}
        for key in self.node_dict.keys():
            serialized_nodes[key] = self.node_dict[key].serialize()
        return serialized_nodes

    def get_element(self):
        serialized_elm = {}
        for key in self.elm_dict.keys():
            serialized_elm[key] = self.elm_dict[key].serialize()
        return serialized_elm

    def Renumber(self):
        pass

    def setup(self):  # run first
        """Calls methods to setup the user interface."""
        self.create_widgets()
        self.setup_layout()

    def create_widgets(self):
        """Create various widgets in the tkinter main window."""
        self.main_Panned_Window = PanedWindow(self, orient=HORIZONTAL)
        self.left_Panned_Window = PanedWindow(self.main_Panned_Window, orient=VERTICAL)
        self.central_Panned_Window = PanedWindow(self.main_Panned_Window, orient=VERTICAL)
        self.right_Panned_Window = PanedWindow(self.main_Panned_Window, orient=VERTICAL)
        self.leftFrame = ThermalLibrary(self.left_Panned_Window)
        self.solution_Frame = SolverSetting(self.left_Panned_Window)
        self.centralFrame = GraphicWindow(self.central_Panned_Window)
        self.centralFrame.naming("Thermal Network Graphic Tree")
        self.bottomFrame = Terminal(self.central_Panned_Window)
        self.rightFrame = PropertyEditor(self.right_Panned_Window, self.functions_dict, self.update_item)
        self.plotFrame = FunctionPlotter(self.right_Panned_Window)
        self.slider_Frame = ScaleFrame(self.right_Panned_Window)
        self.slider_Frame.disable()
        self.bind_events()

    def setup_layout(self):
        self.main_Panned_Window.pack(fill=BOTH, expand=1)
        self.main_Panned_Window.add(self.left_Panned_Window, sticky='nw', stretch='always')
        self.left_Panned_Window.add(self.leftFrame, padx=10, sticky='nw', stretch='always', width=250)
        self.left_Panned_Window.add(self.solution_Frame, padx=10, sticky='sw', stretch='always', width=250)
        self.main_Panned_Window.add(self.central_Panned_Window, sticky='nw', stretch='always')
        self.central_Panned_Window.add(self.centralFrame, padx=10, sticky='nw', stretch='always')
        self.central_Panned_Window.add(self.bottomFrame, padx=10, sticky='nw', stretch='always')
        self.main_Panned_Window.add(self.right_Panned_Window, sticky='nw', stretch='always')
        self.right_Panned_Window.add(self.rightFrame, padx=10, sticky='nw', stretch='last', width=400)
        self.right_Panned_Window.add(self.plotFrame, padx=10, sticky='sw', stretch='last', width=400)
        self.right_Panned_Window.add(self.slider_Frame, padx=10, sticky='sw', stretch='last', width=400)

    def bind_events(self):
        self.centralFrame.bind("<Escape>", self.deselectAll)
        self.leftFrame.thermal_elm.bind("<ButtonRelease-1>", lambda event: self.create_component(event))
        self.leftFrame.thermal_elm.bind("<B1-Motion>", lambda event: self.drag_new_component(event))
        """-----------------------------------------------------------------------------------------------------"""
        # selection:
        self.centralFrame.th_canvas.bind("<Shift-ButtonRelease-1>", lambda event: self.select_item(event))
        # panning of the canvas
        self.centralFrame.th_canvas.bind("<ButtonPress-2>", self.centralFrame.move_start)
        self.centralFrame.th_canvas.bind("<B2-Motion>", self.centralFrame.move_move)
        # self.centralFrame.th_canvas.bind("<ButtonRelease-2>", self.pan_update)
        self.centralFrame.th_canvas.bind("<ButtonRelease-2>", self.centralFrame.offset_calc)
        # self.centralFrame.th_canvas.bind("<MouseWheel>", lambda e: self.centralFrame.zoom(e))
        self.centralFrame.th_canvas.bind("<MouseWheel>", lambda e: self.zoom(e))
        self.centralFrame.th_canvas.bind("<ButtonRelease-3>", lambda event: self.right_menu_popup(event))
        """-----------------------------------------------------------------------------------------------------"""
        self.centralFrame.th_canvas.tag_bind("drag", "<B1-Motion>", lambda event: self.drag_component(event))
        self.centralFrame.th_canvas.tag_bind("drag", "<ButtonRelease-1>", lambda event: self.reconnect_elm(event))
        """-----------------------------------------------------------------------------------------------------"""
        self.slider_Frame.scale.bind("<B1-Motion>", self.slide_solution)

    def unbind_events(self):
        self.leftFrame.thermal_elm.unbind("<ButtonRelease-1>")
        self.leftFrame.thermal_elm.unbind("<B1-Motion>")
        self.centralFrame.th_canvas.tag_unbind("drag", "<B1-Motion>")
        self.centralFrame.th_canvas.tag_unbind("drag", "<ButtonRelease-1>")
        self.centralFrame.th_canvas.unbind("<Shift-ButtonRelease-1>")

    def create_component(self, event):
        """Create a node or an element in the graphic window."""
        self.item_code = self.leftFrame.get_thermal_elm()
        self.container.configure(cursor="arrow")
        graph, offset = self.graph_area()
        # check if the button is released in the graphical area, if so release the graphic element
        if graph[0] <= event.x + offset[0] <= graph[1] and graph[2] <= event.y + offset[1] <= graph[3]:
            # create a new component
            # create a node
            if self.item_code[0] in ["Internal Node", "Temperature", "Heat Flux", "Volumetric heat source",
                                     "Total Heat source", "Thermostatic heat source"]:
                # check if it is the dictionary is empty
                if not bool(self.node_dict):
                    nodeID: int = 1
                else:
                    nodeID = int(list(self.node_dict.keys())[-1]) + 1
                # get the offset including the panning
                tot_offset = [offset[0] + self.centralFrame.offset[0], offset[1] + self.centralFrame.offset[1]]
                self.node_dict[nodeID] = ThermalNode(self.centralFrame.th_canvas, nodeID, self.item_code[0])
                self.node_dict[nodeID].draw_node(event.x + tot_offset[0] - graph[0],
                                                 event.y + tot_offset[1] - graph[2] - 15)
            # create a thermal element
            else:
                if not bool(self.elm_dict):
                    elmID = 1
                else:
                    elmID = list(self.elm_dict.keys())[-1] + 1

                if ((self.item_code[-1] == "Conduction" or self.item_code[-1] == "Convection"
                     or self.item_code[-1] == "Radiation" or self.item_code[-1] == "Advection")
                        and self.leftFrame.is_leaf()):

                    self.elm_dict[elmID] = ThermalElm(self.centralFrame.th_canvas, elmID, self.item_code[-1],
                                                      self.item_code[0])
                    tot_offset = [offset[0] + self.centralFrame.offset[0], offset[1] + self.centralFrame.offset[1]]
                    self.elm_dict[elmID].draw_elm(event.x + tot_offset[0] - graph[0],
                                                  event.y + tot_offset[1] - graph[2] - 15)
                    """Unbind all the other events on the window"""
                    self.leftFrame.thermal_elm.unbind("<ButtonRelease-1>")
                    self.leftFrame.thermal_elm.unbind("<B1-Motion>")
                    # self.centralFrame.th_canvas.tag_unbind("drag", "<B1-Motion>")
                    """Force the connection of the entrance and the exit of the element"""
                    self.selected_elm = elmID
                    self.start_vector = [self.elm_dict[self.selected_elm].ctrX,
                                         self.elm_dict[self.selected_elm].ctrY]
                    self.follow_line = True
                    self.centralFrame.th_canvas.tag_bind("drag", "<ButtonRelease-1>", lambda e: self.connect_node(e))
                    self.centralFrame.th_canvas.bind("<Motion>", lambda e: self.on_move(e))
                else:
                    elmID = elmID - 1
                    pass
        else:
            pass

    def load_node(self, node):
        """Create a node in the graphic window from the loaded file."""
        self.node_dict[node["ID"]] = ThermalNode(self.centralFrame.th_canvas, node["ID"], node["type"])
        self.node_dict[node["ID"]].node_type = node["type"]
        self.node_dict[node["ID"]].node_label = node["label"]
        self.node_dict[node["ID"]].node_comment = node["comment"]
        self.node_dict[node["ID"]].node_material = node["material"]
        self.node_dict[node["ID"]].node_volume = node["volume"]
        self.node_dict[node["ID"]].node_density = node["density"]
        self.node_dict[node["ID"]].node_Cp = node["specific Heat"]
        self.node_dict[node["ID"]].node_area = node["area"]
        self.node_dict[node["ID"]].node_temperature = node["temperature"]
        self.node_dict[node["ID"]].node_heat_flux = node["heat flux"]
        self.node_dict[node["ID"]].node_volumetric_power = node["volumetric power"]
        self.node_dict[node["ID"]].node_power = node["power"]
        self.node_dict[node["ID"]].node_thermostatic_node = node["thermostatic node id"]
        self.node_dict[node["ID"]].node_temp_on = node["temperature on"]
        self.node_dict[node["ID"]].node_temp_off = node["temperature off"]
        if 'solution' in node:
            self.node_dict[node["ID"]].node_solution = node["solution"]
        else:
            self.node_dict[node["ID"]].node_solution = None
        if 'time function' in node:
            self.node_dict[node["ID"]].node_fn_time = node['time function']
        else:
            self.node_dict[node["ID"]].node_solution = 'const'

        self.node_dict[node["ID"]].elm_list_in = node["inlet element list"]
        self.node_dict[node["ID"]].elm_list_out = node["exit element list"]

        if self.node_dict[node["ID"]].node_solution is None:
            self.node_dict[node["ID"]].draw_node(node["center X"], node["center Y"])
        else:
            analysis = self.solution_Frame.get_analysis_setup()
            if analysis.type == 'Steady State':
                self.node_dict[node["ID"]].draw_node(node["center X"], node["center Y"], analysis.begin_time)
            else:
                self.node_dict[node["ID"]].draw_node(node["center X"], node["center Y"], analysis.end_time)

    def load_element(self, elm):
        """Load an element in the graphic window and connect it."""
        elmID = elm["ID"]
        self.elm_dict[elmID] = ThermalElm(self.centralFrame.th_canvas, elmID, elm["type"], elm["subtype"])
        self.elm_dict[elmID].label = elm["label"]
        self.elm_dict[elmID].comment = elm["comment"]
        self.elm_dict[elmID].material = elm["material"]
        self.elm_dict[elmID].area = elm["area"]
        self.elm_dict[elmID].thermal_conductivity = elm["thermal conductivity"]
        self.elm_dict[elmID].velocity = elm["velocity"]
        self.elm_dict[elmID].characteristic_length = elm["characteristic length"]
        self.elm_dict[elmID].angle_theta = elm["angle theta"]
        self.elm_dict[elmID].radius = elm["radius"]
        self.elm_dict[elmID].inner_radius = elm["inner radius"]
        self.elm_dict[elmID].outer_radius = elm["outer radius"]
        self.elm_dict[elmID].height = elm["height"]
        self.elm_dict[elmID].width = elm["width"]
        self.elm_dict[elmID].convection_htc = elm["convection htc"]
        self.elm_dict[elmID].x_begin = elm["x begin"]
        self.elm_dict[elmID].x_end = elm["x end"]
        self.elm_dict[elmID].emissivity = elm["emissivity"]
        self.elm_dict[elmID].exchange_factor_12 = elm["exchange factor 12"]
        self.elm_dict[elmID].exchange_factor_21 = elm["exchange factor 21"]
        self.elm_dict[elmID].nodeIn = elm["inlet node id"]
        self.elm_dict[elmID].nodeOut = elm["exit node id"]

        if 'solution' in elm:
            self.elm_dict[elmID].solution = elm["solution"]
        else:
            self.elm_dict[elmID].solution = None

        if self.elm_dict[elmID].solution is None:
            self.elm_dict[elmID].draw_elm(elm["center X"], elm["center Y"])
        else:
            analysis = self.solution_Frame.get_analysis_setup()
            if analysis.type == 'Steady State':
                self.elm_dict[elmID].draw_elm(elm["center X"], elm["center Y"], analysis.begin_time)
            else:
                self.elm_dict[elmID].draw_elm(elm["center X"], elm["center Y"], analysis.end_time)

        x = self.node_dict[self.elm_dict[elmID].nodeIn].ctrX
        y = self.node_dict[self.elm_dict[elmID].nodeIn].ctrY
        self.elm_dict[elmID].draw_connector_in(x, y, elm["inlet node id"])

        x = self.node_dict[self.elm_dict[elmID].nodeOut].ctrX
        y = self.node_dict[self.elm_dict[elmID].nodeOut].ctrY
        self.elm_dict[elmID].draw_connector_out(x, y, elm["exit node id"])

    def update_item(self, var_name, index, mode):
        """something is changed in the property editor, the dictionary of the nodes or the elements must be updated
           with the user value data"""
        item = self.rightFrame.property_tree.item(0).get("text")
        if item == "Node ID":
            node = self.rightFrame.get_info()
            self.node_dict[node.node_ID] = node
        elif item == "element ID":
            element = self.rightFrame.get_info()
            self.elm_dict[element.elmID] = element
        else:
            pass

    def connect_node(self, event):
        clicked_id = event.widget.find_withtag('current')[0]
        if event.widget.gettags(clicked_id)[1] == "node" and self.selected_elm:
            self.selected_node = int(event.widget.gettags(clicked_id)[2])
            self.centralFrame.th_canvas.delete('connection_line')
            x = self.node_dict[self.selected_node].ctrX
            y = self.node_dict[self.selected_node].ctrY
            """ Check if it is a new element"""
            if self.elm_dict[self.selected_elm].nodeIn is None and self.elm_dict[self.selected_elm].nodeOut is None:
                self.elm_dict[self.selected_elm].draw_connector_in(x, y, self.selected_node)
                self.node_dict[self.selected_node].elm_list_in.append(self.selected_elm)
                self.selected_node = None
                """ Check if it is an element inlet reconnection """
            elif self.elm_dict[self.selected_elm].nodeIn is None:
                """ Check if we try to connect the inlet and exit to the same node"""
                if self.elm_dict[self.selected_elm].nodeOut != self.selected_node:
                    self.elm_dict[self.selected_elm].draw_connector_in(x, y, self.selected_node)
                    self.node_dict[self.selected_node].elm_list_in.append(self.selected_elm)
                    self.follow_line = False
                    self.selected_elm = None
                    self.selected_node = None
                    self.centralFrame.th_canvas.unbind("<Motion>")
                    self.centralFrame.th_canvas.tag_unbind("drag", "<ButtonRelease-1>")
                    self.bind_events()
                else:
                    self.selected_node = None
            elif self.elm_dict[self.selected_elm].nodeOut is None:
                """ check if it is an attempt to connect the element inlet and exit to the same node"""
                if self.elm_dict[self.selected_elm].nodeIn != self.selected_node:
                    self.elm_dict[self.selected_elm].draw_connector_out(x, y, self.selected_node)
                    self.node_dict[int(self.selected_node)].elm_list_out.append(self.selected_elm)
                    self.follow_line = False
                    self.selected_elm = None
                    self.selected_node = None
                    self.centralFrame.th_canvas.unbind("<Motion>")
                    self.centralFrame.th_canvas.tag_unbind("drag", "<ButtonRelease-1>")
                    self.bind_events()
                else:
                    self.selected_node = None
            else:
                pass
        else:
            pass

    def drag_new_component(self, event):
        """Drag a node or an element from the TreeView into the graphic window."""
        # Check if outside canvas area
        graph, offset = self.graph_area()
        if (event.x + offset[0] < graph[0] or event.x + offset[0] > graph[1] or
                event.y + offset[1] < graph[2] or event.y + offset[1] > graph[3]):
            self.container.configure(cursor="no")
        else:
            self.container.configure(cursor="arrow")

    def drag_component(self, event):
        """Drag a node or an element in the graphic window."""
        # Check if outside canvas area
        graph, _ = self.graph_area()
        if (event.x + graph[0] < graph[0] or event.x + graph[0] > graph[1] or
                event.y + graph[2] < graph[2] or event.y + graph[2] > graph[3]):
            self.container.configure(cursor="no")
        else:
            self.container.configure(cursor="arrow")

        offset = [self.centralFrame.offset[0], self.centralFrame.offset[1]]
        x = event.x + offset[0]
        y = event.y + offset[1]
        if event.widget.find_withtag('current'):
            clicked_id = event.widget.find_withtag('current')[0]
            if event.widget.gettags(clicked_id)[1] == "node":
                nodeID = int(event.widget.gettags(clicked_id)[2])
                self.node_dict[nodeID].move_node(x, y)
                for elm in self.node_dict[nodeID].elm_list_in:
                    self.elm_dict[int(elm)].update_g_conIn(x, y)
                for elm in self.node_dict[nodeID].elm_list_out:
                    self.elm_dict[int(elm)].update_g_conOut(x, y)
            elif event.widget.gettags(clicked_id)[1] == "elm":
                elmID = int(event.widget.gettags(clicked_id)[2])
                self.elm_dict[elmID].move_elm(x, y)
        else:
            pass

    def graph_area(self):
        # graph = [X0, X_end, Y0, Y_end]
        graph = [self.centralFrame.th_canvas.winfo_rootx(), self.centralFrame.th_canvas.winfo_rootx() +
                 self.centralFrame.th_canvas.winfo_width(), self.centralFrame.winfo_rooty() + 15,
                 self.centralFrame.th_canvas.winfo_rooty() + 15 + self.centralFrame.th_canvas.winfo_height()]
        offset = [self.leftFrame.thermal_elm.winfo_rootx(), self.leftFrame.thermal_elm.winfo_rooty()]
        return graph, offset

    def on_move(self, event):
        # the function draws a line from the element body to the cursor until a node is selected
        if self.selected_elm is not None and self.follow_line:
            offset = [self.centralFrame.offset[0], self.centralFrame.offset[1]]
            self.draw_line(self.start_vector[0], self.start_vector[1], event.x + offset[0], event.y + offset[1])

    def reconnect_elm(self, event):
        # dividere gli eventi in modo più razionale
        # - connettori --> riconnessione
        # - nodi o elementi --> aggiornamento dati da soluzione
        clicked_id = event.widget.find_withtag('current')[0]
        if event.widget.gettags(clicked_id)[1] == "connector_in":
            self.selected_elm = int(event.widget.gettags(clicked_id)[2])
            self.unbind_events()
            node_in = int(self.elm_dict[self.selected_elm].nodeIn)
            self.node_dict[node_in].elm_list_in.remove(self.selected_elm)
            self.elm_dict[self.selected_elm].g_conIn = None
            self.elm_dict[self.selected_elm].nodeIn = None
            self.start_vector = [self.elm_dict[self.selected_elm].ctrX, self.elm_dict[self.selected_elm].ctrY]
            self.centralFrame.th_canvas.delete(clicked_id)
            self.follow_line = True
            self.centralFrame.th_canvas.bind("<Motion>", lambda e: self.on_move(e))
            self.centralFrame.th_canvas.tag_bind("drag", "<ButtonRelease-1>", lambda e: self.connect_node(e))
        elif event.widget.gettags(clicked_id)[1] == "connector_out":
            self.selected_elm = int(event.widget.gettags(clicked_id)[2])
            self.unbind_events()
            node_out = self.elm_dict[self.selected_elm].nodeOut
            if self.selected_elm in self.node_dict[int(node_out)].elm_list_out:
                self.node_dict[int(node_out)].elm_list_out.remove(self.selected_elm)
            else:
                print('The element ' + str(self.selected_elm) + ' does not exist in the list of the node connections')
            self.elm_dict[self.selected_elm].g_conOut = None
            self.elm_dict[self.selected_elm].nodeOut = None
            self.start_vector = [self.elm_dict[self.selected_elm].ctrX, self.elm_dict[self.selected_elm].ctrY]
            self.centralFrame.th_canvas.delete(clicked_id)
            self.follow_line = True
            self.centralFrame.th_canvas.bind("<Motion>", lambda e: self.on_move(e))
            self.centralFrame.th_canvas.tag_bind("drag", "<ButtonRelease-1>", lambda e: self.connect_node(e))
        elif event.widget.gettags(clicked_id)[1] == "node" and not self.follow_line:
            self.selected_node = int(event.widget.gettags(clicked_id)[2])
            self.rightFrame.edit_node(self.node_dict[self.selected_node])
            solution = self.node_dict[self.selected_node].node_solution
            if solution is not None:
                if len(solution) > 2:
                    node_id = self.node_dict[self.selected_node].node_ID
                    self.plotFrame.plot_function(solution, 'node', node_id)
        elif event.widget.gettags(clicked_id)[1] == "elm" and not self.follow_line:
            self.selected_elm = int(event.widget.gettags(clicked_id)[2])
            # self.elm_dict[self.selected_elm].elm_selected_color()
            self.rightFrame.edit_elm(self.elm_dict[self.selected_elm])
            solution = self.elm_dict[self.selected_elm].solution
            if solution is not None:
                if len(solution) > 2:
                    elm_id = self.elm_dict[self.selected_elm].elmID
                    self.plotFrame.plot_function(solution, 'element', elm_id)
        else:
            pass

    def draw_line(self, x1, y1, x2, y2):
        self.centralFrame.th_canvas.delete('connection_line')  # Delete previous line before drawing a new one
        self.centralFrame.th_canvas.create_line(x1, y1, x2, y2, fill="red", tag="connection_line")
        self.centralFrame.th_canvas.tag_lower("connection_line")

    def network_reset(self):
        # reset the database and clear the screen
        self.centralFrame.th_canvas.delete("all")
        self.node_dict = {}
        self.elm_dict = {}

    def get_analysis_setup(self):
        self.solution_Frame.get_analysis_setup()

    def select_item(self, event):
        """
        it is possible to select multiple elements and nodes.
        re-clicking an item it will be removed from the dictionary.
        """
        clicked_id = event.widget.find_withtag('current')[0]
        if event.widget.gettags(clicked_id)[1] == "node":
            node = int(event.widget.gettags(clicked_id)[2])
            if node in self.item_selection["node"]:
                self.node_dict[node].node_unselected_color()
                self.item_selection["node"].remove(node)
            else:
                self.node_dict[node].node_selected_color()
                self.item_selection["node"].append(node)
        elif event.widget.gettags(clicked_id)[1] == "elm":
            element = int(event.widget.gettags(clicked_id)[2])
            if element in self.item_selection["elm"]:
                self.elm_dict[element].elm_unselected_color()
                self.item_selection["elm"].remove(element)
            else:
                self.elm_dict[element].elm_selected_color()
                self.item_selection["elm"].append(element)
        else:
            pass

    def import_solution(self, T, Q, nodes, elements, spar):
        is_steady = spar.steady
        if is_steady:
            self.slider_Frame.disable()
            time = spar.begin_time
            for index, node in enumerate(nodes):
                self.node_dict[int(node.label)].node_solution = np.zeros((1, 2))  # Reset the data contained
                self.node_dict[int(node.label)].node_solution = [time, T[index]]
                x = self.node_dict[int(node.label)].ctrX
                y = self.node_dict[int(node.label)].ctrY
                self.node_dict[int(node.label)].draw_node(x, y, time)
            for index, element in enumerate(elements):
                self.elm_dict[int(element.label)].solution = np.zeros((1, 2))  # Reset the data contained
                self.elm_dict[int(element.label)].solution = [time, Q[index]]
                x = self.elm_dict[int(element.label)].ctrX
                y = self.elm_dict[int(element.label)].ctrY
                self.elm_dict[int(element.label)].draw_elm(x, y, time)
        else:
            self.slider_Frame.enable()
            from_ = spar.begin_time
            to_ = spar.end_time

            if spar.time_step == spar.time_step:  # Check if the time step != NaN (NaN == NaN = False)
                spar.number_time_steps = int((spar.end_time - spar.begin_time) / spar.time_step)
            elif spar.number_time_steps == spar.number_time_steps:  # Check if number_time_steps != NaN
                spar.number_time_steps = int(spar.number_time_steps)
            else:
                self.bottomFrame.write_text('ERROR: the time step or the time steps are not defined!\n')
            steps = spar.number_time_steps
            time = spar.end_time
            self.slider_Frame.scale_configure([from_, to_, steps, time])
            time = spar.end_time
            for index, node in enumerate(nodes):
                shape = np.shape(T)[0]
                self.node_dict[int(node.label)].node_solution = np.zeros((shape, 2))  # Reset the data contained
                self.node_dict[int(node.label)].node_solution = T[:, [0, index+1]]
                x = self.node_dict[int(node.label)].ctrX
                y = self.node_dict[int(node.label)].ctrY
                self.node_dict[int(node.label)].draw_node(x, y, time)
            for index, element in enumerate(elements):
                shape = np.shape(Q)[0]
                self.elm_dict[int(element.label)].solution = np.zeros((shape, 2))  # Reset the data contained
                self.elm_dict[int(element.label)].solution = Q[:, [0, index+1]]
                x = self.elm_dict[int(element.label)].ctrX
                y = self.elm_dict[int(element.label)].ctrY
                self.elm_dict[int(element.label)].draw_elm(x, y, time)
            # check if a graph is present and refresh
            item = self.rightFrame.property_tree.item(0).get("text")
            if item == "Node ID":
                node = self.rightFrame.get_info()
                solution = self.node_dict[node.node_ID].node_solution
                self.plotFrame.plot_function(solution, 'node', node.node_ID)
                self.slide_solution(self)
            elif item == "element ID":
                element = self.rightFrame.get_info()
                solution = self.elm_dict[element.elmID].solution
                self.plotFrame.plot_function(solution, 'element', element.elmID)
                self.slide_solution(self)
            else:
                pass

    def slide_solution(self, event):
        # update the displayed solution according to the slider position
        if self.slider_Frame.scale_active:
            time = self.slider_Frame.get_value()
            for key in self.node_dict:
                self.node_dict[key].update_solution(time)
            for key in self.elm_dict:
                self.elm_dict[key].update_solution(time)
            self.plotFrame.add_vertical_line(time)

    def zoom(self, event):
        zoom_factor = self.centralFrame.zoom(event)
        for nodeID in self.node_dict.keys():
            self.node_dict[nodeID].ctrX *= zoom_factor
            self.node_dict[nodeID].ctrY *= zoom_factor

        for elm_ID in self.elm_dict.keys():
            self.elm_dict[elm_ID].ctrX *= zoom_factor
            self.elm_dict[elm_ID].ctrY *= zoom_factor

    def update_functions(self):
        self.bottomFrame.write_text('The dictionary of the time functions has been just updated!\n')
        pass


# ---------------------------------------------------------------------------------------------------------------------


if __name__ == '__main__':
    win = Tk()
    win.title('Test of Thermal Network GUI')
    # win.state("zoomed")
    thermal_net_tab = ThermalNetwork(win)
    thermal_net_tab.pack()

    win.mainloop()
