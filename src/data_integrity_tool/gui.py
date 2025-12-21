import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk
import threading
from pathlib import Path
from .core import create_hashes, verify_archive_integrity, get_archive_content_hash, calculate_file_hash, find_hash_files

class DataIntegrityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Data Integrity Tool")
        self.root.geometry("600x500")

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        self.create_tab = ttk.Frame(self.notebook)
        self.verify_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.create_tab, text='Create Hash')
        self.notebook.add(self.verify_tab, text='Verify Hash')

        self.setup_create_tab()
        self.setup_verify_tab()

        # Log area at the bottom
        self.log_area = scrolledtext.ScrolledText(root, height=10, state='disabled')
        self.log_area.pack(fill='x', padx=10, pady=5)

    def log(self, message):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def setup_create_tab(self):
        frame = ttk.Frame(self.create_tab, padding="20")
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text="Select Archive to Hash:").pack(anchor='w')
        
        file_frame = ttk.Frame(frame)
        file_frame.pack(fill='x', pady=5)
        
        self.create_file_path = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.create_file_path).pack(side='left', fill='x', expand=True)
        ttk.Button(file_frame, text="Browse", command=lambda: self.browse_file(self.create_file_path)).pack(side='right', padx=5)

        ttk.Button(frame, text="Generate Hashes", command=self.run_create_hash).pack(pady=20)

    def setup_verify_tab(self):
        frame = ttk.Frame(self.verify_tab, padding="20")
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text="Select Archive to Verify:").pack(anchor='w')
        
        file_frame = ttk.Frame(frame)
        file_frame.pack(fill='x', pady=5)
        
        self.verify_file_path = tk.StringVar()
        self.verify_file_path.trace_add("write", self.on_verify_path_change)
        ttk.Entry(file_frame, textvariable=self.verify_file_path).pack(side='left', fill='x', expand=True)
        ttk.Button(file_frame, text="Browse", command=lambda: self.browse_file(self.verify_file_path)).pack(side='right', padx=5)

        # Archive Hash File Input
        ttk.Label(frame, text="Archive Hash File (Optional):").pack(anchor='w', pady=(10, 0))
        archive_hash_frame = ttk.Frame(frame)
        archive_hash_frame.pack(fill='x', pady=5)
        self.archive_hash_path = tk.StringVar()
        ttk.Entry(archive_hash_frame, textvariable=self.archive_hash_path).pack(side='left', fill='x', expand=True)
        ttk.Button(archive_hash_frame, text="Browse", command=lambda: self.browse_file(self.archive_hash_path)).pack(side='right', padx=5)

        # Content Hash File Input
        ttk.Label(frame, text="Content Hash File (Optional):").pack(anchor='w', pady=(10, 0))
        content_hash_frame = ttk.Frame(frame)
        content_hash_frame.pack(fill='x', pady=5)
        self.content_hash_path = tk.StringVar()
        ttk.Entry(content_hash_frame, textvariable=self.content_hash_path).pack(side='left', fill='x', expand=True)
        ttk.Button(content_hash_frame, text="Browse", command=lambda: self.browse_file(self.content_hash_path)).pack(side='right', padx=5)

        ttk.Button(frame, text="Verify Integrity", command=self.run_verify_hash).pack(pady=20)

    def browse_file(self, var):
        filename = filedialog.askopenfilename(filetypes=[("Archives", "*.zip *.7z *.rar *.tar *.gz"), ("All Files", "*.*")])
        if filename:
            var.set(filename)

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

    def run_create_hash(self):
        path = self.create_file_path.get()
        if not path:
            messagebox.showerror("Error", "Please select a file.")
            return
        
        self.log(f"Starting hash creation for: {path}")
        threading.Thread(target=self._create_hash_thread, args=(Path(path),), daemon=True).start()

    def _create_hash_thread(self, archive_path):
        try:
            if not verify_archive_integrity(archive_path):
                 self.root.after(0, lambda: messagebox.showerror("Error", "Not a valid archive."))
                 return

            self.root.after(0, lambda: self.log("Layer 1: Generating Archive File Hash..."))
            hash_file, content_hash_file = create_hashes(archive_path)
            self.root.after(0, lambda: self.log(f"Created {hash_file.name}"))
            
            if content_hash_file:
                self.root.after(0, lambda: self.log(f"Created {content_hash_file.name}"))
            
            self.root.after(0, lambda: messagebox.showinfo("Success", "Hashes created successfully."))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.root.after(0, lambda: self.log(f"Error: {e}"))

    def run_verify_hash(self):
        path = self.verify_file_path.get()
        if not path:
            messagebox.showerror("Error", "Please select a file.")
            return
        
        self.log(f"Starting verification for: {path}")
        
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
                self.root.after(0, lambda: self.log(f"Layer 1: Checking {hash_file.name}..."))
                with open(hash_file, "r") as f:
                    expected = f.read().split()[0].strip().lower()
                actual = calculate_file_hash(archive_path)
                if expected != actual:
                    self.root.after(0, lambda: self.log("Layer 1: MISMATCH!"))
                else:
                    self.root.after(0, lambda: self.log("Layer 1: PASS"))
            else:
                self.root.after(0, lambda: self.log("Layer 1: SKIPPED (No hash file)"))

            # Layer 2
            self.root.after(0, lambda: self.log("Layer 2: Checking 7z CRC..."))
            if verify_archive_integrity(archive_path):
                self.root.after(0, lambda: self.log("Layer 2: PASS"))
            else:
                self.root.after(0, lambda: self.log("Layer 2: FAIL"))
                self.root.after(0, lambda: messagebox.showerror("Failure", "Layer 2 check failed."))
                return

            # Layer 3
            content_hash_file = Path(content_hash_path_str) if content_hash_path_str else None
            
            # If not provided, try default discovery
            if not content_hash_file:
                potential = Path(str(archive_path) + ".content.sha256")
                if potential.exists():
                    content_hash_file = potential

            if content_hash_file and content_hash_file.exists():
                self.root.after(0, lambda: self.log(f"Layer 3: Checking {content_hash_file.name}..."))
                with open(content_hash_file, "r") as f:
                    expected = f.read().strip().lower()
                actual = get_archive_content_hash(archive_path)
                if actual and actual.lower() == expected:
                    self.root.after(0, lambda: self.log("Layer 3: PASS"))
                else:
                    self.root.after(0, lambda: self.log("Layer 3: MISMATCH!"))
            else:
                self.root.after(0, lambda: self.log("Layer 3: SKIPPED"))

            self.root.after(0, lambda: messagebox.showinfo("Done", "Verification complete. Check logs."))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.root.after(0, lambda: self.log(f"Error: {e}"))

def main():
    root = tk.Tk()
    app = DataIntegrityApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
