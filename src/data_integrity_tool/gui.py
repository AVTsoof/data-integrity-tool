import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk
import threading
from pathlib import Path
from .core import create_hashes, verify_archive_integrity, get_archive_content_hash, calculate_file_hash, find_hash_files

class DataIntegrityApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Data Integrity Tool")
        self.geometry("700x600")
        
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
        label.pack(pady=(0, 10))
        
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
        
        # Header
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", padx=20, pady=20)
        
        home_btn = ttk.Button(header_frame, text="← Back to Home", 
                              command=lambda: controller.show_frame("HomePage"))
        home_btn.pack(side="left")
        
        title = ttk.Label(header_frame, text="Create Hash", style="Header.TLabel", font=("Helvetica", 18, "bold"))
        title.pack(side="left", padx=20)

        # Content
        content_frame = ttk.Frame(self, padding=20)
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

            self.after(0, lambda: self.log("Layer 1: Generating Archive File Hash..."))
            hash_file, content_hash_file = create_hashes(archive_path)
            self.after(0, lambda: self.log(f"Created {hash_file.name}"))
            self.after(0, lambda: self.set_status(self.lbl_hash_file, f"Hash File: {hash_file.name} \u2714", "Success.TLabel"))
            
            if content_hash_file:
                self.after(0, lambda: self.log(f"Created {content_hash_file.name}"))
                self.after(0, lambda: self.set_status(self.lbl_content_hash, f"Content Hash File: {content_hash_file.name} \u2714", "Success.TLabel"))
            else:
                self.after(0, lambda: self.set_status(self.lbl_content_hash, "Content Hash File: N/A", "Pending.TLabel"))
            
            self.after(0, lambda: messagebox.showinfo("Success", "Hashes created successfully."))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.after(0, lambda: self.log(f"Error: {e}"))
            self.after(0, lambda: self.set_status(self.lbl_hash_file, "Hash File: Failed \u2718", "Failure.TLabel"))
            self.after(0, lambda: self.set_status(self.lbl_content_hash, "Content Hash File: Failed \u2718", "Failure.TLabel"))

class VerifyPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Header
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", padx=20, pady=20)
        
        home_btn = ttk.Button(header_frame, text="← Back to Home", 
                              command=lambda: controller.show_frame("HomePage"))
        home_btn.pack(side="left")
        
        title = ttk.Label(header_frame, text="Verify Hash", style="Header.TLabel", font=("Helvetica", 18, "bold"))
        title.pack(side="left", padx=20)

        # Content
        content_frame = ttk.Frame(self, padding=20)
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
        
        self.lbl_layer1 = ttk.Label(self.results_frame, text="Layer 1 (Archive Hash): -", style="Pending.TLabel")
        self.lbl_layer1.pack(anchor="w")
        
        self.lbl_layer2 = ttk.Label(self.results_frame, text="Layer 2 (Content Signature): -", style="Pending.TLabel")
        self.lbl_layer2.pack(anchor="w")

        self.lbl_layer3 = ttk.Label(self.results_frame, text="Layer 3 (Content Hash): -", style="Pending.TLabel")
        self.lbl_layer3.pack(anchor="w")

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
        self.set_status(self.lbl_layer1, "Layer 1 (Archive Hash): -", "Pending.TLabel")
        self.set_status(self.lbl_layer2, "Layer 2 (Content Signature): -", "Pending.TLabel")
        self.set_status(self.lbl_layer3, "Layer 3 (Content Hash): -", "Pending.TLabel")

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
        self.set_status(self.lbl_layer1, "Layer 1 (Archive Hash): Pending...", "Pending.TLabel")
        self.set_status(self.lbl_layer2, "Layer 2 (Content Signature): Pending...", "Pending.TLabel")
        self.set_status(self.lbl_layer3, "Layer 3 (Content Hash): Pending...", "Pending.TLabel")
        
        archive_hash = self.archive_hash_path.get()
        content_hash = self.content_hash_path.get()
        
        threading.Thread(target=self._verify_hash_thread, args=(Path(path), archive_hash, content_hash), daemon=True).start()

    def _verify_hash_thread(self, archive_path, archive_hash_path_str, content_hash_path_str):
        try:
            # Logic similar to CLI verify
            # Layer 1
            hash_file = Path(archive_hash_path_str) if archive_hash_path_str else None
            
            # If not provided, try default discovery (though UI should have handled it)
            if not hash_file:
                 potential = Path(str(archive_path) + ".sha256")
                 if potential.exists():
                     hash_file = potential

            if hash_file and hash_file.exists():
                self.after(0, lambda: self.log(f"Layer 1: Checking {hash_file.name}..."))
                with open(hash_file, "r") as f:
                    expected = f.read().split()[0].strip().lower()
                actual = calculate_file_hash(archive_path)
                if expected != actual:
                    self.after(0, lambda: self.log("Layer 1: MISMATCH!"))
                    self.after(0, lambda: self.set_status(self.lbl_layer1, "Layer 1 (Archive Hash): Failed \u2718", "Failure.TLabel"))
                else:
                    self.after(0, lambda: self.log("Layer 1: PASS"))
                    self.after(0, lambda: self.set_status(self.lbl_layer1, "Layer 1 (Archive Hash): Passed \u2714", "Success.TLabel"))
            else:
                self.after(0, lambda: self.log("Layer 1: SKIPPED (No hash file)"))
                self.after(0, lambda: self.set_status(self.lbl_layer1, "Layer 1 (Archive Hash): Skipped", "Pending.TLabel"))

            # Layer 2
            self.after(0, lambda: self.log("Layer 2: Checking 7z CRC..."))
            if verify_archive_integrity(archive_path):
                self.after(0, lambda: self.log("Layer 2: PASS"))
                self.after(0, lambda: self.set_status(self.lbl_layer2, "Layer 2 (Content Signature): Passed \u2714", "Success.TLabel"))
            else:
                self.after(0, lambda: self.log("Layer 2: FAIL"))
                self.after(0, lambda: self.set_status(self.lbl_layer2, "Layer 2 (Content Signature): Failed \u2718", "Failure.TLabel"))
                self.after(0, lambda: messagebox.showerror("Failure", "Layer 2 check failed."))
                return

            # Layer 3
            content_hash_file = Path(content_hash_path_str) if content_hash_path_str else None
            
            # If not provided, try default discovery
            if not content_hash_file:
                potential = Path(str(archive_path) + ".content.sha256")
                if potential.exists():
                    content_hash_file = potential

            if content_hash_file and content_hash_file.exists():
                self.after(0, lambda: self.log(f"Layer 3: Checking {content_hash_file.name}..."))
                with open(content_hash_file, "r") as f:
                    expected = f.read().strip().lower()
                actual = get_archive_content_hash(archive_path)
                if actual and actual.lower() == expected:
                    self.after(0, lambda: self.log("Layer 3: PASS"))
                    self.after(0, lambda: self.set_status(self.lbl_layer3, "Layer 3 (Content Hash): Passed \u2714", "Success.TLabel"))
                else:
                    self.after(0, lambda: self.log("Layer 3: MISMATCH!"))
                    self.after(0, lambda: self.set_status(self.lbl_layer3, "Layer 3 (Content Hash): Failed \u2718", "Failure.TLabel"))
            else:
                self.after(0, lambda: self.log("Layer 3: SKIPPED"))
                self.after(0, lambda: self.set_status(self.lbl_layer3, "Layer 3 (Content Hash): Skipped", "Pending.TLabel"))

            self.after(0, lambda: messagebox.showinfo("Done", "Verification complete. Check logs."))

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.after(0, lambda: self.log(f"Error: {e}"))

def main():
    app = DataIntegrityApp()
    app.mainloop()

if __name__ == "__main__":
    main()
