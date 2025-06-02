import os
import json
import threading
import time
import datetime
import tkinter as tk
from tkinter import scrolledtext, ttk, filedialog, messagebox

from voice_engine import VoiceAssistant  

MODEL_PATH = "vosk-model-small-en-us-0.15"
TRANSLATION_FILE = "translations.json"

class VoiceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Offline Voice Assistant")
        self.root.geometry("800x650")
        self.root.resizable(False, False)

        # Load local translation dataset
        if os.path.exists(TRANSLATION_FILE):
            with open(TRANSLATION_FILE, "r", encoding="utf8") as f:
                self.translations = json.load(f)
        else:
            self.translations = {}
        # list of available language codes
        codes = {lang for entry in self.translations.values() for lang in entry.keys()}
        self.lang_list = ["None"] + sorted(codes)

        # Backend assistant
        self.assistant = VoiceAssistant(MODEL_PATH)
        self.listening = False

        # Stats & logs
        os.makedirs("logs", exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.timestamp       = ts
        self.transcript_path = os.path.join("logs", f"transcript_{ts}.txt")
        self.summary_path    = os.path.join("logs", f"session_summary_{ts}.txt")
        self.transcript_file = open(self.transcript_path, "w")
        self.start_time      = None
        self.word_count      = 0
        self.command_count   = 0

        # === Menu Bar ===
        menubar = tk.Menu(root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Export Transcript...", command=self.export_transcript)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.close_app)
        menubar.add_cascade(label="File", menu=file_menu)
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        root.config(menu=menubar)

        # === Translation Selector ===
        ctrl = tk.Frame(root)
        ctrl.pack(pady=5)
        tk.Label(ctrl, text="Translate to:").grid(row=0, column=0, padx=5)
        self.target_lang = tk.StringVar(value="None")
        self.lang_menu = ttk.Combobox(
            ctrl,
            textvariable=self.target_lang,
            values=self.lang_list,
            state='readonly',
            width=20
        )
        self.lang_menu.grid(row=0, column=1, padx=5)

        # === Transcript area ===
        self.text_area = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, font=("Consolas", 11)
        )
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Status & partial labels
        self.status_label = tk.Label(
            root, text="🟢 Ready", anchor=tk.W,
            font=("Arial", 12, "bold")
        )
        self.status_label.pack(fill=tk.X)
        self.partial_label = tk.Label(
            root, text="", anchor=tk.W, font=("Arial", 10)
        )
        self.partial_label.pack(fill=tk.X)

        # Control buttons
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)
        self.start_btn = ttk.Button(btn_frame, text="🎙️ Start", command=self.start_listening)
        self.start_btn.grid(row=0, column=0, padx=10)
        self.stop_btn  = ttk.Button(btn_frame, text="⏹️ Stop", command=self.stop_listening, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=10)
        self.close_btn = ttk.Button(btn_frame, text="❌ Close", command=self.close_app)
        self.close_btn.grid(row=0, column=2, padx=10)

    def show_about(self):
        about_text = (
            "Offline Voice Assistant\n"
            "Version 1.0\n\n"
            "• Live speech transcription\n"
            "• Command recognition\n"
            "• Offline translation via your dataset\n\n"
            "Controls:\n"
            "- Start: begin transcription\n"
            "- Stop: end session & save logs\n"
            "- Close: exit application\n\n"
            "Developed by: Your Name"
        )
        messagebox.showinfo("About", about_text)

    def export_transcript(self):
        file = filedialog.asksaveasfilename(
            defaultextension='.txt',
            filetypes=[('Text Files','*.txt')],
            initialfile=f"transcript_{self.timestamp}.txt"
        )
        if file:
            with open(self.transcript_path) as src, open(file, 'w') as dst:
                dst.write(src.read())
            self.update_status("📁 Transcript exported")

    def start_listening(self):
        self.listening       = True
        self.start_time      = time.time()
        self.word_count      = 0
        self.command_count   = 0
        self.update_status("🎤 Listening...")
        self.partial_label.config(text="")
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        threading.Thread(
            target=lambda: self.assistant.listen(
                self.display_text,
                self.handle_command,
                self.display_partial
            ),
            daemon=True
        ).start()

    def stop_listening(self):
        self.assistant.stop()
        self.listening = False
        self.update_status("🟡 Stopped.")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.transcript_file.close()
        self.write_summary()

    def close_app(self):
        if self.listening:
            self.assistant.stop()
        self.transcript_file.close()
        self.root.destroy()

    def display_partial(self, text):
        self.partial_label.config(text=f"… {text}")

    def display_text(self, text):
        self.partial_label.config(text="")
        # Original transcription
        self.text_area.insert(tk.END, f"You said: {text}\n")
        # Offline translation lookup
        tgt = self.target_lang.get()
        if tgt != "None":
            key = text.strip().lower()
            entry = self.translations.get(key)
            if entry and tgt in entry:
                tr = entry[tgt]
                self.text_area.insert(tk.END, f"Translation ({tgt}): {tr}\n")
            else:
                self.text_area.insert(tk.END, f"(no translation for '{key}')\n")
        self.text_area.see(tk.END)
        # Log & stats
        self.transcript_file.write(text + "\n")
        self.transcript_file.flush()
        self.word_count += len(text.split())

    def handle_command(self, command):
        self.text_area.insert(tk.END, f"✅ Command: {command}\n")
        self.text_area.see(tk.END)
        self.update_status(f"⚙️ {command}")
        self.assistant.speak(f"{command} command detected")
        self.command_count += 1
        if command == "exit":
            self.close_app()

    def update_status(self, msg):
        self.status_label.config(text=msg)

    def write_summary(self):
        duration = time.time() - self.start_time if self.start_time else 0
        with open(self.summary_path, 'w') as summary:
            summary.write(f"Session Summary - {self.timestamp}\n")
            summary.write(f"Duration: {round(duration,2)} seconds\n")
            summary.write(f"Total Words Spoken: {self.word_count}\n")
            summary.write(f"Commands Executed: {self.command_count}\n")
        self.text_area.insert(tk.END, f"\nSummary saved to {self.summary_path}\n")

if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style(root)
    style.theme_use('clam')
    app = VoiceApp(root)
    root.mainloop()
