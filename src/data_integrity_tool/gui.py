import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk
import threading
import webbrowser
from pathlib import Path
from .core import create_hashes, verify_archive_integrity, get_archive_content_hash, calculate_file_hash, find_hash_files, verify_layers, ArchiveError, DependencyError

try:
    from ._build_info import VERSION, AUTHOR, URL
except ImportError:
    VERSION = "Dev"
    AUTHOR = "Unknown"
    URL = "Unknown"

class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = tk.Canvas(self, borderwidth=0, background="#f0f2f5")
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas, style="TFrame")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel (Windows/macOS)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        # Bind mousewheel (Linux)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)
        
        # Bind canvas resize to update inner frame width
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_mousewheel(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        else:
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _on_canvas_configure(self, event):
        # Resize the inner frame to match the canvas width
        self.canvas.itemconfig(self.canvas_window, width=event.width)

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show)
        self.widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 25

        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = tk.Label(self.tooltip, text=self.text, background="#ffffe0", relief="solid", borderwidth=1,
                         font=("Helvetica", 9), justify='left', padx=5, pady=3)
        label.pack()

    def hide(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

class DataIntegrityApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"Data Integrity Tool - v{VERSION}")
        self.geometry("800x600") # Increased default size
        self.minsize(600, 500)   # Set minimum size
        
        # Configure Styles
        self.style = ttk.Style(self)
        self.style.theme_use('clam') # Use a theme that allows more customization
        
        # Colors
        self.bg_color = "#f0f2f5"
        self.primary_color = "#007bff"
        self.secondary_color = "#6c757d"
        self.text_color = "#212529"
        
        self.configure(bg=self.bg_color)
        
        self.style.configure("TFrame", background=self.bg_color)
        self.style.configure("TLabel", background=self.bg_color, foreground=self.text_color, font=("Helvetica", 11))
        self.style.configure("Header.TLabel", font=("Helvetica", 24, "bold"), foreground=self.primary_color)
        self.style.configure("SubHeader.TLabel", font=("Helvetica", 14), foreground=self.secondary_color)
        
        self.style.configure("TButton", font=("Helvetica", 11), padding=10)
        self.style.map("TButton",
            foreground=[('pressed', 'white'), ('active', 'white')],
            background=[('pressed', '!disabled', self.primary_color), ('active', self.primary_color)]
        )
        
        self.style.configure("Primary.TButton", background=self.primary_color, foreground="white")
        self.style.map("Primary.TButton",
             background=[('active', '#0056b3')], 
             foreground=[('active', 'white')]
        )

        # Status Styles
        self.style.configure("Success.TLabel", foreground="green", font=("Helvetica", 11, "bold"))
        self.style.configure("Failure.TLabel", foreground="red", font=("Helvetica", 11, "bold"))
        self.style.configure("Skipped.TLabel", foreground="#ff8c00", font=("Helvetica", 11, "bold")) # DarkOrange
        self.style.configure("Pending.TLabel", foreground="gray", font=("Helvetica", 11))

        self.container = ttk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (HomePage, CreatePage, VerifyPage):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("HomePage")

        # Menu
        menubar = tk.Menu(self)
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.config(menu=menubar)

    def show_about(self):
        about_window = tk.Toplevel(self)
        about_window.title("About")
        about_window.geometry("400x250")
        about_window.resizable(False, False)
        about_window.configure(bg=self.bg_color)

        # Center the window
        about_window.transient(self)
        about_window.grab_set()
        
        # Content
        frame = ttk.Frame(about_window, padding=20)
        frame.pack(fill="both", expand=True)
        
        ttk.Label(frame, text="Data Integrity Tool", font=("Helvetica", 16, "bold")).pack(pady=(0, 10))
        ttk.Label(frame, text=f"Version: {VERSION}").pack(pady=2)
        ttk.Label(frame, text=f"Author: {AUTHOR}").pack(pady=2)
        
        url_label = tk.Label(frame, text=URL, fg="blue", cursor="hand2", bg=self.bg_color, font=("Helvetica", 10, "underline"))
        url_label.pack(pady=10)
        url_label.bind("<Button-1>", lambda e: webbrowser.open_new(URL))
        
        ttk.Button(frame, text="Close", command=about_window.destroy).pack(pady=(20, 0))

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        if hasattr(frame, 'reset'):
            frame.reset()
        frame.tkraise()

