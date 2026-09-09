"""
    Class RadiationEnclosureManager
    This GUI is designed to manage the radiation enclosures defined on the nodes
    It gives the possibility of defining the radiation factors anc check the matrices consistency

    Luca Lombardi
    01 Sep 2026: First Draft

    KNOWN ISSUES LIST
    -


"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import scipy.optimize as opt


class RadiationEnclosureManager(ttk.Frame):
    def __init__(self, parent, main_network_ref=None, enclosure_dict=None, logger_cb=None):
        """
        :param parent: Notebook tab container
        :param main_network_ref: Reference to ThermalNetwork instance
        :param enclosure_dict: Reference to master enclosure dictionary in MainApplication
        :param logger_cb: Callback method pointing to Terminal.write_text
        """
        super().__init__(parent)
        self.main_network_ref = main_network_ref

        # Centralized Enclosure Data Dictionary (shared with MainApplication)
        if enclosure_dict is not None:
            self.enclosure_dict = enclosure_dict
        else:
            self.enclosure_dict = {}

        # Local UI state / active working copy
        self.enclosures = {}
        self.active_enclosure = None
        self.matrix_entries = []

        # Terminal Logger Callback (fallback to print)
        self.logger = logger_cb if logger_cb is not None else lambda msg, level="INFO": print(f"[{level}] {msg}")

        self._build_ui()

        # Sync from network canvas whenever this tab becomes active
        self.bind("<Visibility>", lambda e: self.sync_from_network())

    def _build_ui(self):
        # Main split container
        main_paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

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
            columns=("node_id", "area", "emissivity"),
            show="headings",
            height=8
        )
        self.surface_tree.heading("node_id", text="Node ID")
        self.surface_tree.heading("area", text="Area [m²]")
        self.surface_tree.heading("emissivity", text="Eps (ε)")

        self.surface_tree.column("node_id", width=80, anchor=tk.CENTER)
        self.surface_tree.column("area", width=80, anchor=tk.CENTER)
        self.surface_tree.column("emissivity", width=80, anchor=tk.CENTER)
        self.surface_tree.pack(fill=tk.BOTH, expand=True, pady=2)

        # BIND DOUBLE CLICK FOR INLINE EDITING
        self.surface_tree.bind("<Double-1>", self._on_tree_double_click)

        # Surface action buttons
        surf_btn_frame = ttk.Frame(left_frame)
        surf_btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(surf_btn_frame, text="Add Nodes", command=self.add_nodes_to_enclosure).pack(side=tk.LEFT,
                                                                                               expand=True, fill=tk.X,
                                                                                               padx=2)
        ttk.Button(surf_btn_frame, text="Remove Selected", command=self.remove_selected_node).pack(side=tk.LEFT,
                                                                                                   expand=True,
                                                                                                   fill=tk.X, padx=2)
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
        ttk.Button(matrix_actions, text="Normalize Matrix (Sum = 1.0)", command=self.normalize_matrix).pack(
            side=tk.LEFT, padx=5)

        # Build Network Injection Controls
        build_frame = ttk.LabelFrame(right_frame, text="Thermal Network Builder", padding=5)
        build_frame.pack(fill=tk.X, pady=(10, 0))

        self.net_model_var = tk.StringVar(value="Oppenheim")
        ttk.Radiobutton(build_frame, text="Oppenheim Radiosity Method (Surface + Space Resistors)",
                        variable=self.net_model_var, value="Oppenheim").pack(anchor=tk.W)
        ttk.Radiobutton(build_frame, text="Direct Gebhart Matrix Method", variable=self.net_model_var,
                        value="Gebhart").pack(anchor=tk.W)

        ttk.Button(
            build_frame,
            text="Inject Radiation Network into Main Solver",
            command=self.inject_network
        ).pack(fill=tk.X, pady=5)

    # ------------------------------------------------------------------
    # INLINE TREEVIEW EDITING LOGIC
    # ------------------------------------------------------------------
    def _on_tree_double_click(self, event):
        """Spawns an in-place entry box over the double-clicked tree cell."""
        if not self.active_enclosure or self.active_enclosure not in self.enclosures:
            return

        region = self.surface_tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        column = self.surface_tree.identify_column(event.x)  # Returns '#1', '#2', or '#3'
        col_idx = int(column[1:]) - 1

        # Only allow editing Area (col 1) and Emissivity (col 2)
        if col_idx not in (1, 2):
            return

        selected_iid = self.surface_tree.focus()
        if not selected_iid:
            return

        item_values = self.surface_tree.item(selected_iid, "values")
        node_id = item_values[0]
        current_val = item_values[col_idx]

        # Get cell bounding box (x, y, width, height)
        cell_bbox = self.surface_tree.bbox(selected_iid, column)
        if not cell_bbox:
            return

        # Create overlay entry box
        entry = ttk.Entry(self.surface_tree, width=cell_bbox[2])
        entry.place(x=cell_bbox[0], y=cell_bbox[1], w=cell_bbox[2], h=cell_bbox[3])
        entry.insert(0, current_val)
        entry.select_range(0, tk.END)
        entry.focus()

        # Bind submission events
        entry.bind("<Return>", lambda e: self._save_cell_edit(entry, node_id, col_idx))
        entry.bind("<FocusOut>", lambda e: self._save_cell_edit(entry, node_id, col_idx))
        entry.bind("<Escape>", lambda e: entry.destroy())

    def _save_cell_edit(self, entry_widget, node_id, col_idx):
        """Validates and applies the edited value to the enclosure data structure."""
        new_text = entry_widget.get().strip()
        entry_widget.destroy()

        try:
            val = float(new_text)
            enc_data = self.enclosures[self.active_enclosure]
            if node_id not in enc_data["surfaces"]:
                return

            idx = enc_data["surfaces"].index(node_id)

            if col_idx == 1:  # Area [m²]
                if val <= 0:
                    messagebox.showerror("Error", "Area must be a positive number.")
                    return
                enc_data["areas"][idx] = val

                # Update node object in main network reference if present
                live_nodes = self.get_available_nodes()
                node_obj = live_nodes.get(int(node_id) if str(node_id).isdigit() else node_id)
                if node_obj:
                    if hasattr(node_obj, "node_area") and isinstance(node_obj.node_area, list):
                        node_obj.node_area[0] = val
                    else:
                        setattr(node_obj, "node_area", val)

            elif col_idx == 2:  # Emissivity (ε)
                if not (0.0 <= val <= 1.0):
                    messagebox.showerror("Error", "Emissivity (ε) must be between 0.0 and 1.0.")
                    return
                enc_data["eps"][idx] = val

            # Refresh table display and re-verify view factors grid
            self.refresh_surface_list()
            self.refresh_matrix_grid()

        except ValueError:
            messagebox.showerror("Error", "Please enter a valid numeric value.")

    # ------------------------------------------------------------------
    # ENCLOSURE & NODE INTEGRATION LOGIC
    # ------------------------------------------------------------------
    def get_available_nodes(self):
        """Safely retrieves current node references from the main ThermalNetwork instance."""
        if self.main_network_ref is not None and hasattr(self.main_network_ref, "node_dict"):
            return self.main_network_ref.node_dict
        return {}

    def sync_from_network(self):
        """
        Scans all nodes in main_network_ref for 'node_enclosure_id',
        grouping nodes into corresponding enclosures automatically.
        """
        live_nodes = self.get_available_nodes()
        if not live_nodes:
            return

        # Map detected enclosure IDs to node objects
        detected_groups = {}
        for n_id, node in live_nodes.items():
            enc_id = getattr(node, 'node_enclosure_id', None)
            if enc_id and str(enc_id).strip().lower() not in ['none', '', '0']:
                enc_id = str(enc_id).strip()
                detected_groups.setdefault(enc_id, []).append(node)

        # Sync detected groups into local enclosures dict
        for enc_id, nodes in detected_groups.items():
            if enc_id not in self.enclosures:
                self.enclosures[enc_id] = {
                    "surfaces": [],
                    "areas": [],
                    "eps": [],
                    "F": np.empty((0, 0))
                }

            enc = self.enclosures[enc_id]
            # Guarantee both key aliases exist locally
            if "eps" not in enc and "emissivities" in enc:
                enc["eps"] = enc.pop("emissivities")
            if "F" not in enc:
                raw_matrix = enc.get("view_factors", np.empty((0, 0)))
                enc["F"] = np.array(raw_matrix, dtype=float) if len(raw_matrix) > 0 else np.empty((0, 0))

            existing_ids = set(str(n) for n in enc["surfaces"])

            # Add missing nodes detected in network
            for node in nodes:
                str_id = str(node.node_ID)
                if str_id not in existing_ids:
                    # Extract area value safely from node vector if defined
                    raw_area = getattr(node, "node_area", 1.0)
                    area_val = raw_area[0] if isinstance(raw_area, (list, tuple)) else raw_area
                    try:
                        area_val = float(area_val)
                    except (ValueError, TypeError):
                        area_val = 1.0

                    enc["surfaces"].append(str_id)
                    enc["areas"].append(area_val)
                    enc["eps"].append(0.85)

            # Re-dimension View Factor Matrix
            self._resize_matrix(enc_id)

        # Refresh dropdown UI
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

    def _resize_matrix(self, enc_id):
        """Helper to resize View Factor Matrix while retaining existing entries."""
        enc = self.enclosures[enc_id]

        # Ensure 'F' key exists and is a proper NumPy array
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

        # Uniform distribution across non-diagonal entries for new surfaces
        for i in range(new_n):
            for j in range(new_n):
                if i != j and new_F[i, j] == 0.0:
                    new_F[i, j] = 1.0 / max(1, new_n - 1)

        enc["F"] = new_F

    def add_enclosure(self):
        enc_id = f"Enclosure_{len(self.enclosures) + 1}"
        self.enclosures[enc_id] = {
            "surfaces": [],
            "areas": [],
            "eps": [],
            "F": np.empty((0, 0))
        }
        self.combo_enclosures['values'] = list(self.enclosures.keys())
        self.combo_enclosures.set(enc_id)
        self.active_enclosure = enc_id
        self._on_enclosure_selected()

    def delete_enclosure(self):
        selected = self.combo_enclosures.get()
        if selected in self.enclosures:
            del self.enclosures[selected]
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

    def refresh_surface_list(self):
        for item in self.surface_tree.get_children():
            self.surface_tree.delete(item)

        if not self.active_enclosure:
            return

        data = self.enclosures[self.active_enclosure]
        for node, area, e in zip(data["surfaces"], data["areas"], data["eps"]):
            self.surface_tree.insert("", tk.END, values=(node, area, e))

    def refresh_matrix_grid(self):
        """Rebuilds the View Factor Matrix grid and disables main diagonal (F_ii) inputs."""
        for child in self.matrix_container.winfo_children():
            child.destroy()

        if not self.active_enclosure or self.active_enclosure not in self.enclosures:
            return

        data = self.enclosures[self.active_enclosure]
        surfaces = data["surfaces"]
        n = len(surfaces)
        if n == 0:
            return

        # Always force diagonal elements to 0.0 in the internal numerical matrix
        np.fill_diagonal(data["F"], 0.0)

        # Header Row
        ttk.Label(self.matrix_container, text="F(i,j)", font=('Helvetica', 9, 'bold')).grid(row=0, column=0, padx=4,
                                                                                            pady=4)
        for j, s_name in enumerate(surfaces):
            ttk.Label(self.matrix_container, text=str(s_name), font=('Helvetica', 9, 'bold')).grid(row=0, column=j + 1,
                                                                                                   padx=4, pady=4)
        ttk.Label(self.matrix_container, text="Row Sum", font=('Helvetica', 9, 'bold')).grid(row=0, column=n + 1,
                                                                                             padx=8, pady=4)

        self.matrix_entries = []
        for i in range(n):
            row_entries = []
            ttk.Label(self.matrix_container, text=str(surfaces[i]), font=('Helvetica', 9, 'bold')).grid(row=i + 1,
                                                                                                        column=0,
                                                                                                        padx=4, pady=4)

            for j in range(n):
                e = ttk.Entry(self.matrix_container, width=8, justify="center")
                e.insert(0, f"{data['F'][i, j]:.4f}")

                # Disable main diagonal (F_ii) to prevent non-physical self-view inputs
                if i == j:
                    e.config(state="disabled")
                else:
                    # Optional: Bind edit events to save manual input directly into array
                    e.bind("<FocusOut>", lambda ev, row=i, col=j, entry=e: self._on_matrix_cell_edit(row, col, entry))
                    e.bind("<Return>", lambda ev, row=i, col=j, entry=e: self._on_matrix_cell_edit(row, col, entry))

                e.grid(row=i + 1, column=j + 1, padx=2, pady=2)
                row_entries.append(e)

            # Calculate and display row sum status
            r_sum = np.sum(data['F'][i, :]) if data['F'].size > 0 else 0.0
            sum_label = ttk.Label(self.matrix_container, text=f"{r_sum:.3f}")
            sum_label.config(foreground="green" if np.isclose(r_sum, 1.0, atol=1e-2) else "red")
            sum_label.grid(row=i + 1, column=n + 1, padx=8, pady=4)

            self.matrix_entries.append(row_entries)

    def _on_matrix_cell_edit(self, row, col, entry_widget):
        """Helper callback to update local state when a user manually modifies F_ij."""
        if not self.active_enclosure or self.active_enclosure not in self.enclosures:
            return

        val_str = entry_widget.get()
        try:
            val = float(val_str)
            if 0.0 <= val <= 1.0:
                self.enclosures[self.active_enclosure]["F"][row, col] = val
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

                # Also set the enclosure ID on the node object directly
                if node_obj:
                    setattr(node_obj, 'node_enclosure_id', self.active_enclosure)

                enc_data["surfaces"].append(n_id)
                enc_data["areas"].append(float(area_val) if area_val is not None else 1.0)
                enc_data["eps"].append(0.85)

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
            enc_data["surfaces"].pop(idx)
            enc_data["areas"].pop(idx)
            enc_data["eps"].pop(idx)

            # Strip row and column from matrix
            enc_data["F"] = np.delete(np.delete(enc_data["F"], idx, axis=0), idx, axis=1)

            # Reset node attribute in main network reference if available
            live_nodes = self.get_available_nodes()
            node_obj = live_nodes.get(int(node_id) if node_id.isdigit() else node_id)
            if node_obj:
                setattr(node_obj, 'node_enclosure_id', "None")

            self.refresh_surface_list()
            self.refresh_matrix_grid()

    # ------------------------------------------------------------------
    # MATRIX CALCULATIONS & VALIDATIONS
    # ------------------------------------------------------------------
    def check_reciprocity(self):
        """Verifies A_i * F_ij = A_j * F_ji"""
        if not self.active_enclosure:
            return
        data = self.enclosures[self.active_enclosure]
        A = np.array(data["areas"])
        F = data["F"]
        n = len(A)

        errors = []
        for i in range(n):
            for j in range(i + 1, n):
                q1 = A[i] * F[i, j]
                q2 = A[j] * F[j, i]
                if not np.isclose(q1, q2, rtol=1e-3, atol=1e-5):
                    errors.append(
                        f"Pair ({data['surfaces'][i]}, {data['surfaces'][j]}): A_i*F_ij={q1:.4f} != A_j*F_ji={q2:.4f}")

        if errors:
            self.logger(f"Reciprocity Check Failed for '{self.active_enclosure}':", "WARNING")
            for err in errors:
                self.logger(f"  -> {err}", "WARNING")
        else:
            self.logger(f"Reciprocity check passed for '{self.active_enclosure}'.", "SUCCESS")

    def enforce_convex_surfaces(self, enc_id):
        """Ensures no self-view factors exist for flat/convex surface nodes."""
        enc = self.enclosures[enc_id]
        np.fill_diagonal(enc["F"], 0.0)

    def normalize_matrix(self):
        """
        Normalizes the view factor matrix using constrained least-squares optimization (SLSQP).
        Guarantees:
          1. Reciprocity: A_i * F_ij = A_j * F_ji
          2. Closure: sum_j(F_ij) = 1.0
          3. Physical bounds: 0.0 <= F_ij <= 1.0
          4. Zero diagonal: F_ii = 0.0
        """
        if not self.active_enclosure or self.active_enclosure not in self.enclosures:
            self.logger("Select an enclosure before normalizing.", "WARNING")
            return

        data = self.enclosures[self.active_enclosure]
        F_init = np.copy(data["F"])
        A = np.array(data["areas"], dtype=float)
        n = len(A)

        if n < 2 or F_init.size == 0:
            return

        # Flatten initial off-diagonal terms to construct the optimization vector
        # x represents F_ij flattened into a 1D array of size n*n
        x0 = F_init.flatten()

        # Objective function: Minimize sum of squared differences from original initial matrix
        def objective(x):
            return np.sum((x - x0) ** 2)

        # Constraints list
        constraints = []

        # 1. Zero Diagonal Constraints: F_ii = 0
        for i in range(n):
            constraints.append({
                'type': 'eq',
                'fun': lambda x, idx=i: x[idx * n + idx]
            })

        # 2. Row Closure Constraints: sum_j(F_ij) = 1.0
        for i in range(n):
            constraints.append({
                'type': 'eq',
                'fun': lambda x, row=i: np.sum(x[row * n: (row + 1) * n]) - 1.0
            })

        # 3. Reciprocity Constraints: A_i * F_ij - A_j * F_ji = 0
        for i in range(n):
            for j in range(i + 1, n):
                constraints.append({
                    'type': 'eq',
                    'fun': lambda x, r=i, c=j: A[r] * x[r * n + c] - A[c] * x[c * n + r]
                })

        # 4. Strict Bounds: 0.0 <= F_ij <= 1.0
        bounds = [(0.0, 1.0) for _ in range(n * n)]

        # Run Sequential Least Squares Programming (SLSQP)
        res = opt.minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 500, 'ftol': 1e-6}
        )

        if res.success:
            F_opt = res.x.reshape((n, n))
            np.fill_diagonal(F_opt, 0.0)
            data["F"] = F_opt

            self.refresh_matrix_grid()
            self.logger(
                f"Successfully normalized enclosure '{self.active_enclosure}'. Bounds [0, 1] & reciprocity enforced.",
                "SUCCESS")
        else:
            self.logger(f"Optimization failed for '{self.active_enclosure}': {res.message}", "ERROR")

    def inject_network(self):
        """Pushes active enclosure payload into the global enclosure dictionary."""
        if not self.active_enclosure or self.active_enclosure not in self.enclosures:
            self.logger("No active enclosure to inject.", "WARNING")
            return

        data = self.enclosures[self.active_enclosure]

        # Extract local UI 'eps' list safely, falling back to 0.85 if missing
        surfaces = data.get("surfaces", [])
        areas = data.get("areas", [])
        emissivities = data.get("eps", [0.85] * len(surfaces))

        # Convert matrix array to a standard list for serialization
        matrix = data.get("F", [])
        view_factors = matrix.tolist() if hasattr(matrix, "tolist") else matrix

        # Populate the shared master dictionary
        self.enclosure_dict[self.active_enclosure] = {
            "surfaces": surfaces,
            "areas": areas,
            "emissivities": emissivities,  # Mapped correctly from 'eps'
            "view_factors": view_factors,
            "model": self.net_model_var.get()
        }

        self.logger(f"Enclosure '{self.active_enclosure}' injected into Thermal Network.", "SUCCESS")

    def _clear_views(self):
        for item in self.surface_tree.get_children():
            self.surface_tree.delete(item)
        for child in self.matrix_container.winfo_children():
            child.destroy()
