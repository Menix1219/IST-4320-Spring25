import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from datetime import datetime

# --- Configuration ---
DEFAULT_FILENAME = "reminders_data.json"
PRIORITY_LEVELS = ["High", "Medium", "Low"]
DATE_FORMAT = "%Y-%m-%d %H:%M" 

class Reminder:
    """
    Represents a single reminder item.
    """
    def __init__(self, task, due_date_str, priority, details="", is_completed=False, creation_date=None):
        self.task = task
        self.priority = priority
        self.details = details
        self.is_completed = is_completed
        self.creation_date = creation_date if creation_date else datetime.now().strftime(DATE_FORMAT)

        if isinstance(due_date_str, str):
            try:
                self.due_date = datetime.strptime(due_date_str, DATE_FORMAT)
            except ValueError:
                # Fallback if parsing fails, or handle error more gracefully
                messagebox.showwarning("Date Format Error", f"Could not parse due date '{due_date_str}'. Using current date/time as due date.")
                self.due_date = datetime.now()
        elif isinstance(due_date_str, datetime):
            self.due_date = due_date_str
        else:
            messagebox.showwarning("Date Type Error", f"Unexpected due date type '{type(due_date_str)}'. Using current date/time.")
            self.due_date = datetime.now()


    def to_dict(self):
        """Converts the reminder object to a dictionary for JSON serialization."""
        return {
            "task": self.task,
            "due_date_str": self.due_date.strftime(DATE_FORMAT),
            "priority": self.priority,
            "details": self.details,
            "is_completed": self.is_completed,
            "creation_date": self.creation_date
        }

    @classmethod
    def from_dict(cls, data):
        """Creates a Reminder object from a dictionary."""
        return cls(
            task=data["task"],
            due_date_str=data["due_date_str"],
            priority=data["priority"],
            details=data.get("details", ""),
            is_completed=data.get("is_completed", False),
            creation_date=data.get("creation_date")
        )

    def __str__(self):
        status = "[X]" if self.is_completed else "[ ]"
        return f"{status} {self.task} (Due: {self.due_date.strftime(DATE_FORMAT)}, Priority: {self.priority})"