class HomePage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Center content
        center_frame = ttk.Frame(self)
        center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        label = ttk.Label(center_frame, text="Data Integrity Tool", style="Header.TLabel")
        label.pack(pady=(0, 5))
        
        version_label = ttk.Label(center_frame, text=f"v{VERSION}", style="SubHeader.TLabel", font=("Helvetica", 10))
        version_label.pack(pady=(0, 10))
        
        sub_label = ttk.Label(center_frame, text="Select an action to proceed", style="SubHeader.TLabel")
        sub_label.pack(pady=(0, 40))

        create_btn = ttk.Button(center_frame, text="Create Hash", style="Primary.TButton",
                                command=lambda: controller.show_frame("CreatePage"))
        create_btn.pack(fill="x", pady=10, ipadx=20)

        verify_btn = ttk.Button(center_frame, text="Verify Hash", style="Primary.TButton",
                                command=lambda: controller.show_frame("VerifyPage"))
        verify_btn.pack(fill="x", pady=10, ipadx=20)

class CreatePage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Use ScrollableFrame
        self.scroll_frame = ScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True)
        
        # Content goes into scroll_frame.scrollable_frame
        content_parent = self.scroll_frame.scrollable_frame

        # Header
        header_frame = ttk.Frame(content_parent)
        header_frame.pack(fill="x", padx=20, pady=20)
        
        home_btn = ttk.Button(header_frame, text="← Back to Home", 
                              command=lambda: controller.show_frame("HomePage"))
        home_btn.pack(side="left")
        
        title = ttk.Label(header_frame, text="Create Hash", style="Header.TLabel", font=("Helvetica", 18, "bold"))
        title.pack(side="left", padx=20)

        # Content
        content_frame = ttk.Frame(content_parent, padding=20)
        content_frame.pack(fill="both", expand=True)
        
        ttk.Label(content_frame, text="Select Archive to Hash:").pack(anchor='w')
        
        file_frame = ttk.Frame(content_frame)
        file_frame.pack(fill='x', pady=5)
        
        self.create_file_path = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.create_file_path).pack(side='left', fill='x', expand=True, padx=(0, 10))
        ttk.Button(file_frame, text="Browse", command=lambda: self.browse_file(self.create_file_path)).pack(side='right')

        ttk.Button(content_frame, text="Generate Hashes", style="Primary.TButton", 
                   command=self.run_create_hash).pack(pady=30)

        # Results Area
        self.results_frame = ttk.LabelFrame(content_frame, text="Results", padding=10)
        self.results_frame.pack(fill="x", pady=(0, 20))
        
        self.lbl_hash_file = ttk.Label(self.results_frame, text="Hash File: -", style="Pending.TLabel")
        self.lbl_hash_file.pack(anchor="w")
        
        self.lbl_content_hash = ttk.Label(self.results_frame, text="Content Hash File: -", style="Pending.TLabel")
        self.lbl_content_hash.pack(anchor="w")

        # Log Area
        ttk.Label(content_frame, text="Logs:").pack(anchor='w')
        self.log_area = scrolledtext.ScrolledText(content_frame, height=10, state='disabled', font=("Consolas", 9))
        self.log_area.pack(fill='both', expand=True, pady=5)

    def browse_file(self, var):
        filename = filedialog.askopenfilename(filetypes=[("Archives", "*.zip *.7z *.rar *.tar *.gz"), ("All Files", "*.*")])
        if filename:
            var.set(filename)

    def log(self, message):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def reset(self):
        self.create_file_path.set("")
        self.log_area.config(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state='disabled')
        
        # Reset results
        self.set_status(self.lbl_hash_file, "Hash File: -", "Pending.TLabel")
        self.set_status(self.lbl_content_hash, "Content Hash File: -", "Pending.TLabel")

    def set_status(self, label, text, style):
        label.config(text=text, style=style)

    def run_create_hash(self):
        path = self.create_file_path.get()
        if not path:
            messagebox.showerror("Error", "Please select a file.")
            return
        
        self.log(f"Starting hash creation for: {path}")
        
        # Reset statuses
        self.set_status(self.lbl_hash_file, "Hash File: Pending...", "Pending.TLabel")
        self.set_status(self.lbl_content_hash, "Content Hash File: Pending...", "Pending.TLabel")
        
        threading.Thread(target=self._create_hash_thread, args=(Path(path),), daemon=True).start()

    def _create_hash_thread(self, archive_path):
        try:
            if not verify_archive_integrity(archive_path):
                 self.after(0, lambda: messagebox.showerror("Error", "Not a valid archive."))
                 return

            self.after(0, lambda: self.log("Generating Archive File Hash..."))
            hash_file, content_hash_file = create_hashes(archive_path)
            self.after(0, lambda: self.log(f"Created {hash_file.name}"))
            self.after(0, lambda: self.set_status(self.lbl_hash_file, f"Hash File: {hash_file.name} \u2714", "Success.TLabel"))
            
            if content_hash_file:
                self.after(0, lambda: self.log(f"Created {content_hash_file.name}"))
                self.after(0, lambda: self.set_status(self.lbl_content_hash, f"Content Hash File: {content_hash_file.name} \u2714", "Success.TLabel"))
            else:
                self.after(0, lambda: self.set_status(self.lbl_content_hash, "Content Hash File: N/A", "Pending.TLabel"))
            

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.after(0, lambda: self.log(f"Error: {e}"))
            self.after(0, lambda: self.set_status(self.lbl_hash_file, "Hash File: Failed \u2718", "Failure.TLabel"))
            self.after(0, lambda: self.set_status(self.lbl_content_hash, "Content Hash File: Failed \u2718", "Failure.TLabel"))

class VerifyPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Use ScrollableFrame
        self.scroll_frame = ScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True)
        
        # Content goes into scroll_frame.scrollable_frame
        content_parent = self.scroll_frame.scrollable_frame
        
        # Header
        header_frame = ttk.Frame(content_parent)
        header_frame.pack(fill="x", padx=20, pady=20)
        
        home_btn = ttk.Button(header_frame, text="← Back to Home", 
                              command=lambda: controller.show_frame("HomePage"))
        home_btn.pack(side="left")
        
        title = ttk.Label(header_frame, text="Verify Hash", style="Header.TLabel", font=("Helvetica", 18, "bold"))
        title.pack(side="left", padx=20)

        # Content
        content_frame = ttk.Frame(content_parent, padding=20)
        content_frame.pack(fill="both", expand=True)

        ttk.Label(content_frame, text="Select Archive to Verify:").pack(anchor='w')
        
        file_frame = ttk.Frame(content_frame)
        file_frame.pack(fill='x', pady=5)
        
        self.verify_file_path = tk.StringVar()
        self.verify_file_path.trace_add("write", self.on_verify_path_change)
        ttk.Entry(file_frame, textvariable=self.verify_file_path).pack(side='left', fill='x', expand=True, padx=(0, 10))
        ttk.Button(file_frame, text="Browse", command=lambda: self.browse_file(self.verify_file_path)).pack(side='right')

        # Archive Hash File Input
        ttk.Label(content_frame, text="Archive Hash File (Optional):").pack(anchor='w', pady=(10, 0))
        archive_hash_frame = ttk.Frame(content_frame)
        archive_hash_frame.pack(fill='x', pady=5)
        self.archive_hash_path = tk.StringVar()
        ttk.Entry(archive_hash_frame, textvariable=self.archive_hash_path).pack(side='left', fill='x', expand=True, padx=(0, 10))
        ttk.Button(archive_hash_frame, text="Browse", command=lambda: self.browse_file(self.archive_hash_path)).pack(side='right')

        # Content Hash File Input
        ttk.Label(content_frame, text="Content Hash File (Optional):").pack(anchor='w', pady=(10, 0))
        content_hash_frame = ttk.Frame(content_frame)
        content_hash_frame.pack(fill='x', pady=5)
        self.content_hash_path = tk.StringVar()
        ttk.Entry(content_hash_frame, textvariable=self.content_hash_path).pack(side='left', fill='x', expand=True, padx=(0, 10))
        ttk.Button(content_hash_frame, text="Browse", command=lambda: self.browse_file(self.content_hash_path)).pack(side='right')

        ttk.Button(content_frame, text="Verify Integrity", style="Primary.TButton", 
                   command=self.run_verify_hash).pack(pady=30)

        # Results Area
        self.results_frame = ttk.LabelFrame(content_frame, text="Verification Results", padding=10)
        self.results_frame.pack(fill="x", pady=(0, 20))
        
        # Structure - Layer 1 (Old Layer 2)
        l1_frame = ttk.Frame(self.results_frame)
        l1_frame.pack(fill='x', pady=2)
        self.lbl_structure = ttk.Label(l1_frame, text="1. Data Structure: -", style="Pending.TLabel")
        self.lbl_structure.pack(side='left')
        tip_structure = tk.Label(l1_frame, text="(?)", fg="blue", cursor="hand2", bg=self.controller.bg_color)
        tip_structure.pack(side='left', padx=5)
        ToolTip(tip_structure, "Verifies the internal structure of the archive to ensure it is not corrupted.")

        # Content - Layer 2 (Old Layer 3)
        l2_frame = ttk.Frame(self.results_frame)
        l2_frame.pack(fill='x', pady=2)
        self.lbl_content = ttk.Label(l2_frame, text="2. Content Authenticity: -", style="Pending.TLabel")
        self.lbl_content.pack(side='left')
        tip_content = tk.Label(l2_frame, text="(?)", fg="blue", cursor="hand2", bg=self.controller.bg_color)
        tip_content.pack(side='left', padx=5)
        ToolTip(tip_content, "Verifies the actual content against the original source.\nA match confirms the data is authentic and has not been tampered with (e.g., malware injection).")

        # Archive - Layer 3 (Old Layer 1)
        l3_frame = ttk.Frame(self.results_frame)
        l3_frame.pack(fill='x', pady=2)
        self.lbl_archive = ttk.Label(l3_frame, text="3. Archive File: -", style="Pending.TLabel")
        self.lbl_archive.pack(side='left')
        tip_archive = tk.Label(l3_frame, text="(?)", fg="blue", cursor="hand2", bg=self.controller.bg_color)
        tip_archive.pack(side='left', padx=5)
        ToolTip(tip_archive, "Verifies if the archive file itself is the exact original file.\nIf this fails but Content/Structure pass, the data was likely re-archived but is still safe.")

        # Log Area
        ttk.Label(content_frame, text="Logs:").pack(anchor='w')
        self.log_area = scrolledtext.ScrolledText(content_frame, height=10, state='disabled', font=("Consolas", 9))
        self.log_area.pack(fill='both', expand=True, pady=5)

    def browse_file(self, var):
        filename = filedialog.askopenfilename(filetypes=[("Archives", "*.zip *.7z *.rar *.tar *.gz"), ("All Files", "*.*")])
        if filename:
            var.set(filename)

    def log(self, message):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def reset(self):
        self.verify_file_path.set("")
        self.archive_hash_path.set("")
        self.content_hash_path.set("")
        self.log_area.config(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state='disabled')
        
        # Reset results
        self.set_status(self.lbl_structure, "1. Data Structure: -", "Pending.TLabel")
        self.set_status(self.lbl_content, "2. Content Authenticity: -", "Pending.TLabel")
        self.set_status(self.lbl_archive, "3. Archive File: -", "Pending.TLabel")

    def set_status(self, label, text, style):
        label.config(text=text, style=style)

    def on_verify_path_change(self, *args):
        path_str = self.verify_file_path.get()
        if path_str:
             self.check_hashes_for_file(path_str)
        else:
             self.archive_hash_path.set("")
             self.content_hash_path.set("")

    def check_hashes_for_file(self, filename):
        path = Path(filename)
        found = find_hash_files(path)
        
        if found['archive_hash']:
            self.archive_hash_path.set(str(found['archive_hash']))
        else:
            self.archive_hash_path.set("")
            
        if found['content_hash']:
            self.content_hash_path.set(str(found['content_hash']))
        else:
            self.content_hash_path.set("")

    def run_verify_hash(self):
        path = self.verify_file_path.get()
        if not path:
            messagebox.showerror("Error", "Please select a file.")
            return
        
        self.log(f"Starting verification for: {path}")
        
        # Reset statuses
        self.set_status(self.lbl_structure, "1. Data Structure: Pending...", "Pending.TLabel")
        self.set_status(self.lbl_content, "2. Content Authenticity: Pending...", "Pending.TLabel")
        self.set_status(self.lbl_archive, "3. Archive File: Pending...", "Pending.TLabel")
        
        archive_hash = self.archive_hash_path.get()
        content_hash = self.content_hash_path.get()
        
        threading.Thread(target=self._verify_hash_thread, args=(Path(path), archive_hash, content_hash), daemon=True).start()

    def _verify_hash_thread(self, archive_path, archive_hash_path_str, content_hash_path_str):
        try:
            # Use centralized verification logic
            results = verify_layers(archive_path, Path(archive_hash_path_str) if archive_hash_path_str else None, Path(content_hash_path_str) if content_hash_path_str else None)

            # --- New Layer 1: Structure (Old Layer 2) ---
            l2 = results["layer2"]
            self.after(0, lambda: self.log("Checking Data Structure (7z integrity)..."))
            
            if l2["status"] == "PASSED":
                self.after(0, lambda: self.log("Structure Check: PASS"))
                self.after(0, lambda: self.set_status(self.lbl_structure, "1. Data Structure: PASSED: Valid Structure \u2714", "Success.TLabel"))
            else:
                self.after(0, lambda: self.log(f"Structure Check: FAIL ({l2['message']})"))
                self.after(0, lambda: self.set_status(self.lbl_structure, "1. Data Structure: FAILED: Corrupted Structure \u2718", "Failure.TLabel"))
                
                # Stop if structure invalid?
                if l2["status"] == "FAILED":
                     self.after(0, lambda: messagebox.showerror("Failure", f"Structure check failed: {l2['message']}"))
                     return

            # --- New Layer 2: Content Authenticity (Old Layer 3) ---
            l3 = results["layer3"]
            self.after(0, lambda: self.log("Checking Content Authenticity..."))

            content_passed = False
            if l3["status"] == "PASSED":
                content_passed = True
                self.after(0, lambda: self.log("Content Check: PASS"))
                self.after(0, lambda: self.set_status(self.lbl_content, "2. Content Authenticity: PASSED: Matches Original Source \u2714", "Success.TLabel"))
            elif l3["status"] == "FAILED":
                self.after(0, lambda: self.log(f"Content Check: FAIL - Expected: {l3.get('details', {}).get('expected')} Actual: {l3.get('details', {}).get('actual')}"))
                self.after(0, lambda: self.set_status(self.lbl_content, "2. Content Authenticity: FAILED: Content Mismatch / Tampered \u2718", "Failure.TLabel"))
            elif l3["status"] == "ERROR":
                self.after(0, lambda: self.log(f"Content Check: ERROR: {l3['message']}"))
                self.after(0, lambda: self.set_status(self.lbl_content, f"2. Content Authenticity: FAILED: Error ({l3['message']}) \u2718", "Failure.TLabel"))
            else: # SKIPPED
                self.after(0, lambda: self.log(f"Content Check: SKIPPED ({l3['message']})"))
                self.after(0, lambda: self.set_status(self.lbl_content, f"2. Content Authenticity: SKIPPED: {l3['message']} \u2013", "Skipped.TLabel"))

            # --- New Layer 3: Archive File (Old Layer 1) ---
            l1 = results["layer1"]
            self.after(0, lambda: self.log("Checking Archive File Hash..."))
            
            if l1["status"] == "PASSED":
                 self.after(0, lambda: self.log("Archive Check: PASS"))
                 self.after(0, lambda: self.set_status(self.lbl_archive, "3. Archive File: PASSED: Original File (Untouched) \u2714", "Success.TLabel"))
            elif l1["status"] == "WARNING":
                 self.after(0, lambda: self.log(f"Archive Check: MISMATCH! Expected: {l1.get('details', {}).get('expected')} Actual: {l1.get('details', {}).get('actual')}"))
                 # Check if we should say "Re-archived" or just failed
                 if content_passed:
                    self.after(0, lambda: self.set_status(self.lbl_archive, "3. Archive File: WARNING: Re-archived (Data Valid) \u26A0", "Skipped.TLabel")) # Orange for warning
                 else:
                    self.after(0, lambda: self.set_status(self.lbl_archive, "3. Archive File: FAILED: Modified \u2718", "Failure.TLabel"))
            elif l1["status"] == "ERROR":
                 self.after(0, lambda: self.log(f"Archive Check: ERROR: {l1['message']}"))
                 self.after(0, lambda: self.set_status(self.lbl_archive, f"3. Archive File: FAILED: Error ({l1['message']}) \u2718", "Failure.TLabel"))
            else: # SKIPPED
                 self.after(0, lambda: self.log(f"Archive Check: SKIPPED ({l1['message']})"))
                 self.after(0, lambda: self.set_status(self.lbl_archive, f"3. Archive File: SKIPPED: {l1['message']} \u2013", "Skipped.TLabel"))

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.after(0, lambda: self.log(f"Error: {e}"))


def main():
    app = DataIntegrityApp()
    app.mainloop()

if __name__ == "__main__":
    main()
