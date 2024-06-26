import tkinter as tk
import subprocess
import os
import re
from hbase import *
from commandSelector import *

class CmdEmulator:
    ANSI_COLORS = {
        '95': 'magenta',
        '96': 'cyan',
        '0': 'white',
        '36':'darkcyan',
        '94':'blue',
        '32':'green',
        '93':'yellow',
        '91':'red',
    }

    def __init__(self, root):
        self.hbase = HBase()
        self.prompt = "hbase>>> "
        self.chars = 0
        self.root = root
        root.title("HBase CLI")
        root.configure(bg="black")
        self.history = []
        self.history_pointer = -1

        self.output_text = tk.Text(root, height=25, width=110, padx=10, pady=10,
                                    bg="black", fg="white", insertbackground="white", font=("Consolas", 11), undo=True, selectbackground='white',
                                    selectforeground='black')
        self.output_text.pack(fill=tk.BOTH, expand=True)
        self.output_text.insert(tk.END, self.prompt)
        self.current_position = self.output_text.index(tk.END)
        self.output_text.bind("<KeyPress>", self.on_key)
        self.output_text.bind("<Control-l>", self.clear_console)
        self.output_text.bind("<<Paste>>", self.on_paste)
        self.output_text.bind("<<Cut>>", self.on_cut)

        for code, color in self.ANSI_COLORS.items():
            self.output_text.tag_configure(code, foreground=color)
            
    def on_paste(self, event):
        try:
            pasted_text = self.root.clipboard_get()
            self.output_text.insert(tk.INSERT, pasted_text)
            self.chars += len(pasted_text)
        except tk.TclError:
            pass  # Handle empty clipboard or other errors
        return "break"
    
    def on_cut(self, event):
        try:
            selected_text = self.output_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.chars -= len(selected_text) + 2
            self.chars = max(self.chars, 0)
            self.output_text.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            pass  # Handle empty clipboard or other errors
        return
        
    def on_key(self, event):
        if event.keysym == "BackSpace":
            if self.chars <= 0:
                return "break"
            if self.output_text.tag_ranges(tk.SEL):
                selected_text = self.output_text.get(tk.SEL_FIRST, tk.SEL_LAST)
                self.chars -= len(selected_text) + 1
                self.output_text.delete(tk.SEL_FIRST, tk.SEL_LAST)
                return "break"
            self.chars -= 1
        elif event.keysym == "Return":
            self.on_enter(event)
            return "break"
        elif event.keysym == "Up":
            self.history_pointer += 1

            if self.history_pointer >= len(self.history):
                self.history_pointer = len(self.history) - 1
                return "break"

            current = self.output_text.index(tk.INSERT)
            self.output_text.delete(f'{current}-{self.chars}c', current)
            command = self.history[self.history_pointer]
            self.output_text.insert(tk.END, command)

            self.chars = len(command)
            return "break"
        
        elif event.keysym == "Down":
            self.history_pointer -= 1
            
            if self.history_pointer < -1:
                self.history_pointer = -1
                return "break"

            current = self.output_text.index(tk.INSERT)
            self.output_text.delete(f'{current}-{self.chars}c', current)

            if self.history_pointer == -1:
                self.chars = 0
                return "break"

            command = self.history[self.history_pointer]
            self.output_text.insert(tk.END, command)

            self.chars = len(command)
            return "break"
            
        elif event.keysym in ["Left", "Right"]:
            return
        elif event.char:
            self.chars += 1

    def on_enter(self, event):
        command = self.output_text.get("insert linestart", "insert lineend")
        command = ''.join(command.split("hbase>>> ")).strip()
        if command == '':
            self.output_text.insert(tk.END, "\n")
            self.parse_ansi(self.prompt)
        else:    
            self.history.insert(0,command)
            self.history_pointer = -1
            self.execute_command(command)
        
    def execute_command(self, command):
        self.chars = 0
        try:
            output = commandSelector(self.hbase, command)
            self.display_output(output)
        except subprocess.CalledProcessError as e:
            self.display_output(e.output + e.stderr)
            
    def display_output(self, output):
        self.output_text.insert(tk.END, "\n")
        self.parse_ansi(output)
        self.output_text.insert(tk.END, "\n")
        self.output_text.insert(tk.END, f"\n{self.prompt}")
        self.output_text.see(tk.END)

    def clear_console(self, event=None):
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, self.prompt)
        self.chars = 0
        return "break"

    def parse_ansi(self, text):
        """Parse ANSI color codes and insert text with appropriate tags."""
        ansi_escape = re.compile(r'\033\[(\d+)m')
        pos = 0
        current_tag = None

        while pos < len(text):
            match = ansi_escape.search(text, pos)
            if not match:
                self.output_text.insert(tk.END, text[pos:], current_tag)
                break

            start, end = match.span()
            if start > pos:
                self.output_text.insert(tk.END, text[pos:start], current_tag)

            color_code = match.group(1)
            current_tag = color_code if color_code in self.ANSI_COLORS else None
            pos = end

            next_match = ansi_escape.search(text, pos)
            if next_match:
                text_part = text[pos:next_match.start()]
                pos = next_match.start()
            else:
                text_part = text[pos:]
                pos = len(text)

            self.output_text.insert(tk.END, text_part, current_tag)
        
root = tk.Tk()
cmd_emulator = CmdEmulator(root)
root.mainloop()
