from tkinter import Tk, LabelFrame, Frame, END, Button, Entry, BooleanVar, StringVar
from tkinter.ttk import Treeview, OptionMenu
from thermal_node import ThermalNode
from thermal_element import ThermalElm
from gUtility import material_list, fluid_list, node_type, elm_type, angle_units, htc_unit
from gUtility import length_units_SI, area_unit_SI, volume_unit_SI, density_unit_SI, specific_heat_unit, velocity_unit
from gUtility import temperature_unit, heat_flux_unit, volumetric_power_unit, power_unit, thermal_conductivity_unit
from pint import UnitRegistry

"""
    Thermal Solver Network - Property editor
    This class manages the editing of teh properties of nodes and elements

    Luca Lombardi
    Rev 0: First Draft
    
    To Do:
    ...
    ...    
"""


class PropertyEditor(Frame):
    def __init__(self, parent, change_callback):
        Frame.__init__(self, parent)

        self.change_released = BooleanVar(value=False)

        self._frame_prop_edit = LabelFrame(self, text="Property Editor", height=450, width=2000, padx=10, pady=10)
        self._frame_prop_edit.pack(side='left', pady=10, expand=1, fill='x', anchor='n')
        """ dummy items to contain the data """
        self.dummy_node = ThermalNode
        self.dummy_elm = ThermalElm
        """ TreeView of items """
        self.property_tree = Treeview(self._frame_prop_edit, height=20)
        self.property_tree['columns'] = ["value", "units"]
        self.property_tree.column("#0", width=150)
        self.property_tree.column("value", width=120)
        self.property_tree.column("units", width=60)
        self.property_tree.heading("#0", text="Name")
        self.property_tree.heading("value", text="Value")
        self.property_tree.heading("units", text="Unit")
        # -------------------------------------------
        # self.property_tree.grid(row=0, column=0, sticky="w")
        self.property_tree.pack(side='left', padx=5, pady=10, expand=1, fill='x', anchor='n')

        self.property_tree.bind("<Double-1>", self.on_double_click)

        self.change_released.trace_add("write", change_callback)

    def on_double_click(self, event):
        # modify the data
        region_clicked = self.property_tree.identify_region(event.x, event.y)
        if region_clicked not in ("tree", "cell"):
            return

        material_selected = StringVar()
        unit_selected = StringVar()
        type_selected = StringVar()

        selected_column = self.property_tree.identify_column(event.x)
        selected_column = int(selected_column[1:]) - 1

        if selected_column == -1:
            return

        item_type = self.property_tree.item(1)

        if item_type.get('text') == 'Node type':
            selected_iid = self.property_tree.focus()
            selected_values = self.property_tree.item(selected_iid)
            selected_text = selected_values.get("values")[selected_column]
            selected_box = self.property_tree.bbox(selected_iid, selected_column)
            if selected_column == 0:
                if selected_iid == '1':
                    self.change_node_type = OptionMenu(self._frame_prop_edit,
                                                       type_selected,
                                                       selected_text,
                                                       *node_type,
                                                       command=lambda m: self._set_node_type(m, selected_iid))
                    self.change_node_type.place(x=selected_box[0],
                                                y=selected_box[1] + 10,
                                                w=selected_box[2],
                                                h=selected_box[3])
                    self.change_node_type.focus()
                    self.change_node_type.bind("<FocusOut>", self.box_focus_out)
                elif selected_iid == '3':
                    # comment entry
                    entry_box = Entry(self._frame_prop_edit, width=selected_box[2])
                    entry_box.place(x=selected_box[0],
                                    y=selected_box[1] + 10,
                                    w=selected_box[2],
                                    h=selected_box[3])
                    entry_box.insert(0, selected_text)
                    entry_box.select_range(0, END)
                    entry_box.focus()
                    entry_box.bind("<FocusOut>", self.box_focus_out)
                    entry_box.bind("<Return>", lambda e: self.on_enter_press(e, selected_iid, selected_column))
                elif selected_iid == '4':
                    # the cell for material has been selected
                    self.material_option = OptionMenu(self._frame_prop_edit,
                                                      material_selected,
                                                      selected_text,
                                                      *material_list,
                                                      command=lambda m: self._set_material(m, selected_iid))
                    # remember to add the pady or padx in case of modifications in the placement of the
                    # _frame_prop_edit frame. place do not consider this from the pack method.
                    self.material_option.place(x=selected_box[0],
                                               y=selected_box[1] + 10,
                                               w=selected_box[2],
                                               h=selected_box[3])
                    self.material_option.focus()
                    self.material_option.bind("<FocusOut>", self.box_focus_out)
                elif selected_iid == '5':
                    # Volume entry
                    entry_box = Entry(self._frame_prop_edit, width=selected_box[2], validate="key",
                                      validatecommand=(self.register(self.validate_real_number), "%P"))
                    entry_box.place(x=selected_box[0],
                                    y=selected_box[1] + 10,
                                    w=selected_box[2],
                                    h=selected_box[3])
                    entry_box.insert(0, selected_text)
                    entry_box.select_range(0, END)
                    entry_box.focus()
                    entry_box.bind("<FocusOut>", self.box_focus_out)
                    entry_box.bind("<Return>", lambda e: self.on_enter_press(e, selected_iid, selected_column))
                elif selected_iid == '13':
                    # thermostatic node - the only one with an integer entry
                    entry_box = Entry(self._frame_prop_edit, width=selected_box[2], validate="key",
                                      validatecommand=(self.register(self.validate_integer_number), "%P"))
                    entry_box.place(x=selected_box[0],
                                    y=selected_box[1] + 10,
                                    w=selected_box[2],
                                    h=selected_box[3])
                    entry_box.insert(0, selected_text)
                    entry_box.select_range(0, END)
                    entry_box.focus()
                    entry_box.bind("<FocusOut>", self.box_focus_out)
                    entry_box.bind("<Return>", lambda e: self.on_enter_press(e, selected_iid, selected_column))
                elif (int(selected_iid) > 4) and ('enabled' in self.property_tree.item(selected_iid)['tags']):
                    entry_box = Entry(self._frame_prop_edit, width=selected_box[2], validate="key",
                                      validatecommand=(self.register(self.validate_real_number), "%P"))
                    entry_box.place(x=selected_box[0],
                                    y=selected_box[1] + 10,
                                    w=selected_box[2],
                                    h=selected_box[3])
                    entry_box.insert(0, selected_text)
                    entry_box.select_range(0, END)
                    entry_box.focus()
                    entry_box.bind("<FocusOut>", self.box_focus_out)
                    entry_box.bind("<Return>", lambda e: self.on_enter_press(e, selected_iid, selected_column))
            elif (selected_column == 1) and (int(selected_iid) > 4):
                # units column
                if 'enabled' in self.property_tree.item(selected_iid)['tags']:
                    if selected_iid == '5':
                        # Volume units
                        self.unit_option = OptionMenu(self._frame_prop_edit,
                                                      unit_selected,
                                                      selected_text,
                                                      *volume_unit_SI[0],
                                                      command=lambda m: self._set_unit(m, volume_unit_SI, selected_iid))
                    elif selected_iid == '6':
                        # density units
                        self.unit_option = OptionMenu(self._frame_prop_edit,
                                                      unit_selected,
                                                      selected_text,
                                                      *density_unit_SI[0],
                                                      command=lambda m: self._set_unit(m, density_unit_SI,
                                                                                       selected_iid))
                    elif selected_iid == '7':
                        # Specific heat units
                        self.unit_option = OptionMenu(self._frame_prop_edit,
                                                      unit_selected,
                                                      selected_text,
                                                      *specific_heat_unit[0],
                                                      command=lambda m: self._set_unit(m, specific_heat_unit,
                                                                                       selected_iid))
                    elif selected_iid == '8':
                        # Area units
                        self.unit_option = OptionMenu(self._frame_prop_edit,
                                                      unit_selected,
                                                      selected_text,
                                                      *area_unit_SI[0],
                                                      command=lambda m: self._set_unit(m, area_unit_SI,
                                                                                       selected_iid))
                    elif selected_iid in ['9', '14', '15']:
                        # Temperature units
                        self.unit_option = OptionMenu(self._frame_prop_edit,
                                                      unit_selected,
                                                      selected_text,
                                                      *temperature_unit[0],
                                                      command=lambda m: self._set_unit(m, temperature_unit,
                                                                                       selected_iid))
                    elif selected_iid == '10':
                        # Heat flux units
                        self.unit_option = OptionMenu(self._frame_prop_edit,
                                                      unit_selected,
                                                      selected_text,
                                                      *heat_flux_unit[0],
                                                      command=lambda m: self._set_unit(m, heat_flux_unit,
                                                                                       selected_iid))
                    elif selected_iid == '11':
                        # Volumetric power units
                        self.unit_option = OptionMenu(self._frame_prop_edit,
                                                      unit_selected,
                                                      selected_text,
                                                      *volumetric_power_unit[0],
                                                      command=lambda m: self._set_unit(m, volumetric_power_unit,
                                                                                       selected_iid))
                    elif selected_iid == '12':
                        # Power units
                        self.unit_option = OptionMenu(self._frame_prop_edit,
                                                      unit_selected,
                                                      selected_text,
                                                      *power_unit[0],
                                                      command=lambda m: self._set_unit(m, power_unit,
                                                                                       selected_iid))

                    # remember to add the pady or padx in case of modifications in the placement of the
                    # _frame_prop_edit frame. place do not consider this from the pack method.
                    self.unit_option.place(x=selected_box[0],
                                           y=selected_box[1] + 10,
                                           w=selected_box[2],
                                           h=selected_box[3])
                    self.unit_option.focus()
                    self.unit_option.bind("<FocusOut>", self.box_focus_out)
                else:
                    pass
            else:
                pass
        elif item_type.get('text') == 'Element Type':
            selected_iid = self.property_tree.focus()
            selected_values = self.property_tree.item(selected_iid)
            selected_text = selected_values.get("values")[selected_column]
            selected_box = self.property_tree.bbox(selected_iid, selected_column)
            if selected_column == 0:
                if selected_iid == '1':
                    # change the element type
                    type_list = list(elm_type.keys())
                    self.change_elm_type = OptionMenu(self._frame_prop_edit,
                                                      type_selected,
                                                      selected_text,
                                                      *type_list,
                                                      command=lambda m: self._set_elm_type(m, selected_iid))
                    self.change_elm_type.place(x=selected_box[0],
                                               y=selected_box[1] + 10,
                                               w=selected_box[2],
                                               h=selected_box[3])
                    self.change_elm_type.focus()
                    self.change_elm_type.bind("<FocusOut>", self.box_focus_out)
                if selected_iid == '2':
                    # change the element subtype
                    key = self.property_tree.item(1)['values'][0]
                    subtype_list = elm_type[key]
                    self.change_elm_subtype = OptionMenu(self._frame_prop_edit,
                                                         type_selected,
                                                         selected_text,
                                                         *subtype_list,
                                                         command=lambda m: self._set_elm_subtype(m, key))
                    self.change_elm_subtype.place(x=selected_box[0],
                                                  y=selected_box[1] + 10,
                                                  w=selected_box[2],
                                                  h=selected_box[3])
                    self.change_elm_subtype.focus()
                    self.change_elm_subtype.bind("<FocusOut>", self.box_focus_out)
                elif selected_iid == '4':
                    # comment entry
                    entry_box = Entry(self._frame_prop_edit, width=selected_box[2])
                    entry_box.place(x=selected_box[0],
                                    y=selected_box[1] + 10,
                                    w=selected_box[2],
                                    h=selected_box[3])
                    entry_box.insert(0, selected_text)
                    entry_box.select_range(0, END)
                    entry_box.focus()
                    entry_box.bind("<FocusOut>", self.box_focus_out)
                    entry_box.bind("<Return>", lambda e: self.on_enter_press(e, selected_iid, selected_column))
                elif selected_iid == '5':
                    # the cell for material has been selected
                    if item_type.get('values')[0] == 'Conduction':
                        _material_list = material_list
                    else:
                        _material_list = fluid_list
                    self.material_option = OptionMenu(self._frame_prop_edit,
                                                      material_selected,
                                                      selected_text,
                                                      *_material_list,
                                                      command=lambda m: self._set_material(m, selected_iid))
                    # remember to add the pady or padx in case of modifications in the placement of the
                    # _frame_prop_edit frame. place do not consider this from the pack method.
                    self.material_option.place(x=selected_box[0],
                                               y=selected_box[1] + 10,
                                               w=selected_box[2],
                                               h=selected_box[3])
                    self.material_option.focus()
                    self.material_option.bind("<FocusOut>", self.box_focus_out)
                elif (int(selected_iid) > 5) and ('enabled' in self.property_tree.item(selected_iid)['tags']):
                    entry_box = Entry(self._frame_prop_edit, width=selected_box[2], validate="key",
                                      validatecommand=(self.register(self.validate_real_number), "%P"))
                    entry_box.place(x=selected_box[0],
                                    y=selected_box[1] + 10,
                                    w=selected_box[2],
                                    h=selected_box[3])
                    entry_box.insert(0, selected_text)
                    entry_box.select_range(0, END)
                    entry_box.focus()
                    entry_box.bind("<FocusOut>", self.box_focus_out)
                    entry_box.bind("<Return>", lambda e: self.on_enter_press(e, selected_iid, selected_column))
            elif (selected_column == 1) and ((int(selected_iid) > 4) and (int(selected_iid) < 18)):
                if selected_iid == '6':
                    # Area units
                    self.unit_option = OptionMenu(self._frame_prop_edit,
                                                  unit_selected,
                                                  selected_text,
                                                  *area_unit_SI[0],
                                                  command=lambda m: self._set_unit(m, area_unit_SI,
                                                                                   selected_iid))
                elif selected_iid == '7':
                    # Thermal Conductivity units
                    self.unit_option = OptionMenu(self._frame_prop_edit,
                                                  unit_selected,
                                                  selected_text,
                                                  *thermal_conductivity_unit[0],
                                                  command=lambda m: self._set_unit(m, thermal_conductivity_unit,
                                                                                   selected_iid))
                elif selected_iid == '8':
                    # Velocity units
                    self.unit_option = OptionMenu(self._frame_prop_edit,
                                                  unit_selected,
                                                  selected_text,
                                                  *velocity_unit[0],
                                                  command=lambda m: self._set_unit(m, velocity_unit,
                                                                                   selected_iid))
                elif selected_iid in ['9', '11', '12', '13',  '14', '15', '17', '18']:
                    # characteristic length units
                    self.unit_option = OptionMenu(self._frame_prop_edit,
                                                  unit_selected,
                                                  selected_text,
                                                  *length_units_SI[0],
                                                  command=lambda m: self._set_unit(m, length_units_SI,
                                                                                   selected_iid))
                elif selected_iid == '10':
                    # angle units
                    # print(unit_selected)
                    self.unit_option = OptionMenu(self._frame_prop_edit,
                                                  unit_selected,
                                                  selected_text,
                                                  *angle_units[0],
                                                  command=lambda m: self._set_unit(m, angle_units,
                                                                                   selected_iid))
                elif selected_iid == '16':
                    # heat transfer coefficient units
                    self.unit_option = OptionMenu(self._frame_prop_edit,
                                                  unit_selected,
                                                  selected_text,
                                                  *htc_unit[0],
                                                  command=lambda m: self._set_unit(m, htc_unit,
                                                                                   selected_iid))
                else:
                    pass

                # remember to add the pady or padx in case of modifications in the placement of the
                # _frame_prop_edit frame. place do not consider this from the pack method.
                self.unit_option.place(x=selected_box[0],
                                       y=selected_box[1] + 10,
                                       w=selected_box[2],
                                       h=selected_box[3])
                self.unit_option.focus()
                self.unit_option.bind("<FocusOut>", self.box_focus_out)
        else:
            pass

    def on_enter_press(self, event, selected_iid, selected_column):
        if selected_column != -1:
            new_value = event.widget.get()
            new_values = self.property_tree.item(selected_iid).get("values")
            new_values[selected_column] = new_value
            self.property_tree.item(selected_iid, values=new_values)
            event.widget.destroy()
            """ move the results back to the global """
            self.update_properties()
        else:
            pass

    def _set_node_type(self, n_type, selected_iid):
        self.property_tree.set(selected_iid, "value", n_type)
        self.dummy_node.node_type = n_type
        self.change_node_type.destroy()
        self.edit_node(self.dummy_node)
        self.toggle_var()

    def _set_elm_type(self, n_type, selected_iid):
        self.property_tree.set(selected_iid, "value", n_type)
        self.dummy_elm.elmType = n_type
        # and reset the first element in the subtype
        if n_type != 'Convection':
            self.dummy_elm.elmSubType = elm_type[n_type][0]
        else:
            self.dummy_elm.elmSubType = elm_type[n_type][0][5:]

        self.change_elm_type.destroy()
        self.edit_elm(self.dummy_elm)
        self.toggle_var()

    def _set_elm_subtype(self, subtype, key):
        if key != 'Convection':
            self.dummy_elm.elmSubType = subtype
        else:
            self.dummy_elm.elmSubType = subtype[5:]
        self.change_elm_subtype.destroy()
        self.edit_elm(self.dummy_elm)
        self.toggle_var()

    def _set_material(self, material, selected_iid):
        self.property_tree.set(selected_iid, "value", material)
        self.material_option.destroy()
        self.update_properties()

    def _set_unit(self, to_unit, unit_table, selected_iid):
        ureg = UnitRegistry
        q_ = float(self.property_tree.item(selected_iid).get('values')[0])
        from_unit = self.property_tree.item(selected_iid).get('values')[1]
        from_index = unit_table[0].index(from_unit)
        to_index = unit_table[0].index(to_unit)

        from_magnitude = ureg.Quantity(q_, unit_table[1][from_index])
        to_magnitude = from_magnitude.to(unit_table[1][to_index])
        self.property_tree.set(selected_iid, "value", to_magnitude.magnitude)
        self.property_tree.set(selected_iid, "units", to_unit)
        self.unit_option.destroy()
        self.update_properties()

    def update_properties(self):
        item = self.property_tree.item(0).get("text")
        if item == "Node ID":
            self.update_node()
            self.toggle_var()
        elif item == "Element ID":
            print(item + ': ' + str(self.property_tree.item(0).get('values')[0]))
            self.update_element()
            self.toggle_var()
        else:
            pass

    def toggle_var(self):
        self.change_released.set(not self.change_released.get())  # Flip the boolean value

    @staticmethod
    def box_focus_out(event):
        event.widget.destroy()

    @staticmethod
    def validate_integer_number(P):
        if not P:  # Empty input is always valid
            return True
        elif P.isdigit() and int(P) >= 0:
            return True
        else:
            return False

    @staticmethod
    def validate_real_number(P):
        if not P:  # Empty input is always valid
            return True

        try:
            # Check for scientific notation format if "e" or "E" is present
            if "e" in P or "E" in P:
                parts = P.split("e") if "e" in P else P.split("E")
                if len(parts) > 2:
                    return False
                base, exponent = parts
                if not float(base):
                    return False
                if len(exponent) == 0 or (len(exponent) == 1 and exponent.startswith('-')):
                    return True
                elif not int(exponent):
                    return False
            elif len(P) == 1 and (P[0] == '-' or P[0] == '.' or P[0] == '+'):
                return True
            elif float(P) == 0:
                return True

            if not float(P):
                return False

            return True
        except ValueError:
            return False

    def edit_elm(self, elm):
        self.dummy_elm = elm
        """ remove all the items if present, clear the tree """
        if self.property_tree.get_children():
            self.property_tree.delete(*self.property_tree.get_children())
        self.property_tree.insert(parent="", index=END, iid=0, text="Element ID", values=[self.dummy_elm.elmID, ""],
                                  tags=('odd row',))
        self.property_tree.insert(parent="", index=END, iid=1, text="Element Type", values=[self.dummy_elm.elmType, ""],
                                  tags=('even row',))
        self.property_tree.insert(parent="", index=END, iid=2, text="Sub Type", values=[self.dummy_elm.elmSubType,
                                                                                        ""], tags=('odd row',))
        self.property_tree.insert(parent="", index=END, iid=3, text="label", values=[self.dummy_elm.label, ""],
                                  tags=('even row',))
        self.property_tree.insert(parent="", index=END, iid=4, text="comment", values=[self.dummy_elm.comment, ""],
                                  tags=('odd row',))
        if self.dummy_elm.elmType == "Conduction":
            if (self.dummy_elm.material == 'user defined') or (self.dummy_elm.material == ''):
                tag_state = 'enabled'
            else:
                tag_state = 'disabled'
            if self.dummy_elm.elmSubType == "Linear conduction":
                self.property_tree.insert(parent="", index=END, iid=5, text="material",
                                          values=[self.dummy_elm.material, ""], tags=('even row',))
                self.property_tree.insert(parent="", index=END, iid=6, text="area", values=self.dummy_elm.area,
                                          tags=('odd row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=7, text="thermal conductivity",
                                          values=self.dummy_elm.thermal_conductivity, tags=('even row', tag_state))
                self.property_tree.insert(parent="", index=END, iid=15, text="width",
                                          values=self.dummy_elm.width, tags=('odd row', 'enabled'))
            elif self.dummy_elm.elmSubType == "Cylindrical conduction":
                self.property_tree.insert(parent="", index=END, iid=5, text="material",
                                          values=[self.dummy_elm.material, ""], tags=('even row',))
                self.property_tree.insert(parent="", index=END, iid=7, text="thermal conductivity",
                                          values=self.dummy_elm.thermal_conductivity, tags=('odd row', tag_state))
                self.property_tree.insert(parent="", index=END, iid=12, text="inner radius",
                                          values=self.dummy_elm.inner_radius, tags=('even row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=13, text="outer radius",
                                          values=self.dummy_elm.outer_radius, tags=('odd row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=14, text="height",
                                          values=self.dummy_elm.height, tags=('even row', 'enabled'))
            elif self.dummy_elm.elmSubType == "Spherical conduction":
                self.property_tree.insert(parent="", index=END, iid=5, text="material",
                                          values=[self.dummy_elm.material, ""], tags=('even row',))
                self.property_tree.insert(parent="", index=END, iid=7, text="thermal conductivity",
                                          values=self.dummy_elm.thermal_conductivity, tags=('odd row', tag_state))
                self.property_tree.insert(parent="", index=END, iid=12, text="inner radius",
                                          values=self.dummy_elm.inner_radius, tags=('even row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=13, text="outer radius",
                                          values=self.dummy_elm.outer_radius, tags=('odd row', 'enabled'))
        elif self.dummy_elm.elmType == "Convection":
            if self.dummy_elm.elmSubType == "assigned HTC":
                self.property_tree.insert(parent="", index=END, iid=6, text="area",
                                          values=self.dummy_elm.area, tags=('even row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=16, text="convection HTC",
                                          values=self.dummy_elm.convection_htc, tags=('odd row', 'enabled'))
            elif self.dummy_elm.elmSubType == "pipe/duct":
                self.property_tree.insert(parent="", index=END, iid=5, text="material",
                                          values=[self.dummy_elm.material, ""], tags=('even row',))
                self.property_tree.insert(parent="", index=END, iid=6, text="area", values=self.dummy_elm.area,
                                          tags=('odd row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=8, text="velocity", values=self.dummy_elm.velocity,
                                          tags=('even row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=9, text="diameter",
                                          values=self.dummy_elm.characteristic_length, tags=('odd row', 'enabled'))
            elif self.dummy_elm.elmSubType == "Cylinder":
                self.property_tree.insert(parent="", index=END, iid=5, text="material",
                                          values=[self.dummy_elm.material, ""], tags=('even row',))
                self.property_tree.insert(parent="", index=END, iid=6, text="area", values=self.dummy_elm.area,
                                          tags=('odd row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=8, text="velocity", values=self.dummy_elm.velocity,
                                          tags=('even row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=9, text="diameter",
                                          values=self.dummy_elm.characteristic_length, tags=('odd row', 'enabled'))
            elif self.dummy_elm.elmSubType == "Diamond/Square":
                self.property_tree.insert(parent="", index=END, iid=5, text="material",
                                          values=[self.dummy_elm.material, ""], tags=('even row',))
                self.property_tree.insert(parent="", index=END, iid=6, text="area", values=self.dummy_elm.area,
                                          tags=('odd row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=8, text="velocity", values=self.dummy_elm.velocity,
                                          tags=('even row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=15, text="Width",
                                          values=self.dummy_elm.width, tags=('odd row', 'enabled'))
            elif self.dummy_elm.elmSubType == "Impinging Round jet":
                self.property_tree.insert(parent="", index=END, iid=5, text="material",
                                          values=[self.dummy_elm.material, ""], tags=('even row',))
                self.property_tree.insert(parent="", index=END, iid=8, text="velocity", values=self.dummy_elm.velocity,
                                          tags=('odd row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=9, text="nozzle diameter",
                                          values=self.dummy_elm.characteristic_length, tags=('odd row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=11, text="convection radius",
                                          values=self.dummy_elm.radius, tags=('even row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=14, text="plate distance",
                                          values=self.dummy_elm.height, tags=('odd row', 'enabled'))
            elif self.dummy_elm.elmSubType == "Flat Plate":
                self.property_tree.insert(parent="", index=END, iid=5, text="material",
                                          values=[self.dummy_elm.material, ""], tags=('even row',))
                self.property_tree.insert(parent="", index=END, iid=6, text="area", values=self.dummy_elm.area,
                                          tags=('odd row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=8, text="velocity", values=self.dummy_elm.velocity,
                                          tags=('even row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=17, text="X begin", values=self.dummy_elm.x_begin,
                                          tags=('odd row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=18, text="x end", values=self.dummy_elm.x_end,
                                          tags=('even row', 'enabled'))
            elif self.dummy_elm.elmSubType == "EFC Sphere":
                self.property_tree.insert(parent="", index=END, iid=5, text="material",
                                          values=[self.dummy_elm.material, ""], tags=('even row',))
                self.property_tree.insert(parent="", index=END, iid=8, text="velocity", values=self.dummy_elm.velocity,
                                          tags=('odd row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=9, text="diameter",
                                          values=self.dummy_elm.characteristic_length, tags=('even row', 'enabled'))
            elif self.dummy_elm.elmSubType == "Vertical rectangular enclosure":
                self.property_tree.insert(parent="", index=END, iid=5, text="material",
                                          values=[self.dummy_elm.material, ""], tags=('even row',))
                self.property_tree.insert(parent="", index=END, iid=6, text="area", values=self.dummy_elm.area,
                                          tags=('odd row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=14, text="height", values=self.dummy_elm.height,
                                          tags=('even row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=15, text="width", values=self.dummy_elm.width,
                                          tags=('even row', 'enabled'))
            elif self.dummy_elm.elmSubType == "ENC Horizontal cylinder":
                self.property_tree.insert(parent="", index=END, iid=5, text="material",
                                          values=[self.dummy_elm.material, ""], tags=('even row',))
                self.property_tree.insert(parent="", index=END, iid=6, text="area", values=self.dummy_elm.area,
                                          tags=('odd row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=9, text="diameter",
                                          values=self.dummy_elm.characteristic_length, tags=('even row', 'enabled'))
            elif self.dummy_elm.elmSubType == "Horizontal plate facing down":
                self.property_tree.insert(parent="", index=END, iid=5, text="material",
                                          values=[self.dummy_elm.material, ""], tags=('even row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=6, text="area", values=self.dummy_elm.area,
                                          tags=('odd row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=9, text="characteristic length",
                                          values=self.dummy_elm.characteristic_length, tags=('even row', 'enabled'))
            elif self.dummy_elm.elmSubType == "Horizontal plate facing up":
                self.property_tree.insert(parent="", index=END, iid=5, text="material",
                                          values=[self.dummy_elm.material, ""], tags=('even row',))
                self.property_tree.insert(parent="", index=END, iid=6, text="area", values=self.dummy_elm.area,
                                          tags=('odd row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=9, text="characteristic length",
                                          values=self.dummy_elm.characteristic_length, tags=('even row', 'enabled'))
            elif self.dummy_elm.elmSubType == "Inclined plate facing down":
                self.property_tree.insert(parent="", index=END, iid=5, text="material",
                                          values=[self.dummy_elm.material, ""], tags=('even row',))
                self.property_tree.insert(parent="", index=END, iid=6, text="area", values=self.dummy_elm.area,
                                          tags=('odd row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=9, text="characteristic length",
                                          values=self.dummy_elm.characteristic_length, tags=('even row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=10, text="angle theta",
                                          values=self.dummy_elm.angle_theta, tags=('odd row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=14, text="height",
                                          values=self.dummy_elm.height, tags=('even row', 'enabled'))
            elif self.dummy_elm.elmSubType == "Inclined plate facing up":
                self.property_tree.insert(parent="", index=END, iid=5, text="material",
                                          values=[self.dummy_elm.material, ""], tags=('even row',))
                self.property_tree.insert(parent="", index=END, iid=6, text="area", values=self.dummy_elm.area,
                                          tags=('odd row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=9, text="characteristic length",
                                          values=self.dummy_elm.characteristic_length, tags=('even row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=10, text="angle theta",
                                          values=self.dummy_elm.angle_theta, tags=('odd row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=14, text="height",
                                          values=self.dummy_elm.height, tags=('even row', 'enabled'))
            elif self.dummy_elm.elmSubType == "ENC Sphere":
                self.property_tree.insert(parent="", index=END, iid=5, text="material",
                                          values=[self.dummy_elm.material, ""], tags=('even row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=9, text="diameter",
                                          values=self.dummy_elm.characteristic_length, tags=('odd row', 'enabled'))
            elif self.dummy_elm.elmSubType == "Vertical flat plate":
                self.property_tree.insert(parent="", index=END, iid=5, text="material",
                                          values=[self.dummy_elm.material, ""], tags=('even row',))
                self.property_tree.insert(parent="", index=END, iid=6, text="area", values=self.dummy_elm.area,
                                          tags=('odd row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=9, text="characteristic length",
                                          values=self.dummy_elm.characteristic_length, tags=('even row', 'enabled'))
        elif self.dummy_elm.elmType == "Radiation":
            if self.dummy_elm.elmSubType == "Surface Radiation":
                self.property_tree.insert(parent="", index=END, iid=6, text="area", values=self.dummy_elm.area,
                                          tags=('even row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=19, text="emissivity",
                                          values=self.dummy_elm.emissivity, tags=('odd row', 'enabled'))
            elif self.dummy_elm.elmSubType == "Radiation":
                self.property_tree.insert(parent="", index=END, iid=6, text="area", values=self.dummy_elm.area,
                                          tags=('even row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=20, text="exchange factor 1-->2",
                                          values=self.dummy_elm.exchange_factor_12, tags=('odd row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=21, text="exchange factor 2-->1",
                                          values=self.dummy_elm.exchange_factor_21, tags=('even row', 'enabled'))
        elif self.dummy_elm.elmType == "Advection":
            if self.dummy_elm.elmSubType == "Advection":
                self.property_tree.insert(parent="", index=END, iid=5, text="material",
                                          values=[self.dummy_elm.material, ""], tags=('even row',))
                self.property_tree.insert(parent="", index=END, iid=6, text="area",
                                          values=self.dummy_elm.area, tags=('odd row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=8, text="velocity", values=self.dummy_elm.velocity,
                                          tags=('even row', 'enabled'))
            elif self.dummy_elm.elmSubType == "Outflow":
                self.property_tree.insert(parent="", index=END, iid=5, text="material",
                                          values=[self.dummy_elm.material, ""], tags=('even row',))
                self.property_tree.insert(parent="", index=END, iid=6, text="area",
                                          values=self.dummy_elm.area, tags=('odd row', 'enabled'))
                self.property_tree.insert(parent="", index=END, iid=8, text="velocity", values=self.dummy_elm.velocity,
                                          tags=('even row', 'enabled'))
        else:
            pass
        self.property_tree.tag_configure('odd row', background='white')
        self.property_tree.tag_configure('even row', background='light gray')

    def edit_node(self, node):
        self.dummy_node = node
        """ remove all the items if present, clear the tree """
        if self.property_tree.get_children():
            self.property_tree.delete(*self.property_tree.get_children())

        self.property_tree.insert(parent="", index=END, iid=0, text="Node ID", values=[self.dummy_node.node_ID, ""],
                                  tags=('odd row',))
        self.property_tree.insert(parent="", index=END, iid=1, text="Node type", values=[self.dummy_node.node_type, ""],
                                  tags=('even row',))
        self.property_tree.insert(parent="", index=END, iid=2, text="label", values=[self.dummy_node.node_label, ""],
                                  tags=('odd row',))
        self.property_tree.insert(parent="", index=END, iid=3, text="comment",
                                  values=[self.dummy_node.node_comment, ""], tags=('even row',))
        """ Differentiate the treeview on the base of the node type"""
        if self.dummy_node.node_type == "Internal Node":
            self.property_tree.insert(parent="", index=END, iid=4, text="material",
                                      values=[self.dummy_node.node_material, ""], tags=('odd row',))
            self.property_tree.insert(parent="", index=END, iid=5, text="volume", values=self.dummy_node.node_volume,
                                      tags=('even row', 'enabled'))
            if (self.dummy_node.node_material == 'user defined') or (self.dummy_node.node_material == ''):
                tag_state = 'enabled'
            else:
                tag_state = 'disabled'
            self.property_tree.insert(parent="", index=END, iid=6, text="density",
                                      values=self.dummy_node.node_density, tags=('odd row', tag_state))
            self.property_tree.insert(parent="", index=END, iid=7, text="specific heat",
                                      values=self.dummy_node.node_Cp, tags=('even row', tag_state))
        elif self.dummy_node.node_type == "Temperature":
            self.property_tree.insert(parent="", index=END, iid=9, text="temperature",
                                      values=self.dummy_node.node_temperature, tags=('odd row', 'enabled'))
        elif self.dummy_node.node_type == "Heat Flux":
            self.property_tree.insert(parent="", index=END, iid=8, text="area", values=self.dummy_node.node_area,
                                      tags=('odd row', 'enabled'))
            self.property_tree.insert(parent="", index=END, iid=10, text="heat flux",
                                      values=self.dummy_node.node_heat_flux, tags=('even row', 'enabled'))
        elif self.dummy_node.node_type == "Volumetric heat source":
            self.property_tree.insert(parent="", index=END, iid=4, text="material",
                                      values=[self.dummy_node.node_material, ""], tags=('odd row',))
            self.property_tree.insert(parent="", index=END, iid=5, text="volume", values=self.dummy_node.node_volume,
                                      tags=('even row', 'enabled'))
            if (self.dummy_node.node_material == 'user defined') or (self.dummy_node.node_material == ''):
                tag_state = 'enabled'
            else:
                tag_state = 'disabled'
            self.property_tree.insert(parent="", index=END, iid=6, text="density",
                                      values=self.dummy_node.node_density, tags=('odd row', tag_state))
            self.property_tree.insert(parent="", index=END, iid=7, text="specific heat",
                                      values=self.dummy_node.node_Cp, tags=('even row', tag_state))
            self.property_tree.insert(parent="", index=END, iid=11, text="volumetric power",
                                      values=self.dummy_node.node_volumetric_power, tags=('odd row', 'enabled'))
        elif self.dummy_node.node_type == "Total Heat source":
            self.property_tree.insert(parent="", index=END, iid=4, text="material",
                                      values=[self.dummy_node.node_material, ""], tags=('odd row',))
            self.property_tree.insert(parent="", index=END, iid=5, text="volume", values=self.dummy_node.node_volume,
                                      tags=('even row', 'enabled'))
            if (self.dummy_node.node_material == 'user defined') or (self.dummy_node.node_material == ''):
                tag_state = 'enabled'
            else:
                tag_state = 'disabled'
            self.property_tree.insert(parent="", index=END, iid=6, text="density",
                                      values=self.dummy_node.node_density, tags=('odd row', tag_state))
            self.property_tree.insert(parent="", index=END, iid=7, text="specific heat",
                                      values=self.dummy_node.node_Cp, tags=('even row', tag_state))
            self.property_tree.insert(parent="", index=END, iid=12, text="power", values=self.dummy_node.node_power,
                                      tags=('odd row', 'enabled'))
        elif self.dummy_node.node_type == "Thermostatic heat source":
            self.property_tree.insert(parent="", index=END, iid=4, text="material",
                                      values=[self.dummy_node.node_material, ""], tags=('odd row',))
            self.property_tree.insert(parent="", index=END, iid=5, text="volume", values=self.dummy_node.node_volume,
                                      tags=('even row', 'enabled'))
            if (self.dummy_node.node_material == 'user defined') or (self.dummy_node.node_material == ''):
                tag_state = 'enabled'
            else:
                tag_state = 'disabled'
            self.property_tree.insert(parent="", index=END, iid=6, text="density",
                                      values=self.dummy_node.node_density, tags=('odd row', tag_state))
            self.property_tree.insert(parent="", index=END, iid=7, text="specific heat",
                                      values=self.dummy_node.node_Cp, tags=('even row', tag_state))
            self.property_tree.insert(parent="", index=END, iid=12, text="power", values=self.dummy_node.node_power,
                                      tags=('odd row', 'enabled'))
            self.property_tree.insert(parent="", index=END, iid=13, text="thermostatic node",
                                      values=[self.dummy_node.node_thermostatic_node, ''], tags=('even row', 'enabled'))
            self.property_tree.insert(parent="", index=END, iid=14, text="Temperature ON",
                                      values=self.dummy_node.node_temp_on, tags=('odd row', 'enabled'))
            self.property_tree.insert(parent="", index=END, iid=15, text="Temperature OFF",
                                      values=self.dummy_node.node_temp_off, tags=('even row', 'enabled'))
        else:
            pass
        """ apply banded rows """
        self.property_tree.tag_configure('odd row', background='white')
        self.property_tree.tag_configure('even row', background='light gray')
        # change the text color of disabled rows
        self.property_tree.tag_configure('disabled', foreground='gray')
        self.property_tree.tag_configure('enabled', foreground='black')

    def update_node(self):
        self.dummy_node.node_type = self.property_tree.item(1).get("values")[0]
        self.dummy_node.node_label = self.property_tree.item(2).get("values")[0]
        self.dummy_node.node_comment = self.property_tree.item(3).get("values")[0]
        if self.dummy_node.node_type == "Internal Node":
            self.dummy_node.node_material = self.property_tree.item(4).get("values")[0]
            if (self.dummy_node.node_material == 'user defined') or (self.dummy_node.node_material == ''):
                tag_state = 'enabled'
            else:
                tag_state = 'disabled'
            self.dummy_node.node_volume = self.property_tree.item(5).get("values")
            self.dummy_node.node_density = self.property_tree.item(6).get("values")
            current_tags = self.property_tree.item(6)['tags']
            new_tags = (current_tags[0], tag_state)
            self.property_tree.item(6, tags=new_tags)
            self.dummy_node.node_Cp = self.property_tree.item(7).get("values")
            current_tags = self.property_tree.item(7)['tags']
            new_tags = (current_tags[0], tag_state)
            self.property_tree.item(7, tags=new_tags)
        elif self.dummy_node.node_type == "Temperature":
            self.dummy_node.node_temperature = self.property_tree.item(9).get("values")
        elif self.dummy_node.node_type == "Heat Flux":
            self.dummy_node.node_area = self.property_tree.item(8).get("values")
            self.dummy_node.node_heat_flux = self.property_tree.item(10).get("values")
        elif self.dummy_node.node_type == "Volumetric heat source":
            self.dummy_node.node_material = self.property_tree.item(4).get("values")[0]
            if (self.dummy_node.node_material == 'user defined') or (self.dummy_node.node_material == ''):
                tag_state = 'enabled'
            else:
                tag_state = 'disabled'
            self.dummy_node.node_volume = self.property_tree.item(5).get("values")
            self.dummy_node.node_density = self.property_tree.item(6).get("values")
            current_tags = self.property_tree.item(6)['tags']
            new_tags = (current_tags[0], tag_state)
            self.property_tree.item(6, tags=new_tags)
            self.dummy_node.node_Cp = self.property_tree.item(7).get("values")
            current_tags = self.property_tree.item(7)['tags']
            new_tags = (current_tags[0], tag_state)
            self.property_tree.item(7, tags=new_tags)
            self.dummy_node.node_volume = self.property_tree.item(5).get("values")
            self.dummy_node.node_volumetric_power = self.property_tree.item(11).get("values")
        elif self.dummy_node.node_type == "Total Heat source":
            self.dummy_node.node_material = self.property_tree.item(4).get("values")[0]
            if (self.dummy_node.node_material == 'user defined') or (self.dummy_node.node_material == ''):
                tag_state = 'enabled'
            else:
                tag_state = 'disabled'
            self.dummy_node.node_volume = self.property_tree.item(5).get("values")
            self.dummy_node.node_density = self.property_tree.item(6).get("values")
            current_tags = self.property_tree.item(6)['tags']
            new_tags = (current_tags[0], tag_state)
            self.property_tree.item(6, tags=new_tags)
            self.dummy_node.node_Cp = self.property_tree.item(7).get("values")
            current_tags = self.property_tree.item(7)['tags']
            new_tags = (current_tags[0], tag_state)
            self.property_tree.item(7, tags=new_tags)
            self.dummy_node.node_power = self.property_tree.item(12).get("values")
        elif self.dummy_node.node_type == "Thermostatic heat source":
            self.dummy_node.node_material = self.property_tree.item(4).get("values")[0]
            if (self.dummy_node.node_material == 'user defined') or (self.dummy_node.node_material == ''):
                tag_state = 'enabled'
            else:
                tag_state = 'disabled'
            self.dummy_node.node_volume = self.property_tree.item(5).get("values")
            self.dummy_node.node_density = self.property_tree.item(6).get("values")
            current_tags = self.property_tree.item(6)['tags']
            new_tags = (current_tags[0], tag_state)
            self.property_tree.item(6, tags=new_tags)
            self.dummy_node.node_Cp = self.property_tree.item(7).get("values")
            current_tags = self.property_tree.item(7)['tags']
            new_tags = (current_tags[0], tag_state)
            self.property_tree.item(7, tags=new_tags)
            self.dummy_node.node_power = self.property_tree.item(12).get("values")
            self.dummy_node.node_thermostatic_node = self.property_tree.item(13).get("values")[0]
            self.dummy_node.node_temp_on = self.property_tree.item(14).get("values")
            self.dummy_node.node_temp_off = self.property_tree.item(15).get("values")
        else:
            pass
        self.property_tree.tag_configure('disabled', foreground='gray')
        self.property_tree.tag_configure('enabled', foreground='black')

    def update_element(self):
        self.dummy_elm.elmType = self.property_tree.item(1).get("values")[0]
        self.dummy_elm.elmSubType = self.property_tree.item(2).get("values")[0]
        self.dummy_elm.label = self.property_tree.item(3).get("values")[0]
        self.dummy_elm.comment = self.property_tree.item(4).get("values")[0]
        if self.dummy_elm.elmType == "Conduction":
            if self.dummy_elm.elmSubType == "Linear conduction":
                self.dummy_elm.material = self.property_tree.item(5).get("values")[0]
                self.dummy_elm.area = self.property_tree.item(6).get("values")
                self.dummy_elm.thermal_conductivity = self.property_tree.item(7).get("values")
                self.dummy_elm.width = self.property_tree.item(15).get("values")
            elif self.dummy_elm.elmSubType == "Cylindrical conduction":
                self.dummy_elm.material = self.property_tree.item(5).get("values")[0]
                self.dummy_elm.thermal_conductivity = self.property_tree.item(7).get("values")
                self.dummy_elm.inner_radius = self.property_tree.item(12).get("values")
                self.dummy_elm.outer_radius = self.property_tree.item(13).get("values")
                self.dummy_elm.height = self.property_tree.item(14).get("values")
            elif self.dummy_elm.elmSubType == "Spherical conduction":
                self.dummy_elm.material = self.property_tree.item(5).get("values")[0]
                self.dummy_elm.thermal_conductivity = self.property_tree.item(7).get("values")
                self.dummy_elm.inner_radius = self.property_tree.item(12).get("values")
                self.dummy_elm.outer_radius = self.property_tree.item(13).get("values")
            # Check if the material is from the internal library and disable the user defined physical properties
            if (self.dummy_elm.material == 'user defined') or (self.dummy_elm.material == ''):
                tag_state = 'enabled'
            else:
                tag_state = 'disabled'
            current_tags = self.property_tree.item(7)['tags']
            new_tags = (current_tags[0], tag_state)
            self.property_tree.item(7, tags=new_tags)
            self.property_tree.tag_configure('disabled', foreground='gray')
            self.property_tree.tag_configure('enabled', foreground='black')
        elif self.dummy_elm.elmType == "Convection":
            if self.dummy_elm.elmSubType == "assigned HTC":
                self.dummy_elm.area = self.property_tree.item(6).get("values")
                self.dummy_elm.convection_htc = self.property_tree.item(16).get("values")
            elif self.dummy_elm.elmSubType == "pipe/duct":
                self.dummy_elm.material = self.property_tree.item(5).get("values")[0]
                self.dummy_elm.area = self.property_tree.item(6).get("values")
                self.dummy_elm.velocity = self.property_tree.item(8).get("values")
                self.dummy_elm.characteristic_length = self.property_tree.item(9).get("values")
            elif self.dummy_elm.elmSubType == "Cylinder":
                self.dummy_elm.material = self.property_tree.item(5).get("values")[0]
                self.dummy_elm.area = self.property_tree.item(6).get("values")
                self.dummy_elm.velocity = self.property_tree.item(8).get("values")
                self.dummy_elm.characteristic_length = self.property_tree.item(9).get("values")
            elif self.dummy_elm.elmSubType == "Diamond/Square":
                self.dummy_elm.material = self.property_tree.item(5).get("values")[0]
                self.dummy_elm.area = self.property_tree.item(6).get("values")
                self.dummy_elm.velocity = self.property_tree.item(8).get("values")
                self.dummy_elm.width = self.property_tree.item(15).get("values")
            elif self.dummy_elm.elmSubType == "Impinging Round jet":
                self.dummy_elm.material = self.property_tree.item(5).get("values")[0]
                self.dummy_elm.velocity = self.property_tree.item(8).get("values")
                self.dummy_elm.characteristic_length = self.property_tree.item(9).get("values")
                self.dummy_elm.radius = self.property_tree.item(11).get("values")
                self.dummy_elm.height = self.property_tree.item(14).get("values")
            elif self.dummy_elm.elmSubType == "Flat Plate":
                self.dummy_elm.material = self.property_tree.item(5).get("values")[0]
                self.dummy_elm.area = self.property_tree.item(6).get("values")
                self.dummy_elm.velocity = self.property_tree.item(8).get("values")
                self.dummy_elm.x_begin = self.property_tree.item(17).get("values")
                self.dummy_elm.x_end = self.property_tree.item(18).get("values")
            elif self.dummy_elm.elmSubType == "EFC Sphere":
                self.dummy_elm.material = self.property_tree.item(5).get("values")[0]
                self.dummy_elm.velocity = self.property_tree.item(8).get("values")
                self.dummy_elm.characteristic_length = self.property_tree.item(9).get("values")
            elif self.dummy_elm.elmSubType == "Vertical rectangular enclosure":
                self.dummy_elm.material = self.property_tree.item(5).get("values")[0]
                self.dummy_elm.area = self.property_tree.item(6).get("values")
                self.dummy_elm.height = self.property_tree.item(14).get("values")
                self.dummy_elm.width = self.property_tree.item(15).get("values")
            elif self.dummy_elm.elmSubType == "ENC Horizontal cylinder":
                self.dummy_elm.material = self.property_tree.item(5).get("values")[0]
                self.dummy_elm.area = self.property_tree.item(6).get("values")
                self.dummy_elm.characteristic_length = self.property_tree.item(9).get("values")
            elif self.dummy_elm.elmSubType == "Horizontal plate facing down":
                self.dummy_elm.material = self.property_tree.item(5).get("values")[0]
                self.dummy_elm.area = self.property_tree.item(6).get("values")
                self.dummy_elm.characteristic_length = self.property_tree.item(9).get("values")
            elif self.dummy_elm.elmSubType == "Horizontal plate facing up":
                self.dummy_elm.material = self.property_tree.item(5).get("values")[0]
                self.dummy_elm.area = self.property_tree.item(6).get("values")
                self.dummy_elm.characteristic_length = self.property_tree.item(9).get("values")
            elif self.dummy_elm.elmSubType == "Inclined plate facing down":
                self.dummy_elm.material = self.property_tree.item(5).get("values")[0]
                self.dummy_elm.area = self.property_tree.item(6).get("values")
                self.dummy_elm.characteristic_length = self.property_tree.item(9).get("values")
                self.dummy_elm.angle_theta = self.property_tree.item(10).get("values")
                self.dummy_elm.height = self.property_tree.item(14).get("values")
            elif self.dummy_elm.elmSubType == "Inclined plate facing up":
                self.dummy_elm.material = self.property_tree.item(5).get("values")[0]
                self.dummy_elm.area = self.property_tree.item(6).get("values")
                self.dummy_elm.characteristic_length = self.property_tree.item(9).get("values")
                self.dummy_elm.angle_theta = self.property_tree.item(10).get("values")
                self.dummy_elm.height = self.property_tree.item(14).get("values")
            elif self.dummy_elm.elmSubType == "ENC Sphere":
                self.dummy_elm.material = self.property_tree.item(5).get("values")[0]
                self.dummy_elm.characteristic_length = self.property_tree.item(9).get("values")
            elif self.dummy_elm.elmSubType == "Vertical flat plate":
                self.dummy_elm.material = self.property_tree.item(5).get("values")[0]
                self.dummy_elm.area = self.property_tree.item(6).get("values")
                self.dummy_elm.characteristic_length = self.property_tree.item(9).get("values")
        elif self.dummy_elm.elmType == "Radiation":
            if self.dummy_elm.elmSubType == "Surface Radiation":
                self.dummy_elm.area = self.property_tree.item(6).get("values")
                self.dummy_elm.emissivity = self.property_tree.item(19).get("values")[0]
            elif self.dummy_elm.elmSubType == "Radiation":
                self.dummy_elm.area = self.property_tree.item(6).get("values")
                self.dummy_elm.exchange_factor_12 = self.property_tree.item(20).get("values")[0]
                self.dummy_elm.exchange_factor_21 = self.property_tree.item(21).get("values")[0]
        elif self.dummy_elm.elmType == "Advection":
            if self.dummy_elm.elmSubType == "Advection":
                self.dummy_elm.material = self.property_tree.item(5).get("values")[0]
                self.dummy_elm.area = self.property_tree.item(6).get("values")
                self.dummy_elm.velocity = self.property_tree.item(8).get("values")
            elif self.dummy_elm.elmSubType == "Outflow":
                self.dummy_elm.material = self.property_tree.item(5).get("values")[0]
                self.dummy_elm.area = self.property_tree.item(6).get("values")
                self.dummy_elm.velocity = self.property_tree.item(8).get("values")
        else:
            pass

    def get_info(self):
        item = self.property_tree.item(0)
        parent = item.get("text")
        if parent == "Node ID":
            # print("node ID: ", self.dummy_node.node_ID)
            return self.dummy_node
        elif parent == "element ID":
            # print("elm ID: ", self.dummy_elm.elmID)
            return self.dummy_elm
        else:
            pass


"""---------------------------------------------------------------------------------------------------------------"""


def show_int_node():
    dummy_node = ThermalNode
    dummy_node.node_ID = 1
    dummy_node.node_type = "Internal Node"
    dummy_node.node_label = "node_1"
    dummy_node.node_material = "Air"
    dummy_node.node_density = [1.192, f'kg/m\N{SUPERSCRIPT THREE}']
    dummy_node.node_volume = ["100", f'm\N{SUPERSCRIPT THREE}']
    dummy_node.node_Cp = [1012.0, f'J/kg·K']
    dummy_node.node_comment = "node test"
    dummy_node.node_area = [0, f'm\N{SUPERSCRIPT TWO}']
    dummy_node.node_temperature = [20, f'°C']
    dummy_node.node_heat_flux = [0, f'W/m\N{SUPERSCRIPT TWO}']
    dummy_node.node_volumetric_power = [0, f'W/m\N{SUPERSCRIPT THREE}']
    dummy_node.node_power = [0, f'W']
    dummy_node.node_thermostatic_node = None
    dummy_node.node_temp_on = [20, f'°C']
    dummy_node.node_temp_off = [20, f'°C']

    prop_edit.edit_node(dummy_node)


def show_element():
    dummy_elm = ThermalElm
    dummy_elm.elmID = 1
    dummy_elm.elmType = 'Conduction'
    dummy_elm.elmSubType = 'Linear conduction'
    dummy_elm.label = 'element_1'
    dummy_elm.comment = 'element test'
    dummy_elm.material = 'air'
    dummy_elm.area = [1, f'm\N{SUPERSCRIPT TWO}']
    dummy_elm.thermal_conductivity = [1, f'W/m·K']
    dummy_elm.velocity = [1, f'm/s']
    dummy_elm.characteristic_length = [1, f'm']
    dummy_elm.angle_theta = [1, f'rad']
    dummy_elm.radius = [1, f'm']
    dummy_elm.inner_radius = [1, f'm']
    dummy_elm.outer_radius = [2, f'm']
    dummy_elm.height = [1, f'm']
    dummy_elm.width = [1, f'm']
    dummy_elm.convection_htc = [1, f'W/m\N{SUPERSCRIPT TWO}K']
    dummy_elm.x_begin = [0, f'm']
    dummy_elm.x_end = [1, f'm']
    dummy_elm.emissivity = [1, '']
    dummy_elm.exchange_factor_12 = [0, '']
    dummy_elm.exchange_factor_21 = [0, '']

    prop_edit.edit_elm(dummy_elm)


def update_item(var_name, index, mode):
    pass
    """
    something is changed in the property editor, the dictionary of the nodes or the elements must be updated
    with the user value data. This is done via a traceback call in the main project.
    Here the function is just used ot have a proper call of the class
    """


if __name__ == '__main__':
    win = Tk()
    win.title('Test of Property Editor')

    prop_edit = PropertyEditor(win, update_item)
    prop_edit.pack(padx=10, pady=10)
    a = Button(win, text="Internal node", command=show_int_node)
    b = Button(win, text="Linear conduction", command=show_element)

    a.pack(padx=10, pady=10, )
    b.pack(padx=10, pady=10, )

    win.mainloop()
