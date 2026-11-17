import tkinter as tk
from tkinter import ttk, messagebox
import json
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
DATA_FILE = APP_DIR / "focusflow_data.json"

COLORS = {
    "bg": "#101827",
    "panel": "#1b2940",
    "panel2": "#243550",
    "text": "#f3f6fc",
    "muted": "#a8b5c9",
    "accent": "#7c9cff",
    "green": "#55d6a5",
    "red": "#ff7b85",
}

class FocusFlow:
    def __init__(self, root):
        self.root = root
        self.root.title("FocusFlow | Pomodoro Timer")
        self.root.geometry("760x610")
        self.root.minsize(650, 560)
        self.root.configure(bg=COLORS["bg"])

        self.work_minutes = 25
        self.short_minutes = 5
        self.long_minutes = 15
        self.sessions_before_long = 4
        self.completed = 0
        self.mode = "Focus"
        self.remaining = self.work_minutes * 60
        self.running = False
        self.after_id = None
        self.tasks = []

        self.load_data()
        self.build_ui()
        self.update_clock()
        self.update_stats()

    def load_data(self):
        if DATA_FILE.exists():
            try:
                data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
                self.completed = int(data.get("completed", 0))
                self.tasks = data.get("tasks", [])
            except (ValueError, OSError, TypeError):
                self.completed, self.tasks = 0, []

    def save_data(self):
        data = {"completed": self.completed, "tasks": self.tasks}
        try:
            DATA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except OSError:
            pass

    def build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TEntry", padding=8, fieldbackground=COLORS["panel2"],
                        foreground=COLORS["text"])
        style.configure("TButton", padding=8, font=("Segoe UI", 10, "bold"))

        header = tk.Frame(self.root, bg=COLORS["bg"])
        header.pack(fill="x", padx=28, pady=(22, 12))
        tk.Label(header, text="FOCUSFLOW", font=("Segoe UI", 22, "bold"),
                 fg=COLORS["text"], bg=COLORS["bg"]).pack(side="left")
        tk.Label(header, text="Small steps. Deep focus.", font=("Segoe UI", 10),
                 fg=COLORS["muted"], bg=COLORS["bg"]).pack(side="right", pady=9)

        body = tk.Frame(self.root, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=28, pady=8)

        timer_card = tk.Frame(body, bg=COLORS["panel"], padx=24, pady=22)
        timer_card.pack(side="left", fill="both", expand=True, padx=(0, 12))

        self.mode_label = tk.Label(timer_card, text="FOCUS SESSION",
                                   font=("Segoe UI", 11, "bold"),
                                   fg=COLORS["green"], bg=COLORS["panel"])
        self.mode_label.pack(pady=(3, 8))

        self.time_label = tk.Label(timer_card, text="25:00",
                                   font=("Segoe UI", 58, "bold"),
                                   fg=COLORS["text"], bg=COLORS["panel"])
        self.time_label.pack(pady=10)

        self.progress = ttk.Progressbar(timer_card, length=320, maximum=1500,
                                         mode="determinate")
        self.progress.pack(fill="x", pady=(4, 18))

        mode_row = tk.Frame(timer_card, bg=COLORS["panel"])
        mode_row.pack(pady=4)
        self.mode_button(mode_row, "Focus", self.set_focus).pack(side="left", padx=4)
        self.mode_button(mode_row, "Short break", self.set_short).pack(side="left", padx=4)
        self.mode_button(mode_row, "Long break", self.set_long).pack(side="left", padx=4)

        controls = tk.Frame(timer_card, bg=COLORS["panel"])
        controls.pack(pady=20)
        self.start_button = tk.Button(controls, text="▶  Start", command=self.toggle,
                                      bg=COLORS["accent"], fg="#101827",
                                      activebackground="#9bb2ff", relief="flat",
                                      font=("Segoe UI", 11, "bold"), width=13, pady=10)
        self.start_button.pack(side="left", padx=5)
        tk.Button(controls, text="↻  Reset", command=self.reset,
                  bg=COLORS["panel2"], fg=COLORS["text"], activebackground="#304765",
                  relief="flat", font=("Segoe UI", 11, "bold"), width=11, pady=10).pack(side="left", padx=5)

        self.stats_label = tk.Label(timer_card, text="0 focus sessions completed",
                                    font=("Segoe UI", 10), fg=COLORS["muted"],
                                    bg=COLORS["panel"])
        self.stats_label.pack(pady=(5, 0))

        task_card = tk.Frame(body, bg=COLORS["panel"], padx=18, pady=20, width=260)
        task_card.pack(side="right", fill="both")
        task_card.pack_propagate(False)
        tk.Label(task_card, text="MY TASKS", font=("Segoe UI", 12, "bold"),
                 fg=COLORS["text"], bg=COLORS["panel"]).pack(anchor="w")
        tk.Label(task_card, text="Keep your next step visible.",
                 font=("Segoe UI", 9), fg=COLORS["muted"],
                 bg=COLORS["panel"]).pack(anchor="w", pady=(3, 14))

        entry_row = tk.Frame(task_card, bg=COLORS["panel"])
        entry_row.pack(fill="x")
        self.task_entry = ttk.Entry(entry_row)
        self.task_entry.pack(side="left", fill="x", expand=True)
        self.task_entry.bind("<Return>", lambda _event: self.add_task())
        tk.Button(entry_row, text="+", command=self.add_task, bg=COLORS["green"],
                  fg="#10251f", relief="flat", font=("Segoe UI", 12, "bold"),
                  width=3).pack(side="left", padx=(6, 0))

        self.task_list = tk.Listbox(task_card, bg=COLORS["panel2"], fg=COLORS["text"],
                                    selectbackground=COLORS["accent"],
                                    selectforeground="#101827", relief="flat",
                                    highlightthickness=0, font=("Segoe UI", 10),
                                    activestyle="none")
        self.task_list.pack(fill="both", expand=True, pady=14)
        tk.Button(task_card, text="Remove selected task", command=self.remove_task,
                  bg=COLORS["panel2"], fg=COLORS["muted"], relief="flat",
                  font=("Segoe UI", 9)).pack(fill="x")

        footer = tk.Label(self.root, text="Your progress is saved locally on this computer.",
                          font=("Segoe UI", 9), fg=COLORS["muted"], bg=COLORS["bg"])
        footer.pack(pady=(4, 16))
        self.refresh_tasks()

    def mode_button(self, parent, text, command):
        return tk.Button(parent, text=text, command=command, bg=COLORS["panel2"],
                         fg=COLORS["text"], activebackground="#304765",
                         activeforeground=COLORS["text"], relief="flat",
                         font=("Segoe UI", 9), padx=9, pady=7)

    def duration_for_mode(self):
        return {"Focus": self.work_minutes, "Short break": self.short_minutes,
                "Long break": self.long_minutes}[self.mode]

    def set_mode(self, mode):
        self.stop_timer()
        self.mode = mode
        self.remaining = self.duration_for_mode() * 60
        self.mode_label.config(text=mode.upper() + (" SESSION" if mode == "Focus" else ""))
        self.mode_label.config(fg=COLORS["green"] if mode == "Focus" else COLORS["accent"])
        self.update_clock()

    def set_focus(self): self.set_mode("Focus")
    def set_short(self): self.set_mode("Short break")
    def set_long(self): self.set_mode("Long break")

    def toggle(self):
        if self.running:
            self.stop_timer()
        else:
            self.running = True
            self.start_button.config(text="Ⅱ  Pause")
            self.tick()

    def stop_timer(self):
        self.running = False
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        if hasattr(self, "start_button"):
            self.start_button.config(text="▶  Start")

    def reset(self):
        self.stop_timer()
        self.remaining = self.duration_for_mode() * 60
        self.update_clock()

    def tick(self):
        if not self.running:
            return
        if self.remaining > 0:
            self.remaining -= 1
            self.update_clock()
            self.after_id = self.root.after(1000, self.tick)
        else:
            self.stop_timer()
            if self.mode == "Focus":
                self.completed += 1
                self.save_data()
                self.update_stats()
                next_mode = "Long break" if self.completed % self.sessions_before_long == 0 else "Short break"
                messagebox.showinfo("Session complete", f"Great work! Your focus session is complete.\nNext: {next_mode}.")
                self.set_mode(next_mode)
            else:
                messagebox.showinfo("Break complete", "Break's over. Ready for another focus session?")
                self.set_focus()

    def update_clock(self):
        minutes, seconds = divmod(max(0, self.remaining), 60)
        self.time_label.config(text=f"{minutes:02d}:{seconds:02d}")
        total = self.duration_for_mode() * 60
        self.progress.configure(maximum=max(1, total), value=total - self.remaining)

    def update_stats(self):
        self.stats_label.config(text=f"{self.completed} focus sessions completed")

    def add_task(self):
        task = self.task_entry.get().strip()
        if not task:
            return
        self.tasks.append(task)
        self.task_entry.delete(0, "end")
        self.refresh_tasks()
        self.save_data()

    def remove_task(self):
        selected = self.task_list.curselection()
        if not selected:
            return
        del self.tasks[selected[0]]
        self.refresh_tasks()
        self.save_data()

    def refresh_tasks(self):
        if not hasattr(self, "task_list"):
            return
        self.task_list.delete(0, "end")
        for task in self.tasks:
            self.task_list.insert("end", "• " + task)

    def on_close(self):
        self.stop_timer()
        self.save_data()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = FocusFlow(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()

if __name__ == "__main__":
    main()