class ReminderApp:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("Advanced Reminder App")
        self.root.geometry("900x700") # Increased size for more details

        self.reminders_list = []
        self.current_filename = DEFAULT_FILENAME

        self._setup_ui()
        self._load_reminders_on_startup() # Load reminders when the app starts

    def _setup_ui(self):
        # --- Menu Bar ---
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New", command=self._clear_all_fields_and_list)
        file_menu.add_command(label="Open", command=self._load_reminders_dialog)
        file_menu.add_command(label="Save", command=self._save_reminders)
        file_menu.add_command(label="Save As...", command=self._save_reminders_as_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        # --- Main Frame ---
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Input Frame ---
        input_frame = ttk.LabelFrame(main_frame, text="Add/Edit Reminder", padding="10")
        input_frame.pack(fill=tk.X, pady=10)

        ttk.Label(input_frame, text="Task:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.task_entry = ttk.Entry(input_frame, width=40)
        self.task_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(input_frame, text=f"Due Date ({DATE_FORMAT}):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.due_date_entry = ttk.Entry(input_frame, width=20)
        self.due_date_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.due_date_entry.insert(0, datetime.now().strftime(DATE_FORMAT)) # Default to now

        ttk.Button(input_frame, text="Now", command=self._set_due_date_to_now, width=5).grid(row=1, column=2, padx=5, pady=5)


        ttk.Label(input_frame, text="Priority:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.priority_var = tk.StringVar(value=PRIORITY_LEVELS[1]) # Default to Medium
        self.priority_combobox = ttk.Combobox(input_frame, textvariable=self.priority_var, values=PRIORITY_LEVELS, state="readonly", width=18)
        self.priority_combobox.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(input_frame, text="Details (Optional):").grid(row=3, column=0, padx=5, pady=5, sticky="nw")
        self.details_text = tk.Text(input_frame, width=38, height=4, wrap=tk.WORD)
        self.details_text.grid(row=3, column=1, padx=5, pady=5, sticky="ew", rowspan=2)
        details_scrollbar = ttk.Scrollbar(input_frame, orient=tk.VERTICAL, command=self.details_text.yview)
        details_scrollbar.grid(row=3, column=2, sticky="ns", rowspan=2)
        self.details_text.config(yscrollcommand=details_scrollbar.set)


        input_button_frame = ttk.Frame(input_frame)
        input_button_frame.grid(row=5, column=0, columnspan=3, pady=10)

        self.add_button = ttk.Button(input_button_frame, text="Add Reminder", command=self._add_reminder_from_ui)
        self.add_button.pack(side=tk.LEFT, padx=5)
        self.update_button = ttk.Button(input_button_frame, text="Update Selected", command=self._update_selected_reminder, state=tk.DISABLED)
        self.update_button.pack(side=tk.LEFT, padx=5)
        ttk.Button(input_button_frame, text="Clear Fields", command=self._clear_input_fields).pack(side=tk.LEFT, padx=5)


        # --- Reminders Display Frame (Using Treeview) ---
        display_frame = ttk.LabelFrame(main_frame, text="My Reminders", padding="10")
        display_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        cols = ("status", "task", "due_date", "priority", "created_date", "details")
        col_widths = {"status": 50, "task": 250, "due_date": 150, "priority": 80, "created_date": 150, "details":0} # Hide details initially

        self.reminders_tree = ttk.Treeview(display_frame, columns=cols, show="headings", selectmode="browse")

        for col_name in cols:
            self.reminders_tree.heading(col_name, text=col_name.replace("_", " ").title())
            self.reminders_tree.column(col_name, width=col_widths.get(col_name, 100), anchor=tk.W if col_name != "status" else tk.CENTER)

        # Special column for status (checkbox-like)
        self.reminders_tree.column("details", width=0, stretch=tk.NO) # Hide details column initially

        tree_scrollbar_y = ttk.Scrollbar(display_frame, orient=tk.VERTICAL, command=self.reminders_tree.yview)
        self.reminders_tree.configure(yscrollcommand=tree_scrollbar_y.set)
        tree_scrollbar_x = ttk.Scrollbar(display_frame, orient=tk.HORIZONTAL, command=self.reminders_tree.xview)
        self.reminders_tree.configure(xscrollcommand=tree_scrollbar_x.set)

        self.reminders_tree.grid(row=0, column=0, sticky="nsew")
        tree_scrollbar_y.grid(row=0, column=1, sticky="ns")
        tree_scrollbar_x.grid(row=1, column=0, sticky="ew")

        display_frame.grid_rowconfigure(0, weight=1)
        display_frame.grid_columnconfigure(0, weight=1)

        self.reminders_tree.bind("<<TreeviewSelect>>", self._on_reminder_select)
        self.reminders_tree.bind("<Double-1>", self._toggle_complete_selected) # Double click to toggle complete

        # --- Action Buttons for Display ---
        action_button_frame = ttk.Frame(main_frame, padding="5")
        action_button_frame.pack(fill=tk.X)

        self.complete_button = ttk.Button(action_button_frame, text="Toggle Complete", command=self._toggle_complete_selected, state=tk.DISABLED)
        self.complete_button.pack(side=tk.LEFT, padx=5)
        self.edit_button = ttk.Button(action_button_frame, text="Load for Edit", command=self._load_selected_for_editing, state=tk.DISABLED) # Renamed from "Edit"
        self.edit_button.pack(side=tk.LEFT, padx=5)
        self.delete_button = ttk.Button(action_button_frame, text="Delete Selected", command=self._delete_selected_reminder, state=tk.DISABLED)
        self.delete_button.pack(side=tk.LEFT, padx=5)
        ttk.Button(action_button_frame, text="Delete All", command=self._delete_all_reminders).pack(side=tk.LEFT, padx=5)

        # --- Status Bar ---
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _set_due_date_to_now(self):
        self.due_date_entry.delete(0, tk.END)
        self.due_date_entry.insert(0, datetime.now().strftime(DATE_FORMAT))

    def _clear_input_fields(self):
        self.task_entry.delete(0, tk.END)
        self.due_date_entry.delete(0, tk.END)
        self.due_date_entry.insert(0, datetime.now().strftime(DATE_FORMAT))
        self.priority_var.set(PRIORITY_LEVELS[1])
        self.details_text.delete("1.0", tk.END)
        self.task_entry.focus()
        # Reset update button if it was active
        self.add_button.config(state=tk.NORMAL)
        self.update_button.config(state=tk.DISABLED)
        if self.reminders_tree.selection():
            self.reminders_tree.selection_remove(self.reminders_tree.selection()[0])
        self.status_var.set("Input fields cleared.")


    def _clear_all_fields_and_list(self):
        if messagebox.askyesno("New File", "Are you sure you want to clear all current reminders and start a new list? Unsaved changes will be lost."):
            self._clear_input_fields()
            self.reminders_list.clear()
            self._refresh_reminders_tree()
            self.current_filename = DEFAULT_FILENAME # Reset filename
            self.root.title(f"Advanced Reminder App - New File")
            self.status_var.set("New reminder list started.")


    def _add_reminder_from_ui(self):
        task = self.task_entry.get().strip()
        due_date_str = self.due_date_entry.get().strip()
        priority = self.priority_var.get()
        details = self.details_text.get("1.0", tk.END).strip()

        if not task:
            messagebox.showerror("Input Error", "Task cannot be empty.")
            return
        if not due_date_str:
            messagebox.showerror("Input Error", "Due date cannot be empty.")
            return

        try:
            # Validate date format before creating Reminder object
            datetime.strptime(due_date_str, DATE_FORMAT)
        except ValueError:
            messagebox.showerror("Input Error", f"Invalid due date format. Please use {DATE_FORMAT}.")
            return

        new_reminder = Reminder(task, due_date_str, priority, details)
        self._add_reminder_object(new_reminder)
        self._clear_input_fields()
        self.status_var.set(f"Reminder '{task}' added.")

    def _add_reminder_object(self, reminder_obj, *args, **kwargs):
        """
        Adds a Reminder object to the list and refreshes the display.
        *args and **kwargs are included for flexibility as per guideline.
        """
        self.reminders_list.append(reminder_obj)
        self._sort_reminders()
        self._refresh_reminders_tree()

    def _sort_reminders(self):
        """Sorts reminders: by completion status (incomplete first), then by due date, then by priority."""
        priority_map = {level: i for i, level in enumerate(PRIORITY_LEVELS)} # High=0, Medium=1, Low=2
        self.reminders_list.sort(key=lambda r: (r.is_completed, r.due_date, priority_map[r.priority]))


    def _refresh_reminders_tree(self):
        # Clear existing items
        for item in self.reminders_tree.get_children():
            self.reminders_tree.delete(item)

        # Add new items
        for i, reminder in enumerate(self.reminders_list):
            status_icon = "✅" if reminder.is_completed else "⏳" # Using Unicode for visual cue
            values = (
                status_icon,
                reminder.task,
                reminder.due_date.strftime(DATE_FORMAT),
                reminder.priority,
                reminder.creation_date,
                reminder.details # This won't be visible unless column width is changed
            )
         
      
            item_id = self.reminders_tree.insert("", tk.END, iid=str(i) ,values=values)

            # Apply tags for styling based on priority or status
            tags = []
            if reminder.is_completed:
                tags.append("completed")
            else:
                tags.append("pending")
                if reminder.due_date < datetime.now():
                    tags.append("overdue")

            priority_tag = reminder.priority.lower() + "_priority"
            tags.append(priority_tag)

            self.reminders_tree.item(item_id, tags=tuple(tags))

        # Define tag configurations (colors, fonts)
        self.reminders_tree.tag_configure("completed", foreground="gray", font=('TkDefaultFont', 10, 'italic'))
        self.reminders_tree.tag_configure("pending", foreground="black")
        self.reminders_tree.tag_configure("overdue", background="#FFCCCC") # Light red background for overdue
        self.reminders_tree.tag_configure("high_priority", font=('TkDefaultFont', 10, 'bold'))
        self.reminders_tree.tag_configure("medium_priority") # Default
        self.reminders_tree.tag_configure("low_priority", foreground="darkgray")


    def _on_reminder_select(self, event=None):
        selected_items = self.reminders_tree.selection()
        if selected_items:
            self.edit_button.config(state=tk.NORMAL)
            self.delete_button.config(state=tk.NORMAL)
            self.complete_button.config(state=tk.NORMAL)
            # Do not automatically load for editing; use a separate button for that
            # self._load_selected_for_editing()
        else:
            self.edit_button.config(state=tk.DISABLED)
            self.delete_button.config(state=tk.DISABLED)
            self.complete_button.config(state=tk.DISABLED)
            self.add_button.config(state=tk.NORMAL) # Ensure add is enabled if nothing selected
            self.update_button.config(state=tk.DISABLED)

    def _get_selected_reminder_object(self):
        selected_items = self.reminders_tree.selection()
        if not selected_items:
            return None
        item_iid = selected_items[0] # Assuming single selection
        try:
            # The IID is the index in the self.reminders_list
            index = int(item_iid)
            if 0 <= index < len(self.reminders_list):
                return self.reminders_list[index]
        except ValueError:
            messagebox.showerror("Error", "Invalid selection.")
        return None


    def _load_selected_for_editing(self):
        selected_reminder = self._get_selected_reminder_object()
        if selected_reminder:
            self.task_entry.delete(0, tk.END)
            self.task_entry.insert(0, selected_reminder.task)
            self.due_date_entry.delete(0, tk.END)
            self.due_date_entry.insert(0, selected_reminder.due_date.strftime(DATE_FORMAT))
            self.priority_var.set(selected_reminder.priority)
            self.details_text.delete("1.0", tk.END)
            self.details_text.insert("1.0", selected_reminder.details)

            self.add_button.config(state=tk.DISABLED) # Disable Add
            self.update_button.config(state=tk.NORMAL) # Enable Update
            self.status_var.set(f"Editing reminder: '{selected_reminder.task}'")


    def _update_selected_reminder(self, **kwargs): # Added **kwargs for flexibility
        selected_reminder = self._get_selected_reminder_object()
        if not selected_reminder:
            messagebox.showinfo("Update", "No reminder selected to update.")
            return

        new_task = self.task_entry.get().strip()
        new_due_date_str = self.due_date_entry.get().strip()
        new_priority = self.priority_var.get()
        new_details = self.details_text.get("1.0", tk.END).strip()

        if not new_task:
            messagebox.showerror("Input Error", "Task cannot be empty.")
            return
        if not new_due_date_str:
            messagebox.showerror("Input Error", "Due date cannot be empty.")
            return

        try:
            new_due_date_obj = datetime.strptime(new_due_date_str, DATE_FORMAT)
        except ValueError:
            messagebox.showerror("Input Error", f"Invalid due date format. Please use {DATE_FORMAT}.")
            return

        # Update the reminder object
        selected_reminder.task = new_task
        selected_reminder.due_date = new_due_date_obj
        selected_reminder.priority = new_priority
        selected_reminder.details = new_details
        

        self._sort_reminders()
        self._refresh_reminders_tree()
        self._clear_input_fields()
        self.add_button.config(state=tk.NORMAL)
        self.update_button.config(state=tk.DISABLED)
        self.status_var.set(f"Reminder '{new_task}' updated.")


    def _delete_selected_reminder(self):
        selected_reminder = self._get_selected_reminder_object()
        if selected_reminder:
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete reminder: '{selected_reminder.task}'?"):
                task_name = selected_reminder.task
                self.reminders_list.remove(selected_reminder)
                self._sort_reminders() # Re-sort in case order matters for display index
                self._refresh_reminders_tree()
                self._clear_input_fields() # Clear fields if the deleted item was loaded
                self.status_var.set(f"Reminder '{task_name}' deleted.")
        else:
            messagebox.showinfo("Delete", "No reminder selected to delete.")

    def _delete_all_reminders(self):
        if messagebox.askyesno("Confirm Delete All", "Are you sure you want to delete ALL reminders? This cannot be undone from the UI."):
            self.reminders_list.clear()
            self._refresh_reminders_tree()
            self._clear_input_fields()
            self.status_var.set("All reminders deleted.")


    def _toggle_complete_selected(self, event=None): # event=None for button click
        selected_reminder = self._get_selected_reminder_object()
        if selected_reminder:
            selected_reminder.is_completed = not selected_reminder.is_completed
            self._sort_reminders()
            self._refresh_reminders_tree()
            action = "completed" if selected_reminder.is_completed else "marked as pending"
            self.status_var.set(f"Reminder '{selected_reminder.task}' {action}.")
            # Re-select the item to maintain focus and update button states
            try:
                # This might be tricky if sorting changes the index drastically
                # For now, just clear selection to avoid issues and let user re-select
                if self.reminders_tree.selection():
                    self.reminders_tree.selection_remove(self.reminders_tree.selection()[0])
                self._on_reminder_select() # Update button states
            except Exception as e:
                print(f"Error re-selecting after toggle: {e}")
                self._on_reminder_select() # Ensure buttons are in correct state
        else:
            messagebox.showinfo("Toggle Complete", "No reminder selected.")


    def _save_reminders(self, filename=None):
        if filename is None:
            filename = self.current_filename
        if not filename: # Should not happen if current_filename has a default
            messagebox.showerror("Save Error", "No filename specified.")
            return

        try:
            data_to_save = [r.to_dict() for r in self.reminders_list]
            with open(filename, "w") as f:
                json.dump(data_to_save, f, indent=4)
            self.current_filename = filename # Update current filename if save was successful
            self.root.title(f"Advanced Reminder App - {filename}")
            self.status_var.set(f"Reminders saved to {filename}.")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save reminders: {e}")
            self.status_var.set(f"Error saving reminders: {e}")

    def _save_reminders_as_dialog(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Reminders As..."
        )
        if filename: # If a filename was chosen (i.e., dialog not cancelled)
            self._save_reminders(filename)


    def _load_reminders_on_startup(self):
        """Loads reminders from the default file if it exists."""
        try:
            if DEFAULT_FILENAME and open(DEFAULT_FILENAME, "r"): # Check if file exists and is readable
                 self._load_reminders_core(DEFAULT_FILENAME)
                 self.status_var.set(f"Reminders loaded from {self.current_filename}.")
        except FileNotFoundError:
            self.status_var.set(f"No default reminder file found at '{DEFAULT_FILENAME}'. Starting fresh.")
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load reminders on startup from {DEFAULT_FILENAME}: {e}")
            self.status_var.set(f"Error loading reminders on startup: {e}")

    def _load_reminders_dialog(self):
        filename = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Open Reminders File"
        )
        if filename:
            self._load_reminders_core(filename)


    def _load_reminders_core(self, filename):
        try:
            with open(filename, "r") as f:
                data_loaded = json.load(f)
            self.reminders_list = [Reminder.from_dict(item) for item in data_loaded]
            self._sort_reminders()
            self._refresh_reminders_tree()
            self.current_filename = filename
            self.root.title(f"Advanced Reminder App - {filename}")
            self.status_var.set(f"Reminders loaded from {filename}.")
        except FileNotFoundError:
            messagebox.showerror("Load Error", f"File not found: {filename}")
            self.status_var.set(f"Error: File not found - {filename}")
        except json.JSONDecodeError:
            messagebox.showerror("Load Error", f"Error decoding JSON from file: {filename}. File might be corrupted or not a valid JSON.")
            self.status_var.set(f"Error decoding JSON from {filename}")
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load reminders: {e}")
            self.status_var.set(f"Error loading reminders: {e}")

    def _show_about(self):
        about_text = (
            "Advanced Reminder App\n\n"
            "Version: 1.0\n"
            "Created using Tkinter in Python.\n\n"
            "Features:\n"
            "- Add, edit, delete reminders\n"
            "- Set due dates and priorities\n"
            "- Mark reminders as complete\n"
            "- Save and load reminders from JSON files\n"
            "- Sortable and filterable list (implicitly by sorting)\n"
            "- Optional details for each reminder"
        )
        messagebox.showinfo("About Advanced Reminder App", about_text)


if __name__ == "__main__":
    root = tk.Tk()
    app = ReminderApp(root)
    root.mainloop()