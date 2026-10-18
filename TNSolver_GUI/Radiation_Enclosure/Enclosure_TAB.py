"""
Class RadiationEnclosureManager
GUI module to manage radiation enclosures defined on thermal network nodes.
Provides view factor matrix editing, reciprocity checks, matrix normalization,
and dual-mode radiation network injection into TNSolverGUI.

Luca Lombardi
01 Sep 2026: First Draft
08 Oct 2026: Added dual injection mode (Enclosure Block & Explicit Gebhart Branches)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import scipy.optimize as opt
from TNSolver_GUI.Thermal_Network_TAB.progress_window import Terminal, LogManager


class RadiationEnclosureManager(ttk.Frame):
    def __init__(self, parent, main_network_ref=None, enclosure_dict=None, log_manager=None):
        """
        :param parent: Notebook tab container
        :param main_network_ref: Reference to ThermalNetwork instance
        :param enclosure_dict: Reference to master enclosure dictionary in MainApplication
        :param log_manager: Central LogManager instance for terminal synchronisation
        """
        super().__init__(parent)
        self.main_network_ref = main_network_ref

        # Centralized Enclosure Data Dictionary (shared with MainApplication)
        if enclosure_dict is not None:
            self.enclosure_dict = enclosure_dict
        else:
            self.enclosure_dict = {}

        self.log_manager = log_manager

        # Local UI state / active working copy
        self.enclosures = {}
        self.active_enclosure = None
        self.matrix_entries = []

        self._build_ui()

        # Sync from network canvas whenever this tab becomes active
        self.bind("<Visibility>", lambda e: self.sync_from_network())

    def logger(self, msg, level="INFO"):
        """Central logging helper routing through LogManager."""
        if hasattr(self, 'log_manager') and hasattr(self.log_manager, 'write_text'):
            self.log_manager.write_text(msg, level)
        else:
            print(f"[{level}] {msg}")

    def _build_ui(self):
        # Main split container (Vertical to hold content above, terminal below)
        v_paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        v_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Main split container
        main_paned = ttk.PanedWindow(v_paned, orient=tk.HORIZONTAL)
        v_paned.add(main_paned, weight=3)

        # ------------------------------------------------------------------
        # LEFT FRAME: Enclosure & Surface Management
        # ------------------------------------------------------------------
        left_frame = ttk.LabelFrame(main_paned, text="Enclosure Setup", padding=5)
        main_paned.add(left_frame, weight=1)

        # Enclosure selector
        select_frame = ttk.Frame(left_frame)
        select_frame.pack(fill=tk.X, pady=5)

        ttk.Label(select_frame, text="Active Enclosure:").pack(side=tk.LEFT, padx=2)
        self.combo_enclosures = ttk.Combobox(select_frame, state="readonly")
        self.combo_enclosures.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self.combo_enclosures.bind("<<ComboboxSelected>>", self._on_enclosure_selected)

        ttk.Button(select_frame, text="+", width=3, command=self.add_enclosure).pack(side=tk.LEFT, padx=2)
        ttk.Button(select_frame, text="-", width=3, command=self.delete_enclosure).pack(side=tk.LEFT, padx=2)
        ttk.Button(select_frame, text="↻", width=3, command=self.sync_from_network).pack(side=tk.LEFT, padx=2)

        # Surface Treeview
        ttk.Label(left_frame, text="Participating Surface Nodes:").pack(anchor=tk.W, pady=(10, 2))

        self.surface_tree = ttk.Treeview(
            left_frame,
            columns=("node_id", "area", "emissivity", "geometry"),
            show="headings",
            height=8
        )
        self.surface_tree.heading("node_id", text="Node ID")
        self.surface_tree.heading("area", text="Area [m²]")
        self.surface_tree.heading("emissivity", text="Eps (ε)")
        self.surface_tree.heading("geometry", text="Geometry")

        self.surface_tree.column("node_id", width=80, anchor=tk.CENTER)
        self.surface_tree.column("area", width=80, anchor=tk.CENTER)
        self.surface_tree.column("emissivity", width=80, anchor=tk.CENTER)
        self.surface_tree.column("geometry", width=90, anchor=tk.CENTER)
        self.surface_tree.pack(fill=tk.BOTH, expand=True, pady=2)

        # Bind double click for inline editing
        self.surface_tree.bind("<Double-1>", self._on_tree_double_click)

        # Surface action buttons
        surf_btn_frame = ttk.Frame(left_frame)
        surf_btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(surf_btn_frame, text="Add Nodes", command=self.add_nodes_to_enclosure).pack(
            side=tk.LEFT, expand=True, fill=tk.X, padx=2
        )
        ttk.Button(surf_btn_frame, text="Remove Selected", command=self.remove_selected_node).pack(
            side=tk.LEFT, expand=True, fill=tk.X, padx=2
        )

        # ------------------------------------------------------------------
        # RIGHT FRAME: View Factor Matrix & Network Construction
        # ------------------------------------------------------------------
        right_frame = ttk.LabelFrame(main_paned, text="View Factor Matrix (F_ij)", padding=5)
        main_paned.add(right_frame, weight=2)

        # Container for dynamic View Factor Matrix Grid
        self.matrix_container = ttk.Frame(right_frame)
        self.matrix_container.pack(fill=tk.BOTH, expand=True, pady=5)

        # Action bar for Matrix validation
        matrix_actions = ttk.Frame(right_frame)
        matrix_actions.pack(fill=tk.X, pady=5)

        ttk.Button(matrix_actions, text="Check Reciprocity", command=self.check_reciprocity).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            matrix_actions, text="Normalize Matrix", command=self.normalize_matrix
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            matrix_actions, text="Auto Complete Matrix", command=self.auto_complete_matrix
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            matrix_actions, text="Validate Geometry", command=self.validate_geometry
        ).pack(side=tk.LEFT, padx=5)

        # Build Network Injection Controls
        build_frame = ttk.LabelFrame(right_frame, text="Thermal Network Builder", padding=5)
        build_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(build_frame, text="Radiation Method:", font=('Helvetica', 9, 'bold')).pack(anchor=tk.W, pady=(2, 2))
        self.net_model_var = tk.StringVar(value="Gebhart")
        ttk.Radiobutton(
            build_frame,
            text="Oppenheim Radiosity Method (Surface + Space Resistors)",
            variable=self.net_model_var,
            value="Oppenheim",
            state="disabled"
        ).pack(anchor=tk.W, padx=5)
        ttk.Radiobutton(
            build_frame,
            text="Direct Gebhart Matrix Method",
            variable=self.net_model_var,
            value="Gebhart"
        ).pack(anchor=tk.W, padx=5)

        ttk.Separator(build_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=6)

        ttk.Label(build_frame, text="Injection Target & Format:", font=('Helvetica', 9, 'bold')).pack(anchor=tk.W, pady=(2, 2))
        self.injection_mode_var = tk.StringVar(value="block")

        rb_block = ttk.Radiobutton(
            build_frame,
            text="Enclosure Block in Input File (Backward Compatible)",
            variable=self.injection_mode_var,
            value="block"
        )
        rb_block.pack(anchor=tk.W, padx=5)

        rb_branches = ttk.Radiobutton(
            build_frame,
            text="Explicit Gebhart Conductors into Thermal Network Graph",
            variable=self.injection_mode_var,
            value="branches"
        )
        rb_branches.pack(anchor=tk.W, padx=5)

        # Enclosure network controls
        injection_buttons = ttk.Frame(build_frame)
        injection_buttons.pack(fill=tk.X, pady=(8, 5))
        injection_buttons.columnconfigure(0, weight=1)
        injection_buttons.columnconfigure(1, weight=1)

        self.btn_inject = ttk.Button(
            injection_buttons, text="Inject Enclosure",
            command=self.inject_enclosure, state="disabled"
        )
        self.btn_inject.grid(row=0, column=0, sticky="ew", padx=(0, 2), pady=2)

        self.btn_remove = ttk.Button(
            injection_buttons, text="Remove Enclosure (from Network)",
            command=self.remove_enclosure_from_network, state="disabled"
        )
        self.btn_remove.grid(row=0, column=1, sticky="ew", padx=(2, 0), pady=2)

        self.btn_inject_all = ttk.Button(
            injection_buttons, text="Inject All Enclosures",
            command=self.inject_all_enclosures, state="disabled"
        )
        self.btn_inject_all.grid(row=1, column=0, sticky="ew", padx=(0, 2), pady=2)

        self.btn_remove_all = ttk.Button(
            injection_buttons, text="Remove All Enclosures",
            command=self.remove_all_enclosures, state="disabled"
        )
        self.btn_remove_all.grid(row=1, column=1, sticky="ew", padx=(2, 0), pady=2)

        # ------------------------------------------------------------------
        # BOTTOM FRAME: Local Terminal View
        # ------------------------------------------------------------------
        self.local_terminal = Terminal(v_paned)
        v_paned.add(self.local_terminal, weight=1)

        # Register this terminal with the global LogManager passed in __init__
        if self.log_manager:
            self.log_manager.register(self.local_terminal)

    # ------------------------------------------------------------------
    # INLINE TREEVIEW EDITING LOGIC
    # ------------------------------------------------------------------
    def _on_tree_double_click(self, event):
        """Open an inline editor for area, emissivity, or surface geometry."""
        if not self.active_enclosure or self.active_enclosure not in self.enclosures:
            return

        region = self.surface_tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        column = self.surface_tree.identify_column(event.x)
        col_idx = int(column[1:]) - 1
        if col_idx not in (1, 2, 3):
            return

        selected_iid = self.surface_tree.identify_row(event.y)
        if not selected_iid:
            return
        self.surface_tree.focus(selected_iid)
        self.surface_tree.selection_set(selected_iid)

        item_values = self.surface_tree.item(selected_iid, "values")
        node_id = item_values[0]
        current_val = item_values[col_idx]
        cell_bbox = self.surface_tree.bbox(selected_iid, column)
        if not cell_bbox:
            return

        if col_idx == 3:
            editor = ttk.Combobox(
                self.surface_tree,
                values=("Convex", "Concave"),
                state="readonly"
            )
            editor.set(current_val if current_val in ("Convex", "Concave") else "Convex")
        else:
            editor = ttk.Entry(self.surface_tree)
            editor.insert(0, current_val)
            editor.select_range(0, tk.END)

        editor.place(
            x=cell_bbox[0], y=cell_bbox[1],
            w=cell_bbox[2], h=cell_bbox[3]
        )
        editor.focus_set()

        saved = {"done": False}

        def save_once(_event=None):
            if saved["done"]:
                return
            saved["done"] = True
            self._save_cell_edit(editor, node_id, col_idx)

        editor.bind("<Return>", save_once)
        editor.bind("<FocusOut>", save_once)
        editor.bind("<Escape>", lambda _event: editor.destroy())
        if col_idx == 3:
            editor.bind("<<ComboboxSelected>>", save_once)

    def _save_cell_edit(self, entry_widget, node_id, col_idx):
        """Validate and apply area, emissivity, or geometry edits."""
        new_text = entry_widget.get().strip()
        entry_widget.destroy()

        enc_data = self.enclosures[self.active_enclosure]
        self._ensure_geometry_data(enc_data)
        if node_id not in enc_data["surfaces"]:
            return
        idx = enc_data["surfaces"].index(node_id)

        if col_idx == 3:
            geometry = new_text.capitalize()

            if geometry not in ("Convex", "Concave"):
                messagebox.showerror(
                    "Error",
                    "Geometry must be Convex or Concave."
                )
                return

            enc_data["geometry"][idx] = geometry

            live_nodes = self.get_available_nodes()
            node_key = int(node_id) if str(node_id).isdigit() else node_id
            node_obj = live_nodes.get(node_key)

            if node_obj is not None:
                node_obj.node_surface_geometry = geometry

            if geometry == "Convex" and enc_data["F"].shape[0] > idx:
                enc_data["F"][idx, idx] = 0.0

            self.invalidate_verification()
            self.refresh_surface_list()
            self.refresh_matrix_grid()
            return

        try:
            val = float(new_text)
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid numeric value.")
            return

        if col_idx == 1:
            if val <= 0.0:
                messagebox.showerror("Error", "Area must be a positive number.")
                return
            enc_data["areas"][idx] = val
            live_nodes = self.get_available_nodes()
            key = int(node_id) if str(node_id).isdigit() else node_id
            node_obj = live_nodes.get(key)
            if node_obj:
                if hasattr(node_obj, "node_area") and isinstance(node_obj.node_area, list):
                    node_obj.node_area[0] = val
                else:
                    setattr(node_obj, "node_area", val)
        elif col_idx == 2:
            if not 0.0 <= val <= 1.0:
                messagebox.showerror("Error", "Emissivity (ε) must be between 0.0 and 1.0.")
                return
            enc_data["eps"][idx] = val

        self.invalidate_verification()
        self.refresh_surface_list()
        self.refresh_matrix_grid()

    # ------------------------------------------------------------------
    # ENCLOSURE & NODE INTEGRATION LOGIC
    # ------------------------------------------------------------------
    def get_available_nodes(self):
        """Safely retrieves current node references from the main ThermalNetwork instance."""
        if self.main_network_ref is not None and hasattr(self.main_network_ref, "node_dict"):
            return self.main_network_ref.node_dict
        return {}

    def sync_from_network(self):
        """Scans all nodes in main_network_ref, grouping nodes into corresponding enclosures."""
        live_nodes = self.get_available_nodes()
        if not live_nodes:
            return

        detected_groups = {}
        for n_id, node in live_nodes.items():
            enc_id = getattr(node, 'node_enclosure_id', None)
            if enc_id and str(enc_id).strip().lower() not in ['none', '', '0']:
                enc_id = str(enc_id).strip()
                detected_groups.setdefault(enc_id, []).append(node)

        for enc_id, nodes in detected_groups.items():
            if enc_id not in self.enclosures:
                self.enclosures[enc_id] = {
                    "surfaces": [],
                    "areas": [],
                    "eps": [],
                    "geometry": [],
                    "F": np.empty((0, 0)),
                    "is_verified": False
                }

            enc = self.enclosures[enc_id]
            self._ensure_geometry_data(enc)
            if "eps" not in enc and "emissivities" in enc:
                enc["eps"] = enc.pop("emissivities")
            if "F" not in enc:
                raw_matrix = enc.get("view_factors", np.empty((0, 0)))
                enc["F"] = np.array(raw_matrix, dtype=float) if len(raw_matrix) > 0 else np.empty((0, 0))

            existing_ids = set(str(n) for n in enc["surfaces"])

            for node in nodes:
                str_id = str(node.node_ID)
                if str_id not in existing_ids:
                    raw_area = getattr(node, "node_area", 1.0)
                    area_val = raw_area[0] if isinstance(raw_area, (list, tuple)) else raw_area
                    try:
                        area_val = float(area_val)
                    except (ValueError, TypeError):
                        area_val = 1.0

                    enc["surfaces"].append(str_id)
                    enc["areas"].append(area_val)
                    enc["eps"].append(0.85)
                    geometry = getattr(
                        node,
                        "node_surface_geometry",
                        "Convex"
                    )

                    if geometry not in ("Convex", "Concave"):
                        geometry = "Convex"

                    enc.setdefault("geometry", []).append(geometry)

            self._resize_matrix(enc_id)

        names = list(self.enclosures.keys())
        self.combo_enclosures['values'] = names

        if names:
            if not self.active_enclosure or self.active_enclosure not in self.enclosures:
                self.combo_enclosures.set(names[0])
                self.active_enclosure = names[0]
            else:
                self.combo_enclosures.set(self.active_enclosure)

            self.refresh_surface_list()
            self.refresh_matrix_grid()

    @staticmethod
    def _ensure_geometry_data(enc):
        """Upgrade legacy enclosure dictionaries with per-surface geometry."""
        count = len(enc.get("surfaces", []))
        geometry = enc.setdefault("geometry", [])
        geometry[:] = [
            value if value in ("Convex", "Concave") else "Convex"
            for value in geometry[:count]
        ]
        if len(geometry) < count:
            geometry.extend(["Convex"] * (count - len(geometry)))

    def _resize_matrix(self, enc_id):
        """Resizes View Factor Matrix while retaining existing entries."""
        enc = self.enclosures[enc_id]

        if "F" not in enc:
            raw_matrix = enc.get("view_factors", np.empty((0, 0)))
            enc["F"] = np.array(raw_matrix, dtype=float) if len(raw_matrix) > 0 else np.empty((0, 0))

        surfaces = enc["surfaces"]
        new_n = len(surfaces)
        old_n = enc["F"].shape[0] if enc["F"].ndim == 2 else 0

        if new_n == old_n:
            return

        new_F = np.zeros((new_n, new_n))
        if old_n > 0:
            min_n = min(old_n, new_n)
            new_F[:min_n, :min_n] = enc["F"][:min_n, :min_n]

        for i in range(new_n):
            for j in range(new_n):
                if i != j and new_F[i, j] == 0.0:
                    new_F[i, j] = 1.0 / max(1, new_n - 1)

        enc["F"] = new_F

    def delete_enclosure(self):
        selected = self.combo_enclosures.get()
        if (selected and self.main_network_ref is not None and
                hasattr(self.main_network_ref, "remove_auto_generated_elements")):
            removed_count = (self.main_network_ref.remove_auto_generated_elements(selected))

            if removed_count:
                self.logger(f"Removed {removed_count} generated radiation elements "
                            f"for enclosure '{selected}'.", "INFO")
        if selected in self.enclosures:
            del self.enclosures[selected]
            if selected in self.enclosure_dict:
                del self.enclosure_dict[selected]
            names = list(self.enclosures.keys())
            self.combo_enclosures['values'] = names
            if names:
                self.combo_enclosures.set(names[0])
                self.active_enclosure = names[0]
                self._on_enclosure_selected()
            else:
                self.combo_enclosures.set("")
                self.active_enclosure = None
                self._clear_views()

    def _on_enclosure_selected(self, event=None):
        self.active_enclosure = self.combo_enclosures.get()
        self.refresh_surface_list()
        self.refresh_matrix_grid()
        self.update_inject_button_state()

    def refresh_surface_list(self):
        for item in self.surface_tree.get_children():
            self.surface_tree.delete(item)
        if not self.active_enclosure:
            return

        data = self.enclosures[self.active_enclosure]
        self._ensure_geometry_data(data)
        for node, area, emissivity, geometry in zip(
                data["surfaces"], data["areas"], data["eps"], data["geometry"]):
            self.surface_tree.insert(
                "", tk.END,
                values=(node, area, emissivity, geometry)
            )

    def refresh_matrix_grid(self):
        """Rebuild the view-factor grid; concave diagonal cells are editable."""
        for child in self.matrix_container.winfo_children():
            child.destroy()
        if not self.active_enclosure or self.active_enclosure not in self.enclosures:
            return

        data = self.enclosures[self.active_enclosure]
        self._ensure_geometry_data(data)
        surfaces = data["surfaces"]
        n = len(surfaces)
        if n == 0:
            return

        ttk.Label(
            self.matrix_container, text="F(i,j)",
            font=('Helvetica', 9, 'bold')
        ).grid(row=0, column=0, padx=4, pady=4)
        for j, surface_name in enumerate(surfaces):
            ttk.Label(
                self.matrix_container, text=str(surface_name),
                font=('Helvetica', 9, 'bold')
            ).grid(row=0, column=j + 1, padx=4, pady=4)
        ttk.Label(
            self.matrix_container, text="Row Sum",
            font=('Helvetica', 9, 'bold')
        ).grid(row=0, column=n + 1, padx=8, pady=4)

        self.matrix_entries = []
        for i in range(n):
            row_entries = []
            ttk.Label(
                self.matrix_container, text=str(surfaces[i]),
                font=('Helvetica', 9, 'bold')
            ).grid(row=i + 1, column=0, padx=4, pady=4)

            for j in range(n):
                entry = ttk.Entry(self.matrix_container, width=8, justify="center")
                entry.insert(0, f"{data['F'][i, j]:.4f}")
                if i == j and data["geometry"][i] == "Convex":
                    entry.config(state="disabled")
                else:
                    entry.bind(
                        "<FocusOut>",
                        lambda ev, row=i, col=j, widget=entry:
                        self._on_matrix_cell_edit(row, col, widget)
                    )
                    entry.bind(
                        "<Return>",
                        lambda ev, row=i, col=j, widget=entry:
                        self._on_matrix_cell_edit(row, col, widget)
                    )
                entry.grid(row=i + 1, column=j + 1, padx=2, pady=2)
                row_entries.append(entry)

            row_sum = float(np.sum(data["F"][i, :]))
            sum_label = ttk.Label(self.matrix_container, text=f"{row_sum:.3f}")
            sum_label.config(
                foreground="green" if np.isclose(row_sum, 1.0, atol=1e-2) else "red"
            )
            sum_label.grid(row=i + 1, column=n + 1, padx=8, pady=4)
            self.matrix_entries.append(row_entries)

    def _on_matrix_cell_edit(self, row, col, entry_widget):
        if not self.active_enclosure or self.active_enclosure not in self.enclosures:
            return

        val_str = entry_widget.get()
        try:
            val = float(val_str)
            if 0.0 <= val <= 1.0:
                old_val = self.enclosures[self.active_enclosure]["F"][row, col]
                if not np.isclose(old_val, val):
                    self.enclosures[self.active_enclosure]["F"][row, col] = val
                    self.invalidate_verification()
                    self.refresh_matrix_grid()
            else:
                entry_widget.delete(0, tk.END)
                entry_widget.insert(0, f"{self.enclosures[self.active_enclosure]['F'][row, col]:.4f}")
        except ValueError:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, f"{self.enclosures[self.active_enclosure]['F'][row, col]:.4f}")

    def add_nodes_to_enclosure(self):
        if not self.active_enclosure:
            messagebox.showwarning("Warning", "Please select or create an enclosure first.")
            return

        live_nodes = self.get_available_nodes()
        if not live_nodes:
            messagebox.showinfo("No Nodes", "No thermal nodes available in the Thermal Network tab.")
            return

        enc_data = self.enclosures[self.active_enclosure]
        current_node_ids = set(str(n) for n in enc_data["surfaces"])
        available_ids = [str(n_id) for n_id in live_nodes.keys() if str(n_id) not in current_node_ids]

        if not available_ids:
            messagebox.showinfo("Info", "All existing project nodes are already in this enclosure.")
            return

        dlg = tk.Toplevel(self)
        dlg.title("Add Surface Nodes")
        dlg.geometry("300x350")
        dlg.grab_set()

        ttk.Label(dlg, text="Select Node IDs to include:").pack(anchor=tk.W, padx=10, pady=5)

        frame = ttk.Frame(dlg)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        sb = ttk.Scrollbar(frame)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        lb = tk.Listbox(frame, selectmode=tk.MULTIPLE, yscrollcommand=sb.set)
        for n_id in available_ids:
            lb.insert(tk.END, n_id)
        lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.config(command=lb.yview)

        def on_add():
            selected_indices = lb.curselection()
            if not selected_indices:
                dlg.destroy()
                return

            added_nodes = [available_ids[i] for i in selected_indices]
            for n_id in added_nodes:
                node_obj = live_nodes.get(int(n_id) if n_id.isdigit() else n_id)
                raw_area = getattr(node_obj, "node_area", 1.0) if node_obj else 1.0
                area_val = raw_area[0] if isinstance(raw_area, (list, tuple)) else raw_area

                if node_obj:
                    setattr(node_obj, 'node_enclosure_id', self.active_enclosure)

                enc_data["surfaces"].append(n_id)
                enc_data["areas"].append(float(area_val) if area_val is not None else 1.0)
                enc_data["eps"].append(0.85)
                geometry = getattr(
                    node_obj,
                    "node_surface_geometry",
                    "Convex"
                )

                enc_data.setdefault("geometry", []).append(geometry)

                if node_obj is not None:
                    node_obj.node_surface_geometry = geometry

            self._resize_matrix(self.active_enclosure)
            self.refresh_surface_list()
            self.refresh_matrix_grid()
            dlg.destroy()

        btn_bar = ttk.Frame(dlg)
        btn_bar.pack(fill=tk.X, pady=10)
        ttk.Button(btn_bar, text="Add", command=on_add).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_bar, text="Cancel", command=dlg.destroy).pack(side=tk.RIGHT, padx=5)

    def remove_selected_node(self):
        if not self.active_enclosure:
            return

        selected_item = self.surface_tree.selection()
        if not selected_item:
            return

        item_values = self.surface_tree.item(selected_item[0], "values")
        node_id = item_values[0]

        enc_data = self.enclosures[self.active_enclosure]
        if node_id in enc_data["surfaces"]:
            idx = enc_data["surfaces"].index(node_id)
            self._ensure_geometry_data(enc_data)
            enc_data["surfaces"].pop(idx)
            enc_data["areas"].pop(idx)
            enc_data["eps"].pop(idx)
            enc_data["geometry"].pop(idx)

            enc_data["F"] = np.delete(np.delete(enc_data["F"], idx, axis=0), idx, axis=1)

            live_nodes = self.get_available_nodes()
            node_obj = live_nodes.get(int(node_id) if node_id.isdigit() else node_id)
            if node_obj:
                node_obj.node_enclosure_id = "None"
                node_obj.node_surface_geometry = "Convex"

            self.refresh_surface_list()
            self.refresh_matrix_grid()

    # ------------------------------------------------------------------
    # MATRIX CALCULATIONS & GEBHART SOLVER
    # ------------------------------------------------------------------
    def compute_gebhart_matrix(self, F, eps):
        """
        Computes the Gebhart factor matrix B_ij using diffuse radiation theory:
        B = (I - F * (I - E))^-1 * F * E
        """
        n = len(eps)
        if n == 0 or F.shape != (n, n):
            return np.empty((0, 0))

        I = np.eye(n)
        E_diag = np.diag(eps)
        I_minus_E = np.diag(1.0 - np.array(eps))

        M = I - np.dot(F, I_minus_E)
        try:
            B = np.linalg.solve(M, np.dot(F, E_diag))
            return B
        except np.linalg.LinAlgError:
            self.logger("Linear system for Gebhart factors is singular.", "ERROR")
            return np.zeros((n, n))

    def check_reciprocity(self):
        """Validate bounds, closure, geometry, and A_i F_ij = A_j F_ji."""
        if not self.active_enclosure or self.active_enclosure not in self.enclosures:
            return

        data = self.enclosures[self.active_enclosure]
        self._ensure_geometry_data(data)
        A = np.asarray(data["areas"], dtype=float)
        F = np.asarray(data["F"], dtype=float)
        n = len(A)
        if n < 2 or F.shape != (n, n):
            self.logger("A valid matrix with at least two surfaces is required.", "WARNING")
            self.invalidate_verification()
            return

        errors = []
        if np.any(F < -1.0e-10) or np.any(F > 1.0 + 1.0e-10):
            errors.append("One or more view factors are outside [0, 1].")

        for i in range(n):
            row_sum = float(np.sum(F[i, :]))
            if not np.isclose(row_sum, 1.0, rtol=1e-4, atol=1e-6):
                errors.append(
                    f"Surface {data['surfaces'][i]}: row sum={row_sum:.6f}, expected 1.0."
                )
            if data["geometry"][i] == "Convex" and not np.isclose(
                    F[i, i], 0.0, atol=1e-8):
                errors.append(
                    f"Surface {data['surfaces'][i]} is Convex but F_ii={F[i, i]:.6f}."
                )

        for i in range(n):
            for j in range(i + 1, n):
                q_ij = A[i] * F[i, j]
                q_ji = A[j] * F[j, i]
                if not np.isclose(q_ij, q_ji, rtol=1e-3, atol=1e-5):
                    required_f_ji = q_ij / A[j] if A[j] > 0.0 else np.nan
                    errors.append(
                        f"Pair ({data['surfaces'][i]}, {data['surfaces'][j]}): "
                        f"A_i*F_ij={q_ij:.6f} != A_j*F_ji={q_ji:.6f}; "
                        f"reciprocity requires F_ji={required_f_ji:.6f}."
                    )

        if errors:
            self.logger(
                f"Physical consistency check failed for '{self.active_enclosure}':",
                "WARNING"
            )
            for error in errors:
                self.logger(f"  -> {error}", "WARNING")
            self.logger(
                "Use Auto Complete Matrix or mark a self-viewing surface as Concave.",
                "INFO"
            )
            self.invalidate_verification()
            return

        data["is_verified"] = True
        self.logger(
            f"Physical consistency check passed for '{self.active_enclosure}'.",
            "SUCCESS"
        )
        self.update_inject_button_state()

    def enforce_convex_surfaces(self, enc_id):
        """Ensures no self-view factors exist for flat/convex surface nodes."""
        enc = self.enclosures[enc_id]
        np.fill_diagonal(enc["F"], 0.0)

    def normalize_matrix(self):
        """Find the closest physical matrix subject to closure and reciprocity."""
        if not self.active_enclosure or self.active_enclosure not in self.enclosures:
            self.logger("Select an enclosure before normalizing.", "WARNING")
            return

        data = self.enclosures[self.active_enclosure]
        self._ensure_geometry_data(data)
        F_init = np.asarray(data["F"], dtype=float).copy()
        A = np.asarray(data["areas"], dtype=float)
        n = len(A)
        if n < 2 or F_init.shape != (n, n):
            self.logger("A valid matrix with at least two surfaces is required.", "WARNING")
            return

        x0 = np.clip(F_init.flatten(), 0.0, 1.0)

        def objective(x):
            return np.sum((x - x0) ** 2)

        constraints = []
        for i, geometry in enumerate(data["geometry"]):
            if geometry == "Convex":
                constraints.append({
                    'type': 'eq',
                    'fun': lambda x, idx=i: x[idx * n + idx]
                })
        for i in range(n):
            constraints.append({
                'type': 'eq',
                'fun': lambda x, row=i: np.sum(x[row * n:(row + 1) * n]) - 1.0
            })
        for i in range(n):
            for j in range(i + 1, n):
                constraints.append({
                    'type': 'eq',
                    'fun': lambda x, r=i, c=j:
                    A[r] * x[r * n + c] - A[c] * x[c * n + r]
                })

        result = opt.minimize(
            objective,
            x0,
            method="SLSQP",
            bounds=[(0.0, 1.0)] * (n * n),
            constraints=constraints,
            options={'maxiter': 1000, 'ftol': 1e-10}
        )

        if not result.success:
            self.logger(
                f"Normalization failed for '{self.active_enclosure}': {result.message}. "
                "Check surface geometry or add missing enclosure surfaces.",
                "ERROR"
            )
            self.invalidate_verification()
            return

        data["F"] = result.x.reshape((n, n))
        for i, geometry in enumerate(data["geometry"]):
            if geometry == "Convex":
                data["F"][i, i] = 0.0
        self.invalidate_verification()
        self.refresh_matrix_grid()
        self.logger(
            f"Normalized enclosure '{self.active_enclosure}' with closure, "
            "reciprocity, bounds, and geometry constraints.",
            "SUCCESS"
        )
        self.check_reciprocity()

    def auto_complete_matrix(self):
        """Compute the nearest physical view-factor matrix and infer concavity."""
        if not self.active_enclosure or self.active_enclosure not in self.enclosures:
            self.logger("Select an enclosure before auto-completing.", "WARNING")
            return

        data = self.enclosures[self.active_enclosure]
        self._ensure_geometry_data(data)
        A = np.asarray(data["areas"], dtype=float)
        F_initial = np.asarray(data["F"], dtype=float)
        n = len(A)
        if n < 2 or F_initial.shape != (n, n) or np.any(A <= 0.0):
            self.logger("Positive areas and a valid square matrix are required.", "ERROR")
            return

        # First try with the geometry selected by the user.
        self.normalize_matrix()
        if data.get("is_verified", False):
            return

        # If infeasible, progressively allow self-view on surfaces whose rows
        # cannot close while reciprocity is maintained. For two surfaces this
        # identifies the larger surface automatically.
        original_geometry = list(data["geometry"])
        candidates = sorted(range(n), key=lambda idx: A[idx], reverse=True)
        for idx in candidates:
            data["geometry"][idx] = "Concave"
            self.normalize_matrix()
            if data.get("is_verified", False):
                changed = [
                    str(data["surfaces"][k]) for k in range(n)
                    if original_geometry[k] != data["geometry"][k]
                ]
                if changed:
                    self.logger(
                        "Auto Complete inferred Concave geometry for surface(s): "
                        + ", ".join(changed),
                        "INFO"
                    )
                self.refresh_surface_list()
                return

        data["geometry"] = original_geometry
        data["F"] = F_initial.copy()
        self.invalidate_verification()
        self.refresh_surface_list()
        self.refresh_matrix_grid()
        self.logger(
            "Auto Complete could not find a physical matrix. Add missing enclosure "
            "surfaces or review the entered view factors.",
            "ERROR"
        )

    def validate_geometry(self):
        """Report whether self-view factors agree with Convex/Concave settings."""
        if not self.active_enclosure or self.active_enclosure not in self.enclosures:
            return False

        data = self.enclosures[self.active_enclosure]
        self._ensure_geometry_data(data)
        F = np.asarray(data["F"], dtype=float)
        valid = True
        for i, surface in enumerate(data["surfaces"]):
            self_view = F[i, i]
            geometry = data["geometry"][i]
            if geometry == "Convex" and not np.isclose(self_view, 0.0, atol=1e-8):
                self.logger(
                    f"Surface {surface}: Convex requires F_ii=0, found {self_view:.6f}.",
                    "WARNING"
                )
                valid = False
            elif geometry == "Concave" and self_view <= 1.0e-8:
                self.logger(
                    f"Surface {surface}: Concave is allowed, but F_ii is zero. "
                    "This is mathematically valid but should match the actual geometry.",
                    "INFO"
                )
            else:
                self.logger(
                    f"Surface {surface}: {geometry}, F_ii={self_view:.6f}, OK.",
                    "SUCCESS"
                )
        return valid

    def clear_matrix(self):
        """Resets the view factor matrix to uniform distribution."""
        if not self.active_enclosure or self.active_enclosure not in self.enclosures:
            return

        data = self.enclosures[self.active_enclosure]
        n = len(data["surfaces"])
        if n == 0:
            return

        new_F = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if i != j:
                    new_F[i, j] = 1.0 / max(1, n - 1)

        data["F"] = new_F
        self.invalidate_verification()
        self.refresh_matrix_grid()
        self.logger(f"Cleared view factor matrix for '{self.active_enclosure}'.", "INFO")

    # ------------------------------------------------------------------
    # INJECTION LOGIC (BLOCK VS EXPLICIT BRANCHES)
    # ------------------------------------------------------------------
    def inject_network(self):
        """Backward-compatible alias for injecting the active enclosure."""
        return self.inject_enclosure()

    def _is_enclosure_injected(self, enclosure_id):
        """Check block exports and live auto-generated radiation elements."""
        enclosure_id = str(enclosure_id)
        if any(str(key) == enclosure_id for key in self.enclosure_dict):
            return True
        network = self.main_network_ref
        if network is None:
            return False
        blocks = getattr(network, "enclosure_dict", {})
        if any(str(key) == enclosure_id for key in blocks):
            return True
        return any(
            getattr(element, "is_auto_generated", False)
            and str(getattr(element, "enclosure_id", "")) == enclosure_id
            for element in getattr(network, "elm_dict", {}).values()
        )

    def inject_enclosure(self):
        """Inject the active enclosure using the existing block/branch process."""
        enclosure_id = self.active_enclosure
        if not enclosure_id or enclosure_id not in self.enclosures:
            self.logger("No active enclosure to inject.", "WARNING")
            return False
        data = self.enclosures[enclosure_id]
        if not data.get("is_verified", False):
            self.logger(f"Enclosure '{enclosure_id}' is not verified.", "WARNING")
            return False
        if self._is_enclosure_injected(enclosure_id):
            self.logger(f"Enclosure '{enclosure_id}' is already injected; skipped.", "INFO")
            self.update_inject_button_state()
            return False
        surfaces = data.get("surfaces", [])
        areas = data.get("areas", [])
        emissivities = data.get("eps", [0.85] * len(surfaces))
        matrix = np.asarray(data.get("F", np.empty((0, 0))), dtype=float)
        if len(surfaces) < 2 or matrix.shape != (len(surfaces), len(surfaces)):
            self.logger(f"Enclosure '{enclosure_id}' has invalid surface or matrix data.", "ERROR")
            return False
        B_matrix = self.compute_gebhart_matrix(matrix, emissivities)
        mode = self.injection_mode_var.get()
        if mode == "block":
            success = self._inject_as_enclosure_block(
                data, surfaces, areas, emissivities, matrix, B_matrix
            )
        elif mode == "branches":
            success = self._inject_as_explicit_branches(
                surfaces, areas, emissivities, B_matrix
            )
        else:
            self.logger(f"Unknown injection mode '{mode}'.", "ERROR")
            return False
        self.update_inject_button_state()
        return bool(success)

    def remove_enclosure_from_network(self):
        """Remove active enclosure exports while retaining its definition."""
        enclosure_id = self.active_enclosure
        if not enclosure_id:
            self.logger("No active enclosure to remove.", "WARNING")
            return False
        removed_blocks = 0
        for key in list(self.enclosure_dict):
            if str(key) == str(enclosure_id):
                del self.enclosure_dict[key]
                removed_blocks += 1
        network = self.main_network_ref
        removed_elements = 0
        if network is not None:
            blocks = getattr(network, "enclosure_dict", None)
            if isinstance(blocks, dict) and blocks is not self.enclosure_dict:
                for key in list(blocks):
                    if str(key) == str(enclosure_id):
                        del blocks[key]
                        removed_blocks += 1
            if hasattr(network, "remove_auto_generated_elements"):
                removed_elements = network.remove_auto_generated_elements(enclosure_id)
        removed = removed_blocks > 0 or removed_elements > 0
        if removed:
            self.logger(
                f"Enclosure '{enclosure_id}' removed from the network: "
                f"{removed_blocks} block(s), {removed_elements} radiation element(s).",
                "SUCCESS"
            )
        else:
            self.logger(f"Enclosure '{enclosure_id}' is not present in the network.", "INFO")
        self.update_inject_button_state()
        return removed

    def inject_all_enclosures(self):
        """Inject all verified enclosures and skip existing exports."""
        original = self.active_enclosure
        counts = {"injected": 0, "existing": 0, "unverified": 0, "failed": 0}
        try:
            for enclosure_id, data in list(self.enclosures.items()):
                if not data.get("is_verified", False):
                    counts["unverified"] += 1
                    continue
                if self._is_enclosure_injected(enclosure_id):
                    counts["existing"] += 1
                    continue
                self.active_enclosure = enclosure_id
                if self.inject_enclosure():
                    counts["injected"] += 1
                else:
                    counts["failed"] += 1
        finally:
            self.active_enclosure = original
            if original in self.enclosures:
                self.combo_enclosures.set(original)
            self.update_inject_button_state()
        self.logger(
            "Inject All completed: {injected} injected, {existing} already present, "
            "{unverified} unverified, {failed} failed.".format(**counts),
            "SUCCESS" if counts["failed"] == 0 else "WARNING"
        )

    def remove_all_enclosures(self):
        """Remove all exports while keeping enclosure definitions."""
        original = self.active_enclosure
        removed = 0
        try:
            for enclosure_id in list(self.enclosures):
                if not self._is_enclosure_injected(enclosure_id):
                    continue
                self.active_enclosure = enclosure_id
                if self.remove_enclosure_from_network():
                    removed += 1
        finally:
            self.active_enclosure = original
            if original in self.enclosures:
                self.combo_enclosures.set(original)
            self.update_inject_button_state()
        self.logger(f"Remove All completed: {removed} enclosure(s) removed.", "SUCCESS")

    def _inject_as_enclosure_block(self, data, surfaces, areas, emissivities,
                                   F_matrix, B_matrix):
        """Export an enclosure block and report success."""
        block_payload = {
            "surfaces": surfaces,
            "areas": areas,
            "emissivities": emissivities,
            "geometry": data.get("geometry", ["Convex"] * len(surfaces)),
            "view_factors": F_matrix.tolist() if hasattr(F_matrix, "tolist") else F_matrix,
            "gebhart_factors": B_matrix.tolist() if hasattr(B_matrix, "tolist") else B_matrix,
            "model": self.net_model_var.get(),
            "injection_mode": "block"
        }
        self.enclosure_dict[self.active_enclosure] = block_payload
        if self.main_network_ref and hasattr(self.main_network_ref, "enclosure_dict"):
            self.main_network_ref.enclosure_dict[self.active_enclosure] = block_payload
        self.logger(
            f"Enclosure '{self.active_enclosure}' injected successfully as an enclosure block.",
            "SUCCESS"
        )
        return True

    def _inject_as_explicit_branches(self, surfaces, areas, emissivities, B_matrix):
        """Draw explicit Gebhart radiation elements in the main thermal network."""
        network = self.main_network_ref
        if network is None:
            self.logger("Main network reference not found.", "ERROR")
            return False
        if not hasattr(network, "add_auto_generated_radiation_element"):
            self.logger("Radiation-element injection interface not found.", "ERROR")
            return False
        n = len(surfaces)
        areas = np.asarray(areas, dtype=float)
        emissivities = np.asarray(emissivities, dtype=float)
        B_matrix = np.asarray(B_matrix, dtype=float)
        if areas.shape != (n,) or emissivities.shape != (n,) or B_matrix.shape != (n, n):
            self.logger("Invalid enclosure arrays for branch injection.", "ERROR")
            return False
        live_nodes = network.node_dict
        missing = [sid for sid in surfaces if self._resolve_node_id(sid, live_nodes) not in live_nodes]
        if missing:
            self.logger(f"Cannot inject enclosure; missing network nodes: {missing}", "ERROR")
            return False
        # Replacement is retained for direct calls; normal UI injection skips duplicates first.
        replaced = network.remove_auto_generated_elements(self.active_enclosure)
        added_ids = []
        try:
            pair_index = 0
            for i in range(n):
                for j in range(i + 1, n):
                    coupling_ij = areas[i] * emissivities[i] * B_matrix[i, j]
                    coupling_ji = areas[j] * emissivities[j] * B_matrix[j, i]
                    if not np.isclose(coupling_ij, coupling_ji, rtol=1e-3, atol=1e-10):
                        raise ValueError(
                            f"Gebhart reciprocity failed for surfaces {surfaces[i]} and {surfaces[j]}: "
                            f"{coupling_ij:.8e} != {coupling_ji:.8e}"
                        )
                    coupling = 0.5 * (coupling_ij + coupling_ji)
                    if coupling <= 1e-12:
                        continue
                    node_in = self._resolve_node_id(surfaces[i], live_nodes)
                    node_out = self._resolve_node_id(surfaces[j], live_nodes)
                    x, y = self._radiation_element_position(node_in, node_out, pair_index)
                    element = network.add_auto_generated_radiation_element(
                        node_in=node_in,
                        node_out=node_out,
                        exchange_factor=coupling / areas[i],
                        area=areas[i],
                        enclosure_id=self.active_enclosure,
                        x=x,
                        y=y
                    )
                    added_ids.append(element.elmID)
                    pair_index += 1
        except Exception as exc:
            network.remove_auto_generated_elements(self.active_enclosure)
            self.logger(
                f"Injection of enclosure '{self.active_enclosure}' failed and was rolled back: {exc}",
                "ERROR"
            )
            return False
        self.logger(
            f"Enclosure '{self.active_enclosure}' injected successfully into the main thermal network: "
            f"{len(added_ids)} radiation element(s) drawn"
            + (f", {replaced} previous element(s) replaced." if replaced else "."),
            "SUCCESS"
        )
        return True

    # ------------------------------------------------------------------
    # UI HELPERS & STATE MANAGEMENT
    # ------------------------------------------------------------------
    def _clear_views(self):
        for item in self.surface_tree.get_children():
            self.surface_tree.delete(item)
        for child in self.matrix_container.winfo_children():
            child.destroy()

    def invalidate_verification(self):
        """Invalidates reciprocity state and deactivates injection button."""
        if self.active_enclosure and self.active_enclosure in self.enclosures:
            self.enclosures[self.active_enclosure]["is_verified"] = False

            if self.active_enclosure in self.enclosure_dict:
                del self.enclosure_dict[self.active_enclosure]

        self.update_inject_button_state()

    def update_inject_button_state(self):
        """Update all four controls from verification and export status."""
        active_valid = self.active_enclosure in self.enclosures
        active_verified = bool(
            active_valid and self.enclosures[self.active_enclosure].get("is_verified", False)
        )
        active_injected = bool(
            active_valid and self._is_enclosure_injected(self.active_enclosure)
        )
        self.btn_inject.config(state="normal" if active_verified and not active_injected else "disabled")
        self.btn_remove.config(state="normal" if active_injected else "disabled")
        pending = any(
            data.get("is_verified", False) and not self._is_enclosure_injected(enc_id)
            for enc_id, data in self.enclosures.items()
        )
        exported = any(self._is_enclosure_injected(enc_id) for enc_id in self.enclosures)
        self.btn_inject_all.config(state="normal" if pending else "disabled")
        self.btn_remove_all.config(state="normal" if exported else "disabled")

    def add_enclosure(self):
        enc_id = f"Enclosure_{len(self.enclosures) + 1}"
        self.enclosures[enc_id] = {
            "surfaces": [],
            "areas": [],
            "eps": [],
            "geometry": [],
            "F": np.empty((0, 0)),
            "is_verified": False
        }
        self.combo_enclosures['values'] = list(self.enclosures.keys())
        self.combo_enclosures.set(enc_id)
        self.active_enclosure = enc_id
        self._on_enclosure_selected()

    @staticmethod
    def _resolve_node_id(node_id, node_dict):
        """Match enclosure string IDs to the actual node-dictionary key type."""
        if node_id in node_dict:
            return node_id

        if str(node_id).isdigit():
            numeric_id = int(node_id)
            if numeric_id in node_dict:
                return numeric_id

        return node_id

    def _radiation_element_position(self, node_in, node_out, pair_index):
        """
        Place the generated element near the midpoint of its two nodes.

        A perpendicular displacement separates multiple radiation elements
        connecting nearby node pairs.
        """
        first = self.main_network_ref.node_dict[node_in]
        second = self.main_network_ref.node_dict[node_out]

        dx = second.ctrX - first.ctrX
        dy = second.ctrY - first.ctrY
        length = float(np.hypot(dx, dy))

        midpoint_x = 0.5 * (first.ctrX + second.ctrX)
        midpoint_y = 0.5 * (first.ctrY + second.ctrY)

        if length <= 1.0e-12:
            return midpoint_x, midpoint_y

        offset_level = pair_index % 3
        offset_sign = -1 if pair_index % 2 else 1
        offset = offset_sign * offset_level * 18.0

        perpendicular_x = -dy / length
        perpendicular_y = dx / length

        return (
            midpoint_x + offset * perpendicular_x,
            midpoint_y + offset * perpendicular_y
        )
