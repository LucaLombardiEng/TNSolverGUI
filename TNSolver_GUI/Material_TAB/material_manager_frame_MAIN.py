"""
    Class MaterialManager
    This GUI is designed for importing of an external material library as XLM format
    It gives the possibility of defining a user material

    Luca Lombardi
    07 Dec 2025: First Draft

    KNOWN ISSUES LIST
    -
    before eliminating a material from a database already exported it must be controlled if the material was already
    assigned and eventually rise an error message

    the default materials cannot be edited or deleted

    materials names cannot differ by the usage of capital letters only


"""

import tkinter as tk
from tkinter import Tk, LabelFrame, Label, Frame, Scrollbar, Button, Entry, Menu, messagebox, filedialog, simpledialog
from tkinter.ttk import Treeview
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import os
import re
import copy
import numpy as np
import pint

# --- Matplotlib Imports ---
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

# --- import general utilities ---
from TNSolver_GUI.Thermal_Network_TAB.gUtility import (validate_real_number)
from TNSolver_GUI.Function_TAB.import_excel_data import ExcelImporterApp


class MaterialManager(Frame):
    def __init__(self, parent, material_dict, update_material_callback, xml_file_path=None):
        Frame.__init__(self, parent)
        # --- Integration Hooks ---
        self.xml_file_path = xml_file_path or ""
        self.material_dict = material_dict  # Reference to the main program's dict
        self.update_callback = update_material_callback
        self.ureg = pint.UnitRegistry()
        self.ureg.define('Pa_s = pascal * second = Pa-s = Pa.s')

        # Initialize local database with existing project data
        self.material_database = copy.deepcopy(self.material_dict)

        # --- Data Structures ---
        self.library_data = {}
        self.unit_map = {}
        self.active_context = None
        self.current_mat_name = None
        self.current_prop_name = None

        self.canvas = None
        self.toolbar = None

        self._build_ui()

        # Populate UI from existing data
        if self.xml_file_path:
            self.populate_library(self.xml_file_path)
        self._refresh_project_tree()

    def _build_ui(self):
        """Builds the layout."""
        self._frame_matlib = LabelFrame(self, text="Material Management", padx=10, pady=5)
        self._frame_matlib.pack(side='top', fill='both', expand=True, pady=10)

        # 1. LEFT: Library
        self._left_frame = LabelFrame(self._frame_matlib, text="Library (XML)", width=250)
        self._left_frame.pack(side='left', padx=5, pady=5, fill='y')
        self._lib_scroll = Scrollbar(self._left_frame)
        self._lib_scroll.pack(side='right', fill='y')
        self.library_tree = Treeview(self._left_frame, selectmode='browse', show='tree',
                                     yscrollcommand=self._lib_scroll.set)
        self.library_tree.pack(fill='both', expand=True)
        self._lib_scroll.config(command=self.library_tree.yview)
        self.library_tree.bind('<<TreeviewSelect>>', self.on_library_select)

        # 2. BUTTONS (Modified to include "Apply")
        self._btn_frame = Frame(self._frame_matlib)
        self._btn_frame.pack(side='left', padx=5, pady=5, fill='y')
        self._btn_container = Frame(self._btn_frame)
        self._btn_container.pack(side='top', pady=50)

        Button(self._btn_container, text="Add >>", width=13, command=self.add_to_project).pack(pady=5)
        Button(self._btn_container, text="Del", width=13, command=self.remove_from_project).pack(pady=5)

        self.apply_btn = Button(self._btn_container, text="Apply to Project",
                                width=13, bg="#e1f5fe", fg="blue", font=('Helvetica', 9, 'bold'),
                                command=self.apply_to_main_program)
        self.apply_btn.pack(pady=(30, 5))

        Button(self._btn_container, text="Import db", width=13, command=self.import_project_database).pack(pady=(20, 5))
        Button(self._btn_container, text="Export db", width=13, command=self.export_project_database).pack(pady=5)

        # 3. MIDDLE: Project Database
        self._mid_frame = LabelFrame(self._frame_matlib, text="Active Project Materials", width=250)
        self._mid_frame.pack(side='left', padx=5, pady=5, fill='y')
        self._proj_scroll = Scrollbar(self._mid_frame)
        self._proj_scroll.pack(side='right', fill='y')
        self.project_tree = Treeview(self._mid_frame, selectmode='browse', show='tree',
                                     yscrollcommand=self._proj_scroll.set)
        self.project_tree.pack(fill='both', expand=True)
        self._proj_scroll.config(command=self.project_tree.yview)
        self.project_tree.bind('<<TreeviewSelect>>', self.on_project_select)
        self.project_tree.bind('<Double-1>', self.rename_material_inplace)
        self.project_tree.bind('<Button-3>', self.on_project_right_click)

        # 4. RIGHT: Properties & Plots
        self._right_frame = Frame(self._frame_matlib)
        self._right_frame.pack(side='left', padx=5, pady=5, fill='both', expand=True)

        self._frame_prop = LabelFrame(self._right_frame, text="Properties", padx=5, pady=5)
        self._frame_prop.pack(side='top', fill='x', padx=5, pady=5)
        self.prop_tree = self._create_property_tree(self._frame_prop, 3)
        self.prop_tree.bind('<Double-1>', self.on_property_double_click)
        self.prop_tree.bind('<Button-3>', self.on_property_right_click)

        self._lower_right_container = Frame(self._right_frame)
        self._lower_right_container.pack(side='top', fill='both', expand=True, padx=5, pady=5)

        self._frame_array = LabelFrame(self._lower_right_container, text="Array Data", padx=5, pady=5)
        self._frame_array.pack(side='top', fill='both', expand=True, pady=(0, 5))

        self._frame_plot = LabelFrame(self._lower_right_container, text="Property Graph", padx=5, pady=5)
        self._frame_plot.pack(side='top', fill='both', expand=True, pady=(5, 0))
        self._clear_lower_right_frames()

    # =========================================================================
    # INTEGRATION METHODS
    # =========================================================================

    def _refresh_project_tree(self):
        """Clears and repopulates the project tree from self.material_database."""
        self.project_tree.delete(*self.project_tree.get_children())
        for mat_name in self.material_database.keys():
            self.project_tree.insert("", "end", text=mat_name)

    def apply_to_main_program(self):
        """
        Calculates Prandtl numbers for all fluid materials, updates the UI,
        and syncs the local database to the main program dictionary.
        """
        if not self.material_database:
            if not messagebox.askyesno("Confirm",
                                       "The project database is empty. Proceed with clearing project materials?"):
                return

        # 1. Automatically calculate Prandtl for all materials in the project
        # This uses your existing _auto_calculate_prandtl which checks if the material is a fluid.
        for mat_name in self.material_database.keys():
            self._auto_calculate_prandtl(mat_name)

        # 2. Refresh the UI properties tree for the currently viewed material
        # This ensures the 'Prandtl_Number' row appears immediately in the table.
        if self.current_mat_name and self.active_context == 'project':
            self.show_properties(self.current_mat_name, self.material_database)

        # 3. Update the shared dictionary for the main solver
        self.material_dict.clear()
        self.material_dict.update(copy.deepcopy(self.material_database))

        # 4. Call the update hook in the main program
        try:
            if self.update_callback:
                self.update_callback()

            messagebox.showinfo("Success",
                                f"Applied {len(self.material_dict)} materials. \n"
                                "Prandtl numbers calculated for fluid materials.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update main program: {e}")

    # =========================================================================
    # NEW FEATURE: CONTEXT MENU & TYPE SWITCHING
    # =========================================================================

    def on_property_right_click(self, event):
        """Popup to switch between Constant and Table for specific properties."""
        if self.active_context != 'project':
            return

        item_id = self.prop_tree.identify_row(event.y)
        if not item_id:
            return

        self.prop_tree.selection_set(item_id)
        prop_name = self.prop_tree.item(item_id, 'values')[0]

        # Filter for the "Big Five"
        targets = ["Dynamic_Viscosity", "Mass_Density", "Specific_Heat", "Thermal_Conductivity", "Thermal_Expansion"]
        if not any(t in prop_name for t in targets):
            return

        popup = Menu(self, tearoff=0)
        popup.add_command(label="Set as Constant (Scalar)",
                          command=lambda: self.switch_property_mode(prop_name, 'scalar'))
        popup.add_command(label="Set as Table (f(T))",
                          command=lambda: self.switch_property_mode(prop_name, 'table'))
        popup.post(event.x_root, event.y_root)
        popup.add_command(label="Convert Unit...",
                          command=lambda: self.open_unit_converter(prop_name))
        popup.post(event.x_root, event.y_root)

    def switch_property_mode(self, prop_name, target_type):
        """Converts property between scalar and table format."""
        mat = self.current_mat_name
        current = self.material_database[mat][prop_name]

        if target_type == 'scalar' and current['type'] != 'scalar':
            # Convert Table to Scalar (Take first param value)
            val = current['param_data'].split(',')[0] if current.get('param_data') else "0.0"
            self.material_database[mat][prop_name] = {
                'type': 'scalar', 'value': val, 'unit': current.get('param_unit', '')
            }
        elif target_type == 'table' and current['type'] != 'table':
            # Convert Scalar to Table (Default T range)
            val = current.get('value', '0.0')
            self.material_database[mat][prop_name] = {
                'type': 'table',
                'qualifier_name': 'Temperature',
                'qualifier_data': '20, 100, 200',
                'qualifier_unit': '°C',
                'param_name': prop_name,
                'param_data': f"{val}, {val}, {val}",
                'param_unit': current.get('unit', '')
            }
        self.show_properties(mat, self.material_database)

    # =========================================================================
    # UPDATED: AUTO-SORTING SYNC LOGIC
    # =========================================================================

    def _sync_and_sort_array(self):
        """
        Reads the current array tree, sorts the pairs numerically by
        temperature, and updates the database and display.
        """
        if not self.current_mat_name or not self.current_prop_name:
            return

        data_pairs = []
        for item in self.array_tree.get_children():
            v = self.array_tree.item(item, "values")
            try:
                # Convert to float during the reading
                data_pairs.append((float(v[0]), float(v[1])))
            except ValueError:
                continue

        # Sorting
        data_pairs.sort(key=lambda x: x[0])

        # Extract the data as numpy array
        q_array = np.array([p[0] for p in data_pairs])
        p_array = np.array([p[1] for p in data_pairs])

        # Database update
        prop_ref = self.material_database[self.current_mat_name][self.current_prop_name]
        prop_ref['qualifier_data'] = q_array
        prop_ref['param_data'] = p_array

        # UI refresh
        self.show_array_data(prop_ref)

    # =========================================================================
    # RESTORED HELPERS (From your original code)
    # =========================================================================

    @staticmethod
    def _trim_property_name(name):
        if name is None:
            return ""
        first = name.find('_')
        if first != -1:
            second = name.find('_', first + 1)
            if second != -1:
                return name[:second]
        return name

    def _get_unit_with_fallback(self, prop_id_full):
        if prop_id_full is None:
            return ""
        unit = self.unit_map.get(prop_id_full, "")
        if unit:
            return unit
        match = re.match(r'(.*__\w+)', prop_id_full)
        if match:
            base_id_prefix = match.group(1)
            for unit_id, unit_str in self.unit_map.items():
                if unit_id.startswith(base_id_prefix) and unit_str:
                    return unit_str
        return ""

    @staticmethod
    def _is_property_allowed(prop_name):
        p_norm = prop_name.lower().replace('_', ' ').strip()
        keywords = ["viscos", "mass density", "specific heat", "conductiv", "gas constant", "expansion",
                    "material type", "category", "prandtl", "state"]
        return any(kw in p_norm for kw in keywords)

    def populate_library(self, xml_file):
        if not os.path.exists(xml_file):
            print(f"Error: File {xml_file} not found.")
            return

        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
        except ET.ParseError as e:
            print(f"Error parsing XML: {e}")
            return

        # Safe helper to extract text without crashing on NoneType
        def safe_get_text(elem, _path, default="Unknown"):
            _node = elem.find(_path)
            if _node is not None and _node.text:
                return _node.text.strip()
            return default

        # Unit mapping
        for detail in root.findall(".//PropertyDetails") + root.findall(".//ParameterDetails"):
            p_id = detail.get("id")
            u_node = detail.find("Units/Unit/Name")
            if u_node is not None and u_node.text:
                self.unit_map[p_id] = u_node.text

        hierarchy = {"Solid": {}, "Liquid": {}, "Gas": {}}

        for material in root.findall("Material"):
            bulk = material.find("BulkDetails")
            if bulk is None:
                continue

            name = safe_get_text(bulk, "Name", "Unnamed Material")
            subclass = safe_get_text(bulk, "Subclass/Name", "Unknown").upper()
            m_class = safe_get_text(bulk, "Class/Name", "Other").upper()

            # Category Logic
            main_cat = "Gas" if "GAS" in subclass else ("Liquid" if "LIQUID" in subclass else "Solid")

            if "METAL" in m_class:
                sub_cat = "Metals"
            elif "PLASTIC" in m_class:
                sub_cat = "Plastics"
            else:
                sub_cat = "Other"

            if sub_cat not in hierarchy[main_cat]:
                hierarchy[main_cat][sub_cat] = []
            hierarchy[main_cat][sub_cat].append(name)

            props = {}
            # Metadata
            props['Material_Type'] = {'type': 'scalar', 'value': m_class.title(), 'unit': ''}
            props['Category'] = {'type': 'scalar', 'value': subclass.title(), 'unit': ''}
            props['State'] = {'type': 'scalar', 'value': main_cat, 'unit': ''}

            for prop in bulk.findall("PropertyData"):
                p_id = prop.get("property")
                p_name = self._trim_property_name(p_id)
                data_node = prop.find("Data")
                param_node = prop.find("ParameterValue")

                if param_node is not None:
                    # LOGIC TABLE: conversion to NumPy array
                    p_id_val = param_node.get("parameter")
                    param_data_node = param_node.find("Data")

                    raw_q = data_node.text if data_node is not None else ""
                    raw_p = param_data_node.text if param_data_node is not None else ""

                    try:
                        # np.fromstring separate the strings using the commas and convert in floats
                        q_array = np.fromstring(raw_q, sep=',')
                        p_array = np.fromstring(raw_p, sep=',')
                    except:
                        # Fallback in case of XML data not formatted correctly
                        q_array = np.array([])
                        p_array = np.array([])

                    props[p_name] = {
                        'type': 'table',
                        'qualifier_name': 'Temperature',
                        'qualifier_data': q_array,  # saved as numerical data
                        'qualifier_unit': '°C',
                        'param_name': p_name,
                        'param_data': p_array,  # saved as numerical data
                        'param_unit': self._get_unit_with_fallback(p_id_val)
                    }
                else:
                    # SCALAR LOGIC: it remains a string to permit the editing in the UI
                    val = data_node.text if data_node is not None else "N/A"
                    props[p_name] = {
                        'type': 'scalar',
                        'value': val,
                        'unit': self._get_unit_with_fallback(p_id)
                    }
            self.library_data[name] = props

        # Build Tree View
        for m_cat in ["Solid", "Liquid", "Gas"]:
            if hierarchy[m_cat]:
                node = self.library_tree.insert("", "end", text=m_cat, open=True)
                for s_cat in sorted(hierarchy[m_cat].keys()):
                    sub = self.library_tree.insert(node, "end", text=s_cat)
                    for m_name in sorted(hierarchy[m_cat][s_cat]):
                        self.library_tree.insert(sub, "end", text=m_name, values=(m_name,))

    # =========================================================================
    # DISPLAY & SELECTION
    # =========================================================================

    def on_library_select(self, event):
        self.active_context = 'library'
        sel = self.library_tree.selection()
        if not sel:
            return
        val = self.library_tree.item(sel[0], "values")
        if val:
            self.show_properties(val[0], self.library_data)

    def on_project_select(self, event):
        self.active_context = 'project'
        sel = self.project_tree.selection()
        if not sel:
            return
        name = self.project_tree.item(sel[0], "text")
        self.show_properties(name, self.material_database)

    def add_to_project(self):
        """
        Adds selected library material to the project with full SI unit conversion.
        Supersedes add_to_project_old.
        """
        sel = self.library_tree.selection()
        if not sel:
            return
        src_name = self.library_tree.item(sel[0], "values")[0]

        si_targets = {
            "Mass_Density": "kg/m**3",
            "Specific_Heat": "J/(kg*K)",
            "Thermal_Conductivity": "W/(m*K)",
            "Dynamic_Viscosity": "Pa*s",
            "Thermal_Expansion": "1/K",
            "Gas_Constant": "J/(kg*K)",
            "Molar_Mass": "kg/mol"
        }

        new_material_data = {}
        source_props = self.library_data[src_name]

        for key, prop_data in source_props.items():
            if self._is_property_allowed(key):
                new_prop = copy.deepcopy(prop_data)
                target_unit = next((u for k, u in si_targets.items() if k in key), None)

                try:
                    if target_unit:
                        if new_prop['type'] == 'scalar':
                            raw_val = float(new_prop.get('value', 0.0))
                            src_u = self._sanitize_unit(new_prop.get('unit', ''))
                            val_si = self.ureg.Quantity(raw_val, src_u).to(target_unit).magnitude
                            new_prop['value'] = f"{val_si:.6g}"
                            new_prop['unit'] = target_unit
                        elif new_prop['type'] == 'table':
                            raw_data = new_prop.get('param_data')
                            src_u = self._sanitize_unit(new_prop.get('param_unit', ''))
                            vals_si = self.ureg.Quantity(raw_data, src_u).to(target_unit).magnitude
                            new_prop['param_data'] = vals_si
                            new_prop['param_unit'] = target_unit
                    else:
                        # Sanitize units even if no target conversion is defined
                        if new_prop['type'] == 'scalar':
                            new_prop['unit'] = self._sanitize_unit(new_prop.get('unit', ''))
                        elif new_prop['type'] == 'table':
                            new_prop['param_unit'] = self._sanitize_unit(new_prop.get('param_unit', ''))
                except Exception as e:
                    print(f"SI Conversion warning for {key}: {e}")

                new_material_data[key] = new_prop

        # Handle Naming
        name, c = src_name, 1
        while name in self.material_database:
            name, c = f"{src_name}_{c}", c + 1

        self.material_database[name] = new_material_data
        self.project_tree.insert("", "end", text=name)

        # Trigger Prandtl immediately so the project store is complete
        self._auto_calculate_prandtl(name)

    def remove_from_project(self):
        sel = self.project_tree.selection()
        if not sel:
            return
        del self.material_database[self.project_tree.item(sel[0], "text")]
        self.project_tree.delete(sel[0])
        self._clear_property_view()

    def show_properties(self, mat_name, db):
        self.current_mat_name = mat_name
        self.prop_tree.delete(*self.prop_tree.get_children())
        self._clear_lower_right_frames()
        self._frame_prop.config(text=f"Properties for: {mat_name}")

        for p_name, p_data in sorted(db[mat_name].items()):
            val = "table" if p_data['type'] == 'table' else p_data.get('value', 'N/A')
            unit = p_data.get('unit', '') if p_data['type'] == 'scalar' else ""
            self.prop_tree.insert("", "end", iid=p_name, values=(p_name, val, unit))

    def on_property_double_click(self, event):
        sel = self.prop_tree.selection()
        if not sel:
            return
        p_name = sel[0]
        p_data = \
            (self.material_database if self.active_context == 'project' else self.library_data)[self.current_mat_name][
                p_name]

        if p_data['type'] == 'table':
            self.current_prop_name = p_name
            self.show_array_data(p_data)
        elif self.active_context == 'project':
            self.edit_scalar_property(sel[0], p_name)

    def edit_scalar_property(self, item_id, p_name):
        """Edits scalar values with real-time key validation."""
        x, y, w, h = self.prop_tree.bbox(item_id, column="Col2")

        # Ensure these match your XML trimmed names exactly (check for underscores vs spaces)
        physics_props = [
            "Mass_Density", "Specific_Heat", "Dynamic_Viscosity",
            "Molar_Mass", "Thermal_Conductivity", "Gas_Constant", "Thermal_Expansion"
        ]

        vcmd = None
        if any(prop in p_name for prop in physics_props):
            vcmd = (self.register(validate_real_number), "%P")

        entry = Entry(self.prop_tree, validate="key", validatecommand=vcmd)
        entry.insert(0, self.material_database[self.current_mat_name][p_name]['value'])
        entry.place(x=x, y=y, width=w, height=h)
        entry.focus()

        def save(e=None):
            if not entry.winfo_exists():
                return
            val = entry.get()
            self.material_database[self.current_mat_name][p_name]['value'] = val
            self.prop_tree.set(item_id, "Col2", val)
            entry.destroy()

        entry.bind("<Return>", save)
        entry.bind("<FocusOut>", lambda e: entry.after(100, save))  # Small delay to prevent race conditions

    def show_array_data(self, p_data):
        self._clear_lower_right_frames()
        self.array_tree = self._create_property_tree(self._frame_array, 2)

        if self.active_context == 'project':
            self.array_tree.bind('<Double-1>', self.on_array_double_click)
            self.array_tree.bind('<Button-3>', self.on_array_right_click)

        q_name = p_data['qualifier_name']
        p_name = self._trim_property_name(p_data['param_name'])

        self.array_tree.heading("Col1", text=f"{q_name} ({p_data['qualifier_unit']})")
        self.array_tree.heading("Col2", text=f"{p_name} ({p_data['param_unit']})")

        # Logica di estrazione: gestisce sia Array che Stringhe
        q_vals = p_data['qualifier_data']
        p_vals = p_data['param_data']

        if isinstance(q_vals, str):
            q_vals = [x.strip() for x in re.split(r'\s*,\s*', q_vals) if x.strip()]
            p_vals = [x.strip() for x in re.split(r'\s*,\s*', p_vals) if x.strip()]

        # Conversione per il plot e inserimento in tabella
        x_plot, y_plot = [], []
        for q, p in zip(q_vals, p_vals):
            self.array_tree.insert("", "end", values=(q, p))
            x_plot.append(float(q))
            y_plot.append(float(p))

        if x_plot:
            self._show_array_plot(x_plot, y_plot, q_name, p_name)

    # =========================================================================
    # NEW: ARRAY MANAGEMENT (RIGHT-CLICK)
    # =========================================================================
    def on_array_right_click(self, event):
        """Context menu for the Array Data table."""
        if self.active_context != 'project':
            return

        # Identify the row under the mouse
        item_id = self.array_tree.identify_row(event.y)

        # If right-clicking an unselected row, select it
        if item_id:
            if item_id not in self.array_tree.selection():
                self.array_tree.selection_set(item_id)

        popup = Menu(self, tearoff=0)
        popup.add_command(label="Add New Row", command=self.array_add_row)
        popup.add_command(label="Import from Excel...", command=self.launch_excel_importer)

        # Only show 'Remove' if there is a selection
        selection = self.array_tree.selection()
        if selection:
            label_text = "Remove Selected Row" if len(selection) == 1 else f"Remove {len(selection)} Rows"
            popup.add_command(label=label_text, command=self.array_remove_rows)

        popup.add_separator()
        popup.add_command(label="Clear Full Array", command=self.array_clear_all)
        popup.post(event.x_root, event.y_root)

    def on_array_double_click(self, event):
        """Now updated to use your preferred 'validate="key"' approach."""
        if self.active_context != 'project':
            return
        region = self.array_tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        column = self.array_tree.identify_column(event.x)
        item_id = self.array_tree.identify_row(event.y)
        col_idx = int(column.replace("#", "")) - 1
        x, y, w, h = self.array_tree.bbox(item_id, column)

        # Array data is ALWAYS numeric, so we always validate
        vcmd = (self.register(validate_real_number), "%P")

        entry = Entry(self.array_tree, validate="key", validatecommand=vcmd)
        entry.insert(0, self.array_tree.item(item_id, "values")[col_idx])
        entry.place(x=x, y=y, width=w, height=h)
        entry.focus()

        def save_edit(e=None):
            if not entry.winfo_exists():
                return
            new_vals = list(self.array_tree.item(item_id, "values"))
            new_vals[col_idx] = entry.get()
            self.array_tree.item(item_id, values=new_vals)
            entry.destroy()
            self._sync_and_sort_array()

        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", lambda e: entry.after(100, save_edit))

    def array_add_row(self):
        """Appends a row and immediately sorts the table."""
        prop_ref = self.material_database[self.current_mat_name][self.current_prop_name]
        q_list = [x.strip() for x in prop_ref['qualifier_data'].split(',') if x.strip()]
        p_list = [x.strip() for x in prop_ref['param_data'].split(',') if x.strip()]

        try:
            # Predict next logical temperature (+10 degrees)
            last_q = float(q_list[-1]) if q_list else 20.0
            last_p = float(p_list[-1]) if p_list else 0.0
            new_q, new_p = str(last_q + 10.0), str(last_p)
        except:
            new_q, new_p = "25.0", "0.0"

        # Instead of just calling show_array_data, we add it to the tree
        # and let the sync method handle the sorting and saving.
        self.array_tree.insert("", "end", values=(new_q, new_p))
        self._sync_and_sort_array()

    def array_remove_rows(self):
        """Removes all selected rows from the Treeview and updates the DB."""
        selected_items = self.array_tree.selection()
        if not selected_items:
            return

        # Confirmation for multiple rows (optional but safer)
        if len(selected_items) > 5:
            if not messagebox.askyesno("Confirm", f"Delete {len(selected_items)} rows?"):
                return

        # Remove from Treeview
        for item in selected_items:
            self.array_tree.delete(item)

        # Re-sync database and refresh the plot
        self._sync_and_sort_array()

    def array_clear_all(self):
        """Wipes the entire table."""
        prop_ref = self.material_database[self.current_mat_name][self.current_prop_name]
        prop_ref['qualifier_data'] = ""
        prop_ref['param_data'] = ""
        self.show_array_data(prop_ref)

    def _show_array_plot(self, x, y, xl, yl):
        fig = Figure(figsize=(5, 3), dpi=90)
        ax = fig.add_subplot(111)
        ax.plot(x, y, 'b-o', markersize=4)
        ax.set_xlabel(xl)
        ax.set_ylabel(yl)
        ax.grid(True)
        fig.tight_layout()
        self.canvas = FigureCanvasTkAgg(fig, master=self._frame_plot)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self._frame_plot)

    @staticmethod
    def _create_property_tree(parent, num_cols):
        container = Frame(parent)
        container.pack(fill='both', expand=True)
        tree = Treeview(container, columns=[f"Col{i}" for i in range(1, num_cols + 1)], show='headings')
        if num_cols == 3:
            tree.heading("Col1", text="Property")
            tree.column("Col1", width=150)
            tree.heading("Col2", text="Value")
            tree.column("Col2", width=100)
            tree.heading("Col3", text="Unit")
            tree.column("Col3", width=50)
        tree.pack(side='left', fill='both', expand=True)
        sb = Scrollbar(container, command=tree.yview)
        sb.pack(side='right', fill='y')
        tree.config(yscrollcommand=sb.set)
        return tree

    def _clear_lower_right_frames(self):
        for f in [self._frame_array, self._frame_plot]:
            for w in f.winfo_children():
                w.destroy()
        Label(self._frame_array, text="Double-click 'table' to edit array.").pack()
        Label(self._frame_plot, text="Graph will appear here.").pack()

    def _clear_property_view(self):
        self.prop_tree.delete(*self.prop_tree.get_children())
        self._clear_lower_right_frames()

    def launch_excel_importer(self):
        """Opens your ExcelImporterApp in a modal popup window."""
        popup = tk.Toplevel(self)
        popup.title("Excel Data Importer")
        popup.geometry("900x600")
        popup.transient(self.winfo_toplevel())  # Keep on top of main window
        popup.grab_set()  # Block interaction with main window until closed

        # We pass self.process_excel_data as a callback
        importer = ExcelImporterApp(popup)
        importer.pack(fill='both', expand=True)

        # We need to monkey-patch or wrap your existing import button
        # to ensure it returns data to this class.
        original_command = importer.import_columns_button['command']

        def wrapped_import():
            data = importer.import_selected_columns()
            if data:  # If data_dictionary is returned
                self.process_excel_data(data)
                popup.destroy()

        importer.import_columns_button.config(command=wrapped_import)

    def process_excel_data(self, data_dict):
        """Takes the {coord: value} dict and updates the material database."""
        if not data_dict:
            return

        # 1. Convert dict to sorted lists (Excel data can be unsorted)
        sorted_coords = sorted(data_dict.keys())
        q_vals = [str(c) for c in sorted_coords]
        p_vals = [str(data_dict[c]) for c in sorted_coords]

        # 2. Update the property reference
        prop_ref = self.material_database[self.current_mat_name][self.current_prop_name]
        prop_ref['qualifier_data'] = ", ".join(q_vals)
        prop_ref['param_data'] = ", ".join(p_vals)

        # 3. Refresh UI (Table & Graph)
        self.show_array_data(prop_ref)
        messagebox.showinfo("Import Successful", f"Imported {len(data_dict)} points from Excel.")

    # =========================================================================
    # PROJECT MANAGEMENT
    # =========================================================================

    def reset_database(self):
        """
        Refreshes the local database from the main shared dictionary.
        Call this after the main program modifies the shared dictionary in-place.
        """
        # 1. Re-sync the local working copy from the main source
        self.material_database = copy.deepcopy(self.material_dict)

        # 2. Reset internal selection state
        self.current_mat_name = None
        self.current_prop_name = None
        self.active_context = None

        # 3. Clear the UI Elements
        self._clear_property_view()

        # 4. Repopulate the Project Tree
        self._refresh_project_tree()

    def rename_material_inplace(self, event=None):
        """Places an Entry widget directly over the Treeview item for renaming."""
        sel = self.project_tree.selection()
        if not sel:
            return

        item_id = sel[0]
        old_name = self.project_tree.item(item_id, "text")

        # Get the coordinates of the item (text part)
        # Treeview.bbox returns (x, y, width, height)
        bbox = self.project_tree.bbox(item_id, column="#0")
        if not bbox or len(bbox) < 4:
            return
        x, y, w, h = bbox

        # Create the temporary entry widget
        edit_entry = Entry(self.project_tree)
        edit_entry.insert(0, old_name)
        edit_entry.select_range(0, tk.END)  # Highlight text for quick overwrite

        # Place it exactly over the tree item
        edit_entry.place(x=x, y=y, width=w, height=h)
        edit_entry.focus_set()

        def save_rename(event=None):
            new_name = edit_entry.get().strip()

            # Validation logic
            if new_name and new_name != old_name:
                if new_name in self.material_database:
                    # Optional: change background to red briefly to show error
                    edit_entry.config(bg="#ffcccc")
                    return

                    # Update Database: Migrating data to the new key
                self.material_database[new_name] = self.material_database.pop(old_name)

                # Update Treeview UI
                self.project_tree.item(item_id, text=new_name)

                # Sync current tracking
                if self.current_mat_name == old_name:
                    self.current_mat_name = new_name
                    self._frame_prop.config(text=f"Properties for: {new_name}")

            edit_entry.destroy()

        # Keyboard and Focus management
        edit_entry.bind("<Return>", save_rename)
        edit_entry.bind("<FocusOut>", lambda e: edit_entry.destroy())
        edit_entry.bind("<Escape>", lambda e: edit_entry.destroy())

    def on_project_right_click(self, event):
        """Updated context menu to call the in-place rename."""
        item_id = self.project_tree.identify_row(event.y)
        if not item_id:
            return

        self.project_tree.selection_set(item_id)

        popup = Menu(self, tearoff=0)
        popup.add_command(label="Rename", command=self.rename_material_inplace)
        popup.add_command(label="Delete", command=self.remove_from_project)
        popup.add_command(label="Import Database (.xml)", command=self.import_project_database)
        popup.add_command(label="Export Database (.xml)", command=self.export_project_database)
        popup.add_separator()
        popup.add_command(label="Calculate Prandtl (μ·Cp/k)", command=self.calculate_prandtl)
        popup.post(event.x_root, event.y_root)

    def export_project_database(self):
        """Saves the current project materials to an XML file."""
        if not self.material_database:
            messagebox.showwarning("Export", "Project database is empty.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".xml",
            filetypes=[("XML files", "*.xml")],
            title="Export Project Database"
        )

        if not file_path:
            return

        root = ET.Element("ProjectDatabase")
        for mat_name, props in self.material_database.items():
            mat_node = ET.SubElement(root, "Material", name=mat_name)
            for p_name, p_data in props.items():
                p_node = ET.SubElement(mat_node, "Property", name=p_name, type=p_data['type'])

                if p_data['type'] == 'scalar':
                    ET.SubElement(p_node, "Value").text = str(p_data.get('value', ''))
                    ET.SubElement(p_node, "Unit").text = str(p_data.get('unit', ''))
                else:
                    # Table Data
                    q_data = p_data.get('qualifier_data', '')
                    p_vals = p_data.get('param_data', '')

                    if isinstance(q_data, (list, np.ndarray)):
                        q_data = ", ".join(map(str, q_data))
                    if isinstance(p_vals, (list, np.ndarray)):
                        p_vals = ", ".join(map(str, p_vals))
                    ET.SubElement(p_node, "QualifierName").text = p_data.get('qualifier_name', '')
                    ET.SubElement(p_node, "QualifierUnit").text = p_data.get('qualifier_unit', '')
                    ET.SubElement(p_node, "QualifierData").text = q_data
                    ET.SubElement(p_node, "ParamUnit").text = p_data.get('param_unit', '')
                    ET.SubElement(p_node, "ParamData").text = p_vals

        # Pretty-print and save
        xml_str = ET.tostring(root, encoding='utf-8')
        pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="    ")

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(pretty_xml)
            messagebox.showinfo("Export", "Database exported to XML successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save XML: {e}")

    def import_project_database(self):
        """Importa materiali da un file XML e calcola automaticamente Prandtl dove possibile."""
        file_path = filedialog.askopenfilename(
            filetypes=[("XML files", "*.xml")],
            title="Import Project Database"
        )

        if not file_path:
            return

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            imported_count = 0

            for mat_node in root.findall("Material"):
                raw_name = mat_node.get("name")
                final_name = raw_name
                counter = 1
                while final_name in self.material_database:
                    final_name = f"{raw_name}_{counter}"
                    counter += 1

                mat_props = {}
                for p_node in mat_node.findall("Property"):
                    p_name = p_node.get("name")
                    p_type = p_node.get("type")

                    if p_type == 'scalar':
                        mat_props[p_name] = {
                            'type': 'scalar',
                            'value': p_node.find("Value").text or "",
                            'unit': p_node.find("Unit").text or ""
                        }
                    else:
                        # Carichiamo i dati convertendoli subito in array NumPy
                        raw_q = p_node.find("QualifierData").text or ""
                        raw_p = p_node.find("ParamData").text or ""

                        mat_props[p_name] = {
                            'type': 'table',
                            'qualifier_name': p_node.find("QualifierName").text or "",
                            'qualifier_unit': p_node.find("QualifierUnit").text or "",
                            'qualifier_data': np.fromstring(raw_q, sep=','),
                            'param_name': p_name,
                            'param_unit': p_node.find("ParamUnit").text or "",
                            'param_data': np.fromstring(raw_p, sep=',')
                        }

                self.material_database[final_name] = mat_props

                # --- CALCOLO AUTOMATICO PRANDTL ---
                # Eseguiamo il calcolo senza mostrare popup di errore per ogni materiale
                self._auto_calculate_prandtl(final_name)

                self.project_tree.insert("", "end", text=final_name)
                imported_count += 1

            messagebox.showinfo("Import", f"Merged {imported_count} materials with auto-Prandtl check.")

        except Exception as e:
            messagebox.showerror("Error", f"Invalid XML format: {e}")

    def calculate_prandtl(self):
        """Calculates Prandtl number (Pr = mu * Cp / k) with IDE-friendly Pint calls."""
        if not self.current_mat_name:
            messagebox.showwarning("Warning", "Please select a material first.")
            return

        mat_data = self.material_database[self.current_mat_name]

        # 1. Broadened Validation Logic
        category = mat_data.get('Category', {}).get('value', '').lower()
        mat_type = mat_data.get('Material_Type', {}).get('value', '').lower()

        allowed_categories = ['liquid', 'gas']
        is_valid_fluid = (category in allowed_categories) or \
                         (category == 'other' and mat_type == 'fluidmaterial')

        if not is_valid_fluid:
            messagebox.showerror("Error",
                                 f"Prandtl calculation requires a Fluid. \n"
                                 f"Current: Category={category.capitalize()}, Type={mat_type}")
            return

        req = {'mu': 'Dynamic_Viscosity', 'cp': 'Specific_Heat', 'k': 'Thermal_Conductivity'}
        missing = [name for key, name in req.items() if name not in mat_data]
        if missing:
            messagebox.showerror("Error", f"Missing: {', '.join(missing)}")
            return

        expected_si = {'mu': 'Pa*s', 'cp': 'J/(kg*K)', 'k': 'W/(m*K)'}

        try:
            def get_data_in_si(prop_key):
                p = mat_data[req[prop_key]]
                raw_unit = p.get('unit' if p['type'] == 'scalar' else 'param_unit', '')

                # SANITIZE: Fixes 'C' -> 'degC' and fixes the denominator precedence
                curr_san = self._sanitize_unit(raw_unit)
                targ_san = expected_si[prop_key]

                # Log for debugging if needed: print(f"DEBUG: {raw_unit} -> {curr_san}")

                curr_unit = self.ureg.parse_expression(curr_san)
                targ_unit = self.ureg.parse_expression(targ_san)

                # Pint handles the delta_degC automatically for conductivity/specific heat
                if p['type'] == 'scalar':
                    val = float(p['value'])
                    si_val = self.ureg.Quantity(val, curr_unit).to(targ_unit).magnitude
                    return si_val, None
                else:
                    vals = np.array(p['param_data'], dtype=float)
                    si_vals = self.ureg.Quantity(vals, curr_unit).to(targ_unit).magnitude
                    return si_vals, p['qualifier_data']

            mu_v, mu_q = get_data_in_si('mu')
            cp_v, cp_q = get_data_in_si('cp')
            k_v, k_q = get_data_in_si('k')

            if all(q is None for q in [mu_q, cp_q, k_q]):
                pr_val = (mu_v * cp_v) / k_v
                self._update_prandtl_for_mat(self.current_mat_name, pr_val, is_table=False)
            else:
                grids = [q for q in [mu_q, cp_q, k_q] if q is not None]
                common_grid = np.unique(np.concatenate(grids))
                mu_i = np.interp(common_grid, mu_q, mu_v) if mu_q is not None else np.full_like(common_grid, mu_v)
                cp_i = np.interp(common_grid, cp_q, cp_v) if cp_q is not None else np.full_like(common_grid, cp_v)
                k_i = np.interp(common_grid, k_q, k_v) if k_q is not None else np.full_like(common_grid, k_v)

                pr_vals = (mu_i * cp_i) / k_i
                self._update_prandtl_for_mat(self.current_mat_name, (common_grid, pr_vals), is_table=True)

            self.show_properties(self.current_mat_name, self.material_database)
            messagebox.showinfo("Success", "Prandtl Number calculated.")

        except Exception as e:
            messagebox.showerror("Calculation Error", f"Failure: {e}")

    def _auto_calculate_prandtl(self, mat_name):
        """Robust automated Prandtl calculation using the 'State' property."""
        mat_data = self.material_database[mat_name]

        # 1. Robust Fluid Check using 'State'
        # Defaults to empty string if 'State' is missing
        state = mat_data.get('State', {}).get('value', '').lower()

        # Only proceed if state is liquid or gas
        if state not in ['liquid', 'gas']:
            return

        req = {'mu': 'Dynamic_Viscosity', 'cp': 'Specific_Heat', 'k': 'Thermal_Conductivity'}
        if not all(name in mat_data for name in req.values()):
            return

        expected_si = {'mu': 'Pa*s', 'cp': 'J/(kg*K)', 'k': 'W/(m*K)'}

        try:
            def get_data_in_si(prop_key):
                p = mat_data[req[prop_key]]
                raw_u = p.get('unit' if p['type'] == 'scalar' else 'param_unit', '')
                curr_u = self.ureg.parse_expression(self._sanitize_unit(raw_u))
                targ_u = self.ureg.parse_expression(expected_si[prop_key])

                if p['type'] == 'scalar':
                    val = float(p['value'])
                    return self.ureg.Quantity(val, curr_u).to(targ_u).magnitude, None
                else:
                    vals = np.array(p['param_data'], dtype=float)
                    si_vals = self.ureg.Quantity(vals, curr_u).to(targ_u).magnitude
                    return si_vals, p['qualifier_data']

            mu_v, mu_q = get_data_in_si('mu')
            cp_v, cp_q = get_data_in_si('cp')
            k_v, k_q = get_data_in_si('k')

            if all(q is None for q in [mu_q, cp_q, k_q]):
                pr_val = (mu_v * cp_v) / k_v
                self._update_prandtl_for_mat(mat_name, pr_val, is_table=False)
            else:
                grids = [q for q in [mu_q, cp_q, k_q] if q is not None]
                common_grid = np.unique(np.concatenate(grids))
                mu_i = np.interp(common_grid, mu_q, mu_v) if mu_q is not None else np.full_like(common_grid, mu_v)
                cp_i = np.interp(common_grid, cp_q, cp_v) if cp_q is not None else np.full_like(common_grid, cp_v)
                k_i = np.interp(common_grid, k_q, k_v) if k_q is not None else np.full_like(common_grid, k_v)

                pr_vals = (mu_i * cp_i) / k_i
                self._update_prandtl_for_mat(mat_name, (common_grid, pr_vals), is_table=True)

        except Exception as e:
            print(f"Auto-Prandtl failed for {mat_name}: {e}")

    def _update_prandtl_for_mat(self, mat_name, data, is_table=False):
        """Save the Prandtl number in the database for the specified material."""
        if not is_table:
            self.material_database[mat_name]['Prandtl_Number'] = {
                'type': 'scalar', 'value': f"{data:.4f}", 'unit': '-'
            }
        else:
            temps, values = data
            self.material_database[mat_name]['Prandtl_Number'] = {
                'type': 'table',
                'qualifier_name': 'Temperature', 'qualifier_unit': '°C',
                'qualifier_data': temps,
                'param_name': 'Prandtl_Number', 'param_unit': '-',
                'param_data': values
            }

    def open_unit_converter(self, prop_name):
        """Converts property units using explicit Pint methods."""
        mat = self.current_mat_name
        prop_data = self.material_database[mat][prop_name]

        current_raw = prop_data.get('unit') if prop_data['type'] == 'scalar' else prop_data.get('param_unit', '')
        target_raw = simpledialog.askstring("Unit Converter", f"Convert from [{current_raw}] to:")
        if not target_raw:
            return

        try:
            # Use parse_expression to avoid "not callable" warning
            u_from = self.ureg.parse_expression(self._sanitize_unit(current_raw))
            u_to = self.ureg.parse_expression(self._sanitize_unit(target_raw))

            if prop_data['type'] == 'scalar':
                val = float(prop_data['value'])
                new_q = self.ureg.Quantity(val, u_from).to(u_to)
                prop_data['value'] = f"{new_q.magnitude:.6g}"
                prop_data['unit'] = target_raw
            else:
                vals = prop_data['param_data']
                new_q = self.ureg.Quantity(vals, u_from).to(u_to)
                prop_data['param_data'] = new_q.magnitude
                prop_data['param_unit'] = target_raw

            self.show_properties(mat, self.material_database)
        except Exception as e:
            messagebox.showerror("Error", f"Conversion failed: {e}")

    @staticmethod
    def _sanitize_unit(unit_str):
        """
        Robustly formats unit strings for Pint.
        - Converts 'C', 'degC', '°C' -> 'delta_degC' (CRITICAL for valid math)
        - Replaces '-' or '.' with '*'
        - Groups denominator with parentheses
        """
        if not unit_str or unit_str == '-':
            return 'dimensionless'

        # 1. Standardize separators
        # 'microJ/mm-degC' -> 'microJ/mm*degC'
        s = unit_str.replace('-', '*').replace('·', '*').replace('.', '*')

        # 2. Split into Numerator/Denominator
        if '/' in s:
            parts = s.split('/', 1)
            num = parts[0]
            den = parts[1]
        else:
            num = s
            den = ""

        # 3. Helper to fix Temperature Units

        def fix_temp(text):
            # Replace 'C', 'degC', '°C' with 'delta_degC'
            # We use \b (word boundaries) to avoid replacing inside words
            # But we must allow for the case where it ends the string or hits a symbol

            # Step A: Normalize all forms to 'degC' first
            text = re.sub(r'\bC\b', 'degC', text)
            text = text.replace('°C', 'degC')

            # Step B: Convert 'degC' to 'delta_degC' for Pint compatibility
            text = text.replace('degC', 'delta_degC')

            # Step C: Fix Kelvin (K is usually fine, but delta_K is safer if mixed)
            # text = re.sub(r'\bK\b', 'delta_K', text)
            return text

        # 4. Apply fixes
        num = fix_temp(num)

        if den:
            den = fix_temp(den)

            # 5. Apply Parentheses to Denominator
            # If denominator has multiplication, wrap it: (mm*delta_degC)
            if '*' in den and not den.strip().startswith('('):
                den = f"({den})"

            return f"{num}/{den}"

        return num


if __name__ == "__main__":
    win = Tk()
    win.title("Material Manager Pro")
    win.geometry("1200x800")
    # 1. Define the path to your XML library
    path = "C:/Users/Luca_Lombardi/Documents/My Python/TNSolvergui/Documentation/physicalmateriallibrary.xml"

    # 2. Define an empty initial materials dictionary
    initial_materials = {}

    # 3. Define a dummy callback function
    def dummy_callback():
        print("Material database updated in main program.")

    # 4. Correct the MaterialManager call with all required arguments
    # Arguments: parent, material_dict, update_material_callback, xml_file_path
    app = MaterialManager(win, initial_materials, dummy_callback, xml_file_path=path)

    app.pack(fill='both', expand=True)
    win.mainloop()
