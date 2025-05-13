# Import tkinter for GUI creation.
import tkinter as tk
from tkinter import scrolledtext
# Import the convert function to invoke on button click.
from converter import convert

# List of C keywords for basic syntax highlighting
C_KEYWORDS = [
    "int", "float", "bool", "if", "else", "while", "for", "return", "void", "char",
    "struct", "typedef", "switch", "case", "break", "continue", "const", "unsigned",
    "include", "main"
]

# Function to apply syntax highlighting to C keywords.
def highlight_syntax(text_widget):
    text_widget.tag_remove("keyword", "1.0", tk.END)
    for keyword in C_KEYWORDS:
        start = "1.0"
        while True:
            start = text_widget.search(rf"\m{keyword}\M", start, stopindex=tk.END, regexp=True)
            if not start:
                break
            end = f"{start}+{len(keyword)}c"
            text_widget.tag_add("keyword", start, end)
            start = end
    text_widget.tag_config("keyword", foreground="#56b6c2")

# Reads C code, writes it to a file, calls conversion, and displays result.
def convert_code():
    c_code = c_text.get("1.0", tk.END).strip()

    # Dummy conversion: replace 'bool' with 'bit'
    with open("input.c", 'w') as f:
        f.write(c_code)

    convert()
    with open("output.pml", 'r') as f:
        promela_code = f.read()

    promela_text.config(state=tk.NORMAL)
    promela_text.delete("1.0", tk.END)
    promela_text.insert(tk.END, promela_code)
    promela_text.config(state=tk.DISABLED)

    status_label.config(text="Converted successfully", fg="#98c379")
    highlight_syntax(c_text)

# --- GUI SETUP ---

# Create the main application window.
root = tk.Tk()
root.title("C to Promela Converter")
root.configure(bg="#1e1e1e")

# Fonts and colors
font_style = ("Consolas", 12)
bg_color = "#1e1e1e"
fg_color = "#dcdcdc"
entry_bg = "#2d2d2d"

# Labels
# Labels for UI elements.
c_label = tk.Label(root, text="C Code", bg=bg_color, fg="#61afef", font=("Arial", 12, "bold"))
c_label.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")

# Labels for UI elements.
promela_label = tk.Label(root, text="Promela Code", bg=bg_color, fg="#61afef", font=("Arial", 12, "bold"))
promela_label.grid(row=0, column=1, padx=10, pady=(10, 0), sticky="w")
def visit_Assignment(self, node, indent=1):
    lhs = self.expr_to_str(node.lvalue)
    rhs = node.rvalue

    # If RHS is a function call
    if isinstance(rhs, c_ast.FuncCall):
        func_name = self.expr_to_str(rhs.name)
        if func_name in self.func_defs:
            args = [self.expr_to_str(arg) for arg in rhs.args.exprs] if rhs.args else []
            self.emit(f"chan ret_{func_name} = [0] of {{ int }};", indent)
            self.emit(f"run {func_name}(ret_{func_name}, {', '.join(args)});", indent)
            self.emit(f"ret_{func_name} ? {lhs};", indent)
        else:
            # fallback to default C style function call representation
            self.emit(f"{lhs} = {func_name}({', '.join(self.expr_to_str(arg) for arg in rhs.args.exprs)});", indent)
    else:
        if isinstance(rhs, c_ast.TernaryOp):
            self.handle_ternary_assignment(lhs, rhs, indent)
        else:
            self.emit(f"{lhs} = {self.expr_to_str(rhs)};", indent)

# Textboxes
# Text area widgets for input and output.
c_text = scrolledtext.ScrolledText(root, width=50, height=20, font=font_style, bg=entry_bg, fg=fg_color, insertbackground="white")
c_text.grid(row=1, column=0, padx=10, pady=5)
c_text.bind("<KeyRelease>", lambda e: highlight_syntax(c_text))

# Text area widgets for input and output.
promela_text = scrolledtext.ScrolledText(root, width=50, height=20, font=font_style, bg=entry_bg, fg=fg_color, state=tk.DISABLED)
promela_text.grid(row=1, column=1, padx=10, pady=5)

# Convert button
# Button to trigger the conversion process.
convert_button = tk.Button(root, text="Convert", command=convert_code, bg="#61afef", fg="black", font=("Arial", 10, "bold"))
convert_button.grid(row=2, column=0, columnspan=2, pady=10)

# Status label
# Labels for UI elements.
status_label = tk.Label(root, text="", bg=bg_color, fg="#98c379", font=("Arial", 10))
status_label.grid(row=3, column=0, columnspan=2, pady=(0, 10))

# Starts the Tkinter event loop to run the GUI.
root.mainloop()
