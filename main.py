import os
import tkinter as tk
from tkinter import messagebox


APP_TITLE = "CalcPad — Desktop Calculator"

THEMES = {
    "dark": {
        "window": "#1a1b26",
        "display_bg": "#24283b",
        "display_fg": "#c0caf5",
        "display_border": "#414868",
        "history_bg": "#16161e",
        "history_fg": "#a9b1d6",
        "history_border": "#2f3549",
        "history_select_bg": "#414868",
        "history_select_fg": "#c0caf5",
        "scrollbar_bg": "#414868",
        "scrollbar_trough": "#16161e",
        "label_muted": "#7a88b8",
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
        "toggle_bg": "#565f89",
        "toggle_fg": "#c0caf5",
        "toggle_active": "#6c7086",
    },
    "light": {
        "window": "#e8ecf4",
        "display_bg": "#ffffff",
        "display_fg": "#1e293b",
        "display_border": "#cbd5e1",
        "history_bg": "#ffffff",
        "history_fg": "#475569",
        "history_border": "#cbd5e1",
        "history_select_bg": "#bfdbfe",
        "history_select_fg": "#1e293b",
        "scrollbar_bg": "#cbd5e1",
        "scrollbar_trough": "#e2e8f0",
        "label_muted": "#64748b",
        "num_bg": "#e2e8f0",
        "num_fg": "#1e293b",
        "num_active": "#cbd5e1",
        "op_bg": "#3b82f6",
        "op_fg": "#ffffff",
        "op_active": "#2563eb",
        "clear_bg": "#ef4444",
        "clear_fg": "#ffffff",
        "clear_active": "#dc2626",
        "equal_bg": "#22c55e",
        "equal_fg": "#ffffff",
        "equal_active": "#16a34a",
        "toggle_bg": "#cbd5e1",
        "toggle_fg": "#334155",
        "toggle_active": "#94a3b8",
    },
}

FONT_DISPLAY = ("Segoe UI", 22)
FONT_BTN = ("Segoe UI", 14, "bold")
FONT_HISTORY = ("Consolas", 11)
FONT_SECTION = ("Segoe UI Semibold", 10)
BTN_PAD = (8, 10)
GRID_PAD_CELL = 8
SECTION_GAP = 12
HISTORY_HEIGHT_LINES = 6
HISTORY_MAX_LINES = 200
WINDOW_MARGIN_X = 22
WINDOW_MARGIN_Y = 20

# Keyboard reference (handled in _on_key_press; printable keys also pass through _insert_safely)
#   Enter / KP_Enter     evaluate (only if _expression_ready())
#   Escape               clear expression
#   BackSpace            delete last character
#   Digits 0–9           insert digit (not after ')')
#   .                    decimal (leading “.” → “0.”; one “.” per number)
#   + - * /              operators (position rules; “**” allowed)
#   ( )                  parentheses (balanced “)”; no “()” or digit“(”)
#   Numpad               KP_Add → +, KP_Subtract → −, KP_Multiply → *,
#                        KP_Divide → /, KP_Decimal → .
# Ctrl/Alt/Meta + key    ignored (does not modify expression)
# Any other key          ignored without consuming system shortcuts needlessly

_MOD_CONTROL = 0x0004
_MOD_ALT = 0x20000
_MOD_META = 0x0008

_KEYSYM_TO_SYMBOL = {
    "KP_Add": "+",
    "KP_Subtract": "-",
    "KP_Multiply": "*",
    "KP_Divide": "/",
    "KP_Decimal": ".",
    "plus": "+",
    "minus": "-",
    "asterisk": "*",
    "slash": "/",
    "parenleft": "(",
    "parenright": ")",
    "Paren_L": "(",
    "Paren_R": ")",
}


def _apply_window_icon(root):
    base = os.path.dirname(os.path.abspath(__file__))
    ico_path = os.path.join(base, "app_icon.ico")
    png_path = os.path.join(base, "app_icon.png")
    try:
        if os.path.isfile(ico_path):
            root.iconbitmap(ico_path)
        elif os.path.isfile(png_path):
            img = tk.PhotoImage(file=png_path)
            root.iconphoto(True, img)
            root._calc_icon_image = img
    except tk.TclError:
        pass


