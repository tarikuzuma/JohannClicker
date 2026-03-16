"""
AutoClicker Application
=======================
A desktop autoclicker built with customtkinter (modern UI) and pynput
(mouse control / global hotkeys). Mimics the "Auto-Clicker by Polar 2.0" layout.

Features:
  - Coordinate picker (Pick button → click anywhere → X/Y auto-fill)
  - Threaded clicking loop (non-blocking, UI stays responsive)
  - Global hotkey CTRL+F3 to start/stop
  - Queued position table with X, Y, L/R, Delay columns
"""

import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

import customtkinter as ctk
from pynput import mouse, keyboard


# ──────────────────────────────────────────────────────────────────────
# Application
# ──────────────────────────────────────────────────────────────────────
class AutoClickerApp(ctk.CTk):
    """Main application window for the AutoClicker."""

    # Appearance defaults
    WIDTH = 820
    HEIGHT = 480

    def __init__(self):
        super().__init__()

        # ── Window setup ──────────────────────────────────────────────
        self.title("Auto-Clicker by Tarikuzuma 1.0")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.resizable(False, False)
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # ── Internal state ────────────────────────────────────────────
        self._clicking = False           # True while the loop is running
        self._stop_event = threading.Event()  # Signals the loop to stop
        self._pick_listener = None       # pynput mouse listener for Pick
        self._pick_kbd_listener = None   # pynput keyboard listener for Pick
        self._pick_overlay = None       # Tooltip window during Pick
        self._hotkey_listener = None     # pynput global hotkey listener

        # ── Build the UI ──────────────────────────────────────────────
        self._build_left_panel()
        self._build_right_panel()
        self._configure_treeview_style()

        # ── Start global hotkey listener ──────────────────────────────
        self._start_hotkey_listener()

        # Graceful shutdown
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ==================================================================
    # UI Construction
    # ==================================================================

    def _build_left_panel(self):
        """Build the left 'Starting Options' panel."""
        frame = ctk.CTkFrame(self, width=280, corner_radius=8)
        frame.grid(row=0, column=0, padx=(12, 6), pady=12, sticky="nsew")
        frame.grid_propagate(False)

        # ── Section label ─────────────────────────────────────────────
        ctk.CTkLabel(
            frame, text="Starting Options",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, padx=12, pady=(12, 4), sticky="w")

        # ── Number of Repeats ─────────────────────────────────────────
        ctk.CTkLabel(frame, text="Number of Repeats", anchor="w").grid(
            row=1, column=0, padx=12, pady=(8, 4), sticky="w"
        )
        self.repeats_entry = ctk.CTkEntry(frame, width=80, justify="center")
        self.repeats_entry.insert(0, "1")
        self.repeats_entry.grid(row=1, column=1, padx=12, pady=(8, 4), sticky="e")

        # ── Start clicking ────────────────────────────────────────────
        self.start_btn = ctk.CTkButton(
            frame,
            text="Start clicking (CTRL+F3)",
            command=self._start_clicking,
            width=240,
        )
        self.start_btn.grid(row=2, column=0, columnspan=2, padx=12, pady=(12, 4))

        # ── Stop clicking ─────────────────────────────────────────────
        self.stop_btn = ctk.CTkButton(
            frame,
            text="Stop clicking (CTRL+F3)",
            command=self._stop_clicking,
            fg_color="#d9534f",
            hover_color="#c9302c",
            width=240,
        )
        self.stop_btn.grid(row=3, column=0, columnspan=2, padx=12, pady=4)

        # ── Clear All ─────────────────────────────────────────────────
        self.clear_btn = ctk.CTkButton(
            frame,
            text="Clear All",
            command=self._clear_all,
            fg_color="#f0ad4e",
            hover_color="#ec971f",
            text_color="white",
            width=240,
        )
        self.clear_btn.grid(row=4, column=0, columnspan=2, padx=12, pady=4)

        # ── Options button (cosmetic) ─────────────────────────────────
        ctk.CTkButton(
            frame,
            text="Options…",
            width=240,
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            command=lambda: messagebox.showinfo("Options", "No additional options."),
        ).grid(row=5, column=0, columnspan=2, padx=12, pady=4)

        # ── Help button (cosmetic) ────────────────────────────────────
        ctk.CTkButton(
            frame,
            text="Help?",
            width=240,
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            command=lambda: messagebox.showinfo(
                "Help",
                "1. Use 'Pick' to capture screen coordinates.\n"
                "2. Set delay, click type, then 'Add Position'.\n"
                "3. Press 'Start clicking' or CTRL+F3 to begin.\n"
                "4. Press 'Stop clicking' or CTRL+F3 to halt.",
            ),
        ).grid(row=6, column=0, columnspan=2, padx=12, pady=(4, 12))

    def _build_right_panel(self):
        """Build the right 'Cursor Positions' panel."""
        frame = ctk.CTkFrame(self, corner_radius=8)
        frame.grid(row=0, column=1, padx=(6, 12), pady=12, sticky="nsew")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Section label ─────────────────────────────────────────────
        ctk.CTkLabel(
            frame, text="Cursor Positions",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, columnspan=6, padx=12, pady=(12, 4), sticky="w")

        # ── Pick button ───────────────────────────────────────────────
        self.pick_btn = ctk.CTkButton(
            frame, text="Pick", width=70, command=self._pick_coordinate
        )
        self.pick_btn.grid(row=1, column=0, padx=(12, 4), pady=4, sticky="w")

        # ── X entry ───────────────────────────────────────────────────
        ctk.CTkLabel(frame, text="X").grid(row=1, column=1, padx=(4, 0), pady=4)
        self.x_entry = ctk.CTkEntry(frame, width=60, justify="center")
        self.x_entry.insert(0, "0")
        self.x_entry.grid(row=1, column=2, padx=(0, 8), pady=4)

        # ── Y entry ───────────────────────────────────────────────────
        ctk.CTkLabel(frame, text="Y").grid(row=1, column=3, padx=(4, 0), pady=4)
        self.y_entry = ctk.CTkEntry(frame, width=60, justify="center")
        self.y_entry.insert(0, "0")
        self.y_entry.grid(row=1, column=4, padx=(0, 8), pady=4)

        # ── Right Click checkbox ──────────────────────────────────────
        self.right_click_var = ctk.BooleanVar(value=False)
        self.right_click_cb = ctk.CTkCheckBox(
            frame, text="Right Click", variable=self.right_click_var
        )
        self.right_click_cb.grid(row=1, column=5, padx=(4, 12), pady=4)

        # ── Time to Sleep (.ms) ───────────────────────────────────────
        ctk.CTkLabel(frame, text="Time to Sleep (.ms)").grid(
            row=2, column=0, columnspan=2, padx=12, pady=4, sticky="w"
        )
        self.delay_entry = ctk.CTkEntry(frame, width=80, justify="center")
        self.delay_entry.insert(0, "600")
        self.delay_entry.grid(row=2, column=2, padx=0, pady=4, sticky="w")

        # ── Add Position button ───────────────────────────────────────
        self.add_btn = ctk.CTkButton(
            frame, text="Add position", width=120, command=self._add_position
        )
        self.add_btn.grid(row=2, column=3, columnspan=3, padx=(8, 12), pady=4, sticky="e")

        # ── Queued Cursor Positions label ─────────────────────────────
        ctk.CTkLabel(
            frame, text="Queued Cursor Positions",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).grid(row=3, column=0, columnspan=6, padx=12, pady=(8, 2), sticky="w")

        # ── Treeview (table) ──────────────────────────────────────────
        tree_frame = tk.Frame(frame, bg="#f0f0f0")
        tree_frame.grid(
            row=4, column=0, columnspan=6,
            padx=12, pady=(0, 12), sticky="nsew",
        )
        frame.grid_rowconfigure(4, weight=1)
        frame.grid_columnconfigure(5, weight=1)

        columns = ("x", "y", "lr", "delay")
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", selectmode="browse"
        )
        self.tree.heading("x", text="X")
        self.tree.heading("y", text="Y")
        self.tree.heading("lr", text="L/R")
        self.tree.heading("delay", text="Delay (ms)")
        self.tree.column("x", width=80, anchor="center")
        self.tree.column("y", width=80, anchor="center")
        self.tree.column("lr", width=60, anchor="center")
        self.tree.column("delay", width=120, anchor="center")

        scrollbar = ttk.Scrollbar(
            tree_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ── Context Menu ─────────────────────────────────────────────
        self._tree_menu = tk.Menu(self.tree, tearoff=0)
        self._tree_menu.add_command(label="Move Up", command=self._move_up)
        self._tree_menu.add_command(label="Move Down", command=self._move_down)
        self._tree_menu.add_separator()
        self._tree_menu.add_command(label="Delete row", command=self._delete_selected_row)
        self.tree.bind("<Button-3>", self._show_tree_menu)

        # ── Drag and Drop Reordering ──────────────────────────────────
        self.tree.bind("<ButtonPress-1>", self._on_drag_start)
        self.tree.bind("<ButtonRelease-1>", self._on_drag_drop)
        self.tree.bind("<B1-Motion>", self._on_drag_motion)

    def _configure_treeview_style(self):
        """Apply a clean style to the ttk Treeview."""
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background="white",
            foreground="black",
            fieldbackground="white",
            rowheight=26,
            font=("Segoe UI", 10),
        )
        # Highlight tag for dragging
        self.tree.tag_configure("dragging", background="#e1f5fe", foreground="#0288d1")
        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 10, "bold"),
            background="#dcdcdc",
            foreground="black",
        )
        style.map("Treeview", background=[("selected", "#3b8ed0")])

    # ==================================================================
    # Coordinate Picker
    # ==================================================================

    def _pick_coordinate(self):
        """Start a mouse listener that captures the next click's coordinates."""
        self.pick_btn.configure(text="Click…", state="disabled")

        # Minimise the window so the user can click on the target position
        self.iconify()

        # Small delay to allow the window to minimize before listening
        self.after(400, self._start_pick_listener)

    def _start_pick_listener(self):
        """Begin listening for mouse move/click and Escape key to capture coordinates."""
        # Create overlay
        self._pick_overlay = tk.Toplevel(self)
        self._pick_overlay.overrideredirect(True)
        self._pick_overlay.attributes("-topmost", True)
        self._pick_overlay.attributes("-alpha", 0.9)
        self._overlay_label = tk.Label(
            self._pick_overlay,
            text="X: 0, Y: 0\nClick or ESC to pick",
            bg="black",
            fg="white",
            padx=10,
            pady=5,
            font=("Segoe UI", 10, "bold")
        )
        self._overlay_label.pack()

        def on_move(x, y):
            # Update overlay position and text
            self.after(0, lambda: self._update_overlay(x, y))

        def on_click(x, y, button, pressed):
            if pressed and button == mouse.Button.left:
                # Schedule UI update on the main thread
                self.after(0, lambda: self._finish_pick(x, y))
                return False  # Stop listener

        def on_press(key):
            if key == keyboard.Key.esc:
                # Get current mouse position since pynput mouse.Controller doesn't track it here easily
                # but we can just use the last known from on_move or a fresh controller
                ctrl = mouse.Controller()
                cur_x, cur_y = ctrl.position
                self.after(0, lambda: self._finish_pick(cur_x, cur_y))
                return False # Stop listener

        self._pick_listener = mouse.Listener(on_move=on_move, on_click=on_click)
        self._pick_kbd_listener = keyboard.Listener(on_press=on_press)
        
        self._pick_listener.start()
        self._pick_kbd_listener.start()

    def _update_overlay(self, x, y):
        """Update the overlay window's position and text."""
        if self._pick_overlay and self._pick_overlay.winfo_exists():
            self._overlay_label.configure(text=f"X: {int(x)}, Y: {int(y)}\nClick or ESC to pick")
            # Position offset so it doesn't block the click
            self._pick_overlay.geometry(f"+{int(x)+20}+{int(y)+20}")

    def _finish_pick(self, x: int, y: int):
        """Fill X/Y entries, clean up overlay/listeners, and restore window."""
        # Stop listeners if they are still running
        if self._pick_listener:
            self._pick_listener.stop()
            self._pick_listener = None
        if self._pick_kbd_listener:
            self._pick_kbd_listener.stop()
            self._pick_kbd_listener = None

        # Destroy overlay
        if self._pick_overlay:
            self._pick_overlay.destroy()
            self._pick_overlay = None

        self.x_entry.delete(0, "end")
        self.x_entry.insert(0, str(int(x)))
        self.y_entry.delete(0, "end")
        self.y_entry.insert(0, str(int(y)))

        # Immediately append to the table
        self._add_position()

        self.pick_btn.configure(text="Pick", state="normal")
        self.deiconify()  # Restore the window
        self.lift()
        self.focus_force()

    # ==================================================================
    # Table Management
    # ==================================================================

    def _add_position(self):
        """Validate inputs and add a new row to the queued positions table."""
        try:
            x = int(self.x_entry.get())
            y = int(self.y_entry.get())
        except ValueError:
            messagebox.showerror("Input Error", "X and Y must be valid integers.")
            return

        try:
            delay = int(self.delay_entry.get())
            if delay < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Input Error", "Delay must be a non-negative integer (ms)."
            )
            return

        lr = "R" if self.right_click_var.get() else "L"
        self.tree.insert("", "end", values=(x, y, lr, delay))

    def _delete_selected_row(self):
        """Delete the currently selected row from the treeview."""
        selected = self.tree.selection()
        if selected:
            self.tree.delete(selected[0])

    # ==================================================================
    # Drag and Drop Reordering
    # ==================================================================

    def _on_drag_start(self, event):
        """Identify the row being dragged and show signifier."""
        item = self.tree.identify_row(event.y)
        if item:
            self._drag_item = item
            self.tree.selection_set(item)
            # Add signifier
            self.tree.item(item, tags=("dragging",))
            self.tree.configure(cursor="sb_v_double_arrow")

    def _on_drag_motion(self, event):
        """Provide visual feedback (selection follows mouse)."""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)

    def _on_drag_drop(self, event):
        """Move the dragged item, clean up signifiers."""
        if hasattr(self, "_drag_item") and self._drag_item:
            # Remove signifiers
            self.tree.item(self._drag_item, tags=())
            self.tree.configure(cursor="")

            target_item = self.tree.identify_row(event.y)
            if target_item and target_item != self._drag_item:
                target_index = self.tree.index(target_item)
                self.tree.move(self._drag_item, "", target_index)
            
            self._drag_item = None

    def _move_up(self):
        """Move the selected row up in the treeview."""
        selected = self.tree.selection()
        if not selected:
            return
        for item in selected:
            index = self.tree.index(item)
            if index > 0:
                self.tree.move(item, self.tree.parent(item), index - 1)

    def _move_down(self):
        """Move the selected row down in the treeview."""
        selected = self.tree.selection()
        if not selected:
            return
        # Move items in reverse order when moving down to maintain correct indexing
        for item in reversed(selected):
            index = self.tree.index(item)
            if index < len(self.tree.get_children()) - 1:
                self.tree.move(item, self.tree.parent(item), index + 1)

    def _show_tree_menu(self, event):
        """Show the right-click context menu on the treeview."""
        row_id = self.tree.identify_row(event.y)
        if row_id:
            self.tree.selection_set(row_id)
            self._tree_menu.post(event.x_root, event.y_root)

    def _clear_all(self):
        """Remove every row from the queued positions table."""
        for item in self.tree.get_children():
            self.tree.delete(item)

    # ==================================================================
    # Clicking Loop (threaded)
    # ==================================================================

    def _start_clicking(self):
        """Validate inputs and launch the clicking loop in a background thread."""
        if self._clicking:
            return  # Already running

        # Validate repeats
        try:
            repeats = int(self.repeats_entry.get())
            if repeats < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Input Error", "Number of Repeats must be a positive integer."
            )
            return

        # Gather positions from the table
        positions = []
        for item_id in self.tree.get_children():
            vals = self.tree.item(item_id, "values")
            positions.append(
                {
                    "x": int(vals[0]),
                    "y": int(vals[1]),
                    "button": vals[2],
                    "delay": int(vals[3]),
                }
            )

        if not positions:
            messagebox.showwarning(
                "No Positions", "Add at least one position before starting."
            )
            return

        # Prepare state
        self._clicking = True
        self._stop_event.clear()
        self._update_button_states()

        # Launch worker thread
        thread = threading.Thread(
            target=self._click_loop,
            args=(positions, repeats),
            daemon=True,
        )
        thread.start()

    def _click_loop(self, positions: list[dict], repeats: int):
        """
        Worker executed in a background thread.
        Iterates through *positions* for *repeats* cycles,
        performing clicks via pynput.
        """
        ctrl = mouse.Controller()

        for _ in range(repeats):
            for pos in positions:
                if self._stop_event.is_set():
                    break

                # Move the cursor and click
                ctrl.position = (pos["x"], pos["y"])
                btn = (
                    mouse.Button.right
                    if pos["button"] == "R"
                    else mouse.Button.left
                )
                ctrl.click(btn)

                # Sleep in small increments so we can react to stop quickly
                delay_s = pos["delay"] / 1000.0
                elapsed = 0.0
                while elapsed < delay_s and not self._stop_event.is_set():
                    time.sleep(min(0.05, delay_s - elapsed))
                    elapsed += 0.05

            if self._stop_event.is_set():
                break

        # Finished (either completed or stopped)
        self._clicking = False
        self.after(0, self._update_button_states)

    def _stop_clicking(self):
        """Signal the background clicking loop to stop."""
        self._stop_event.set()
        self._clicking = False
        self._update_button_states()

    def _update_button_states(self):
        """Enable / disable Start and Stop buttons based on state."""
        if self._clicking:
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
        else:
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="normal")

    # ==================================================================
    # Global Hotkey (CTRL+F3)
    # ==================================================================

    def _start_hotkey_listener(self):
        """Register CTRL+F3 as a global hotkey to toggle start/stop."""
        self._hotkey_listener = keyboard.GlobalHotKeys(
            {"<ctrl>+<f3>": self._toggle_clicking}
        )
        self._hotkey_listener.daemon = True
        self._hotkey_listener.start()

    def _toggle_clicking(self):
        """Toggle between start and stop — called from the hotkey thread."""
        if self._clicking:
            self.after(0, self._stop_clicking)
        else:
            self.after(0, self._start_clicking)

    # ==================================================================
    # Shutdown
    # ==================================================================

    def _on_close(self):
        """Clean up listeners and close the application."""
        self._stop_event.set()

        if self._pick_listener and self._pick_listener.is_alive():
            self._pick_listener.stop()
        if self._hotkey_listener and self._hotkey_listener.is_alive():
            self._hotkey_listener.stop()

        self.destroy()


# ──────────────────────────────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = AutoClickerApp()
    app.mainloop()
