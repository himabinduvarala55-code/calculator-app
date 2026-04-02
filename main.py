import tkinter as tk
from tkinter import scrolledtext


# Theme (Tokyo Night–inspired)
COLORS = {
    "window": "#1a1b26",
    "display_bg": "#24283b",
    "display_fg": "#c0caf5",
    "display_border": "#414868",
    "history_bg": "#16161e",
    "history_fg": "#a9b1d6",
    "history_border": "#2f3549",
    "num_bg": "#414868",
    "num_fg": "#c0caf5",
    "num_active": "#565f89",
    "op_bg": "#7aa2f7",
    "op_fg": "#1a1b26",
    "op_active": "#89b4fa",
    "clear_bg": "#f7768e",
    "clear_fg": "#1a1b26",
    "clear_active": "#ff9eaa",
    "equal_bg": "#9ece6a",
    "equal_fg": "#1a1b26",
    "equal_active": "#b5e589",
}

FONT_DISPLAY = ("Segoe UI", 22)
FONT_BTN = ("Segoe UI", 14, "bold")
FONT_HISTORY = ("Consolas", 11)
BTN_PAD = (6, 8)
GRID_PAD_OUTER = 14
GRID_PAD_CELL = 5
HISTORY_HEIGHT_LINES = 6
HISTORY_MAX_LINES = 200


class CalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Calculator")
        self.root.resizable(False, False)
        self.root.configure(bg=COLORS["window"])

        self.expression = ""
        self.display_var = tk.StringVar()

        history_frame = tk.Frame(self.root, bg=COLORS["window"])
        history_frame.grid(
            row=0,
            column=0,
            columnspan=4,
            padx=GRID_PAD_OUTER,
            pady=(GRID_PAD_OUTER, GRID_PAD_CELL),
            sticky="nsew",
        )

        self.history_text = scrolledtext.ScrolledText(
            history_frame,
            height=HISTORY_HEIGHT_LINES,
            width=32,
            font=FONT_HISTORY,
            bg=COLORS["history_bg"],
            fg=COLORS["history_fg"],
            insertbackground=COLORS["history_fg"],
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=COLORS["history_border"],
            highlightcolor=COLORS["history_border"],
            state=tk.DISABLED,
            wrap=tk.WORD,
        )
        self.history_text.pack(fill=tk.BOTH, expand=True)

        display = tk.Entry(
            self.root,
            textvariable=self.display_var,
            font=FONT_DISPLAY,
            justify="right",
            bd=1,
            relief="flat",
            state="readonly",
            readonlybackground=COLORS["display_bg"],
            fg=COLORS["display_fg"],
            insertwidth=0,
            highlightthickness=2,
            highlightbackground=COLORS["display_border"],
            highlightcolor=COLORS["display_border"],
        )
        display.grid(
            row=1,
            column=0,
            columnspan=4,
            padx=GRID_PAD_OUTER,
            pady=(0, GRID_PAD_CELL),
            ipady=12,
            sticky="nsew",
        )

        buttons = [
            ("7", 2, 0, "num"),
            ("8", 2, 1, "num"),
            ("9", 2, 2, "num"),
            ("/", 2, 3, "op"),
            ("4", 3, 0, "num"),
            ("5", 3, 1, "num"),
            ("6", 3, 2, "num"),
            ("*", 3, 3, "op"),
            ("1", 4, 0, "num"),
            ("2", 4, 1, "num"),
            ("3", 4, 2, "num"),
            ("-", 4, 3, "op"),
            ("0", 5, 0, "num"),
            (".", 5, 1, "num"),
            ("C", 5, 2, "clear"),
            ("+", 5, 3, "op"),
            ("=", 6, 0, "equal"),
        ]

        for text, row, col, kind in buttons:
            if text == "=":
                btn = self._make_button(
                    text,
                    kind,
                    command=self.calculate,
                )
                btn.grid(
                    row=row,
                    column=col,
                    columnspan=4,
                    padx=GRID_PAD_OUTER,
                    pady=(GRID_PAD_CELL, GRID_PAD_OUTER),
                    sticky="nsew",
                )
            else:
                if kind == "num":
                    cmd = lambda v=text: self.append(v)
                elif kind == "clear":
                    cmd = self.clear
                else:
                    cmd = lambda v=text: self.append(v)
                btn = self._make_button(text, kind, command=cmd)
                if col == 0:
                    px = (GRID_PAD_OUTER, GRID_PAD_CELL)
                elif col == 3:
                    px = (GRID_PAD_CELL, GRID_PAD_OUTER)
                else:
                    px = (GRID_PAD_CELL, GRID_PAD_CELL)
                btn.grid(
                    row=row,
                    column=col,
                    padx=px,
                    pady=GRID_PAD_CELL,
                    sticky="nsew",
                )

        for i in range(2, 7):
            self.root.grid_rowconfigure(i, weight=1, minsize=52)
        for i in range(4):
            self.root.grid_columnconfigure(i, weight=1, minsize=64)

        self.root.bind_all("<Key>", self._on_key_press)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        try:
            self.root.unbind_all("<Key>")
        except tk.TclError:
            pass
        self.root.destroy()

    def _on_key_press(self, event):
        if event.keysym in ("Return", "KP_Enter"):
            self.calculate()
            return "break"
        if event.keysym == "Escape":
            self.clear()
            return "break"
        if event.keysym == "BackSpace":
            self.backspace()
            return "break"

        if event.keysym == "KP_Add":
            self.append("+")
            return "break"
        if event.keysym == "KP_Subtract":
            self.append("-")
            return "break"
        if event.keysym in ("KP_Multiply", "asterisk"):
            self.append("*")
            return "break"
        if event.keysym in ("KP_Divide", "slash"):
            self.append("/")
            return "break"
        if event.keysym == "KP_Decimal":
            self.append(".")
            return "break"
        if event.keysym == "parenleft":
            self.append("(")
            return "break"
        if event.keysym == "parenright":
            self.append(")")
            return "break"

        if event.char and event.char in "0123456789+-*/.()":
            self.append(event.char)
            return "break"

    def _make_button(self, text, kind, command):
        if kind == "num":
            bg, fg, active = COLORS["num_bg"], COLORS["num_fg"], COLORS["num_active"]
        elif kind == "op":
            bg, fg, active = COLORS["op_bg"], COLORS["op_fg"], COLORS["op_active"]
        elif kind == "clear":
            bg, fg, active = COLORS["clear_bg"], COLORS["clear_fg"], COLORS["clear_active"]
        else:
            bg, fg, active = COLORS["equal_bg"], COLORS["equal_fg"], COLORS["equal_active"]

        return tk.Button(
            self.root,
            text=text,
            font=FONT_BTN,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=active,
            activeforeground=fg,
            relief="flat",
            bd=0,
            cursor="hand2",
            highlightthickness=0,
            padx=BTN_PAD[0],
            pady=BTN_PAD[1],
            takefocus=False,
        )

    def _add_history_line(self, line):
        self.history_text.configure(state=tk.NORMAL)
        self.history_text.insert(tk.END, line + "\n")
        while True:
            text = self.history_text.get("1.0", "end-1c")
            n = len(text.splitlines())
            if n <= HISTORY_MAX_LINES:
                break
            self.history_text.delete("1.0", "2.0")
        self.history_text.see(tk.END)
        self.history_text.configure(state=tk.DISABLED)

    def append(self, value):
        self.expression += value
        self.display_var.set(self.expression)

    def backspace(self):
        self.expression = self.expression[:-1]
        self.display_var.set(self.expression)

    def clear(self):
        self.expression = ""
        self.display_var.set("")

    def calculate(self):
        expr = self.expression.strip()
        if not expr:
            return
        try:
            result = eval(expr, {"__builtins__": {}}, {})
            self._add_history_line(f"{expr} = {result}")
            self.expression = str(result)
            self.display_var.set(self.expression)
        except ZeroDivisionError:
            self._add_history_line(f"{expr} = Error (divide by zero)")
            self.display_var.set("Error: Divide by 0")
            self.expression = ""
        except Exception:
            self._add_history_line(f"{expr} = Error")
            self.display_var.set("Error")
            self.expression = ""


if __name__ == "__main__":
    root = tk.Tk()
    CalculatorApp(root)
    root.mainloop()