class CalculatorApp:
    def __init__(self, root):
        self.root = root
        self.theme_mode = "dark"
        self._buttons = []

        self.root.title(APP_TITLE)
        self.root.resizable(False, False)

        self.expression = ""
        self.display_var = tk.StringVar()

        c = self._colors()
        self.root.configure(bg=c["window"])

        self.content = tk.Frame(self.root, bg=c["window"], padx=WINDOW_MARGIN_X, pady=WINDOW_MARGIN_Y)
        self.content.grid(row=0, column=0, sticky="nsew")

        self.history_frame = tk.Frame(self.content, bg=c["window"])
        self.history_frame.grid(
            row=0,
            column=0,
            columnspan=4,
            padx=(0, 0),
            pady=(0, GRID_PAD_CELL),
            sticky="nsew",
        )

        self.header_frame = tk.Frame(self.history_frame, bg=c["window"])
        self.header_frame.pack(fill=tk.X, pady=(0, SECTION_GAP // 2))

        self.history_label = tk.Label(
            self.header_frame,
            text="History — click a row to reuse its result",
            font=FONT_SECTION,
            fg=c["label_muted"],
            bg=c["window"],
            anchor="w",
        )
        self.history_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.theme_btn = tk.Button(
            self.header_frame,
            text="Light mode",
            font=FONT_SECTION,
            command=self._toggle_theme,
            relief="flat",
            bd=0,
            cursor="hand2",
            highlightthickness=0,
            padx=12,
            pady=4,
            takefocus=False,
        )
        self.theme_btn.pack(side=tk.RIGHT)
        self._buttons.append((self.theme_btn, "toggle"))

        self.history_list_wrap = tk.Frame(
            self.history_frame,
            bg=c["window"],
            highlightthickness=1,
            highlightbackground=c["history_border"],
            highlightcolor=c["history_border"],
        )
        self.history_list_wrap.pack(fill=tk.BOTH, expand=True)

        self.history_scroll = tk.Scrollbar(
            self.history_list_wrap,
            orient=tk.VERTICAL,
            jump=True,
            bg=c["scrollbar_bg"],
            troughcolor=c["scrollbar_trough"],
            activebackground=c["num_active"],
            bd=0,
            highlightthickness=0,
        )

        self.history_list = tk.Listbox(
            self.history_list_wrap,
            height=HISTORY_HEIGHT_LINES,
            width=34,
            font=FONT_HISTORY,
            bg=c["history_bg"],
            fg=c["history_fg"],
            selectbackground=c["history_select_bg"],
            selectforeground=c["history_select_fg"],
            relief="flat",
            bd=0,
            highlightthickness=0,
            yscrollcommand=self.history_scroll.set,
            exportselection=False,
            selectmode=tk.BROWSE,
            activestyle="none",
            cursor="hand2",
        )
        self.history_scroll.config(command=self.history_list.yview)

        self.history_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        self.history_scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 8), pady=10)

        self.history_list.bind("<ButtonRelease-1>", self._on_history_click)
        self.history_list.bind("<MouseWheel>", self._history_mousewheel)
        self.history_list.bind("<Button-4>", self._history_mousewheel)
        self.history_list.bind("<Button-5>", self._history_mousewheel)
        self.history_list_wrap.bind("<MouseWheel>", self._history_mousewheel)
        self.history_scroll.bind("<MouseWheel>", self._history_mousewheel)

        self.display = tk.Entry(
            self.content,
            textvariable=self.display_var,
            font=FONT_DISPLAY,
            justify="right",
            bd=1,
            relief="flat",
            state="readonly",
            readonlybackground=c["display_bg"],
            fg=c["display_fg"],
            insertwidth=0,
            highlightthickness=2,
            highlightbackground=c["display_border"],
            highlightcolor=c["display_border"],
        )
        self.display.grid(
            row=1,
            column=0,
            columnspan=4,
            padx=(0, 0),
            pady=(SECTION_GAP, GRID_PAD_CELL),
            ipady=14,
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
                    padx=(0, 0),
                    pady=(GRID_PAD_CELL + 2, 0),
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
                    px = (0, GRID_PAD_CELL)
                elif col == 3:
                    px = (GRID_PAD_CELL, 0)
                else:
                    px = (GRID_PAD_CELL, GRID_PAD_CELL)
                btn.grid(
                    row=row,
                    column=col,
                    padx=px,
                    pady=(GRID_PAD_CELL, GRID_PAD_CELL),
                    sticky="nsew",
                )

        for i in range(2, 7):
            self.content.grid_rowconfigure(i, weight=1, minsize=56)
        for i in range(4):
            self.content.grid_columnconfigure(i, weight=1, minsize=70)

        self._apply_theme()
        self.root.bind_all("<Key>", self._on_key_press)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _colors(self):
        return THEMES[self.theme_mode]

    def _toggle_theme(self):
        self.theme_mode = "light" if self.theme_mode == "dark" else "dark"
        self._apply_theme()

    def _apply_theme(self):
        c = self._colors()
        self.root.configure(bg=c["window"])
        self.content.configure(bg=c["window"])
        self.history_frame.configure(bg=c["window"])
        self.header_frame.configure(bg=c["window"])
        self.history_label.configure(fg=c["label_muted"], bg=c["window"])
        self.history_list_wrap.configure(
            bg=c["window"],
            highlightbackground=c["history_border"],
            highlightcolor=c["history_border"],
        )
        self.history_list.configure(
            bg=c["history_bg"],
            fg=c["history_fg"],
            selectbackground=c["history_select_bg"],
            selectforeground=c["history_select_fg"],
        )
        self.history_scroll.configure(
            bg=c["scrollbar_bg"],
            troughcolor=c["scrollbar_trough"],
            activebackground=c["num_active"],
        )
        self.display.configure(
            readonlybackground=c["display_bg"],
            fg=c["display_fg"],
            highlightbackground=c["display_border"],
            highlightcolor=c["display_border"],
        )
        for btn, kind in self._buttons:
            if kind == "toggle":
                btn.configure(
                    text="Light mode" if self.theme_mode == "dark" else "Dark mode",
                    bg=c["toggle_bg"],
                    fg=c["toggle_fg"],
                    activebackground=c["toggle_active"],
                    activeforeground=c["toggle_fg"],
                )
            else:
                bg, fg, active = self._button_colors(kind, c)
                btn.configure(
                    bg=bg,
                    fg=fg,
                    activebackground=active,
                    activeforeground=fg,
                )

    @staticmethod
    def _button_colors(kind, c):
        if kind == "num":
            return c["num_bg"], c["num_fg"], c["num_active"]
        if kind == "op":
            return c["op_bg"], c["op_fg"], c["op_active"]
        if kind == "clear":
            return c["clear_bg"], c["clear_fg"], c["clear_active"]
        return c["equal_bg"], c["equal_fg"], c["equal_active"]

    def _on_close(self):
        try:
            self.root.unbind_all("<Key>")
        except tk.TclError:
            pass
        self.root.destroy()

    def _modifier_down(self, event):
        st = getattr(event, "state", 0) or 0
        return bool(st & (_MOD_CONTROL | _MOD_ALT | _MOD_META))

    def _bell_reject(self):
        self.root.bell()

    def _paren_surplus(self):
        return self.expression.count("(") - self.expression.count(")")

    def _active_number_has_dot(self):
        for ch in reversed(self.expression):
            if ch == ".":
                return True
            if ch in "+-*/)":
                break
            if ch == "(":
                break
        return False

    def _expression_ready(self):
        e = self.expression.strip()
        if not e:
            return False
        if self._paren_surplus() != 0:
            return False
        last = e[-1]
        return last.isdigit() or last == ")" or last == "."

    def _insert_safely(self, ch):
        e = self.expression
        last = e[-1] if e else ""

        if ch.isdigit():
            if last == ")":
                self._bell_reject()
                return False
            self.expression += ch
            self.display_var.set(self.expression)
            return True

        if ch == ".":
            if last == ")":
                self._bell_reject()
                return False
            if self._active_number_has_dot():
                self._bell_reject()
                return False
            if not e or last in "(+-*/)":
                self.expression += "0."
                self.display_var.set(self.expression)
                return True
            if last.isdigit():
                self.expression += "."
                self.display_var.set(self.expression)
                return True
            self._bell_reject()
            return False

        if ch == "(":
            if last and (last.isdigit() or last == ")"):
                self._bell_reject()
                return False
            self.expression += "("
            self.display_var.set(self.expression)
            return True

        if ch == ")":
            if self._paren_surplus() <= 0:
                self._bell_reject()
                return False
            if not last or last == "(" or last in "+-*/.":
                self._bell_reject()
                return False
            self.expression += ")"
            self.display_var.set(self.expression)
            return True

        if ch == "-":
            if last == ".":
                self._bell_reject()
                return False
            if not e or last in "(+-*/":
                self.expression += "-"
                self.display_var.set(self.expression)
                return True
            if last.isdigit() or last == ")":
                self.expression += "-"
                self.display_var.set(self.expression)
                return True
            self._bell_reject()
            return False

        if ch == "+":
            if not e or last == "(":
                self.expression += "+"
                self.display_var.set(self.expression)
                return True
            if last in "*/":
                self._bell_reject()
                return False
            if last == "+":
                self.expression += "+"
                self.display_var.set(self.expression)
                return True
            if last == "-":
                self._bell_reject()
                return False
            if last.isdigit() or last == ")" or last == ".":
                self.expression += "+"
                self.display_var.set(self.expression)
                return True
            self._bell_reject()
            return False

        if ch == "*":
            if last == "*":
                self.expression += "*"
                self.display_var.set(self.expression)
                return True
            if (
                not e
                or last == "("
                or last == "."
                or last == "-"
                or last in "+*/"
            ):
                self._bell_reject()
                return False
            self.expression += "*"
            self.display_var.set(self.expression)
            return True

        if ch == "/":
            if (
                not e
                or last == "("
                or last == "."
                or last == "-"
                or last in "+*/"
            ):
                self._bell_reject()
                return False
            self.expression += "/"
            self.display_var.set(self.expression)
            return True

        return False

    def _on_key_press(self, event):
        if self._modifier_down(event):
            return

        if event.keysym in ("Return", "KP_Enter"):
            if not self._expression_ready():
                self._bell_reject()
            else:
                self.calculate()
            return "break"

        if event.keysym == "Escape":
            self.clear()
            return "break"

        if event.keysym == "BackSpace":
            self.backspace()
            return "break"

        sym = _KEYSYM_TO_SYMBOL.get(event.keysym)
        if sym:
            self._insert_safely(sym)
            return "break"

        char = event.char
        if char and char in "0123456789+-*/.()":
            self._insert_safely(char)
            return "break"

    def _make_button(self, text, kind, command):
        c = self._colors()
        bg, fg, active = self._button_colors(kind, c)

        btn = tk.Button(
            self.content,
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
        self._buttons.append((btn, kind))
        return btn

    def _history_mousewheel(self, event):
        d = getattr(event, "delta", 0)
        if d:
            if abs(d) < 120:
                self.history_list.yview_scroll(-1 if d > 0 else 1, "units")
            else:
                self.history_list.yview_scroll(int(-d / 120), "units")
        elif getattr(event, "num", None) == 4:
            self.history_list.yview_scroll(-1, "units")
        elif getattr(event, "num", None) == 5:
            self.history_list.yview_scroll(1, "units")

    def _on_history_click(self, event):
        idx = self.history_list.nearest(event.y)
        if idx < 0 or idx >= self.history_list.size():
            return
        line = self.history_list.get(idx).strip()
        value = self._result_from_history_line(line)
        if value is None:
            return
        self.expression = value
        self.display_var.set(self.expression)

    @staticmethod
    def _result_from_history_line(line):
        if " = " not in line:
            return None
        _, rhs = line.rsplit(" = ", 1)
        rhs = rhs.strip()
        if rhs.startswith("Error"):
            return None
        return rhs

    def _add_history_line(self, line):
        self.history_list.insert(tk.END, line)
        while self.history_list.size() > HISTORY_MAX_LINES:
            self.history_list.delete(0)
        self.history_list.see(tk.END)

    def append(self, value):
        for ch in value:
            if not self._insert_safely(ch):
                break

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
        if not self._expression_ready():
            messagebox.showerror("Invalid expression", "The expression is not complete or is malformed.")
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
            messagebox.showerror("Math error", "You cannot divide by zero.")
        except Exception:
            self._add_history_line(f"{expr} = Error")
            self.display_var.set("Error")
            self.expression = ""
            messagebox.showerror("Evaluation error", "There was a problem evaluating this expression.")


if __name__ == "__main__":
    root = tk.Tk()
    _apply_window_icon(root)
    CalculatorApp(root)
    root.mainloop()
