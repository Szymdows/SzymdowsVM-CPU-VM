import sys
import os
import random
import math
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QFileDialog, 
                             QFrame, QTextEdit)
from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtCore import QTimer, Qt

# ==========================================
# CONSTANTS & CONFIGURATION
# ==========================================
MEM_SIZE = 4096       # 4KB of RAM
VIDEO_COLS = 80
VIDEO_ROWS = 25
VIDEO_RAM_SIZE = VIDEO_COLS * VIDEO_ROWS
FONT_FILE = "PerfectDOSVGA437.ttf"

# ==========================================
# VIRTUAL CPU (EXPANDED INSTRUCTION SET)
# ==========================================
class VirtualCPU:
    def __init__(self):
        # 1. REGISTERS (General Purpose + Pointers)
        self.regs = {
            "AX": 0, "BX": 0, "CX": 0, "DX": 0, # General
            "SP": MEM_SIZE - 1,                 # Stack Pointer (Starts at end of RAM)
            "BP": MEM_SIZE - 1,                 # Base Pointer
            "SI": 0, "DI": 0                    # Source/Dest Index
        }
        self.ip = 0  # Instruction Pointer
        
        # 2. EXTENDED FLAGS
        self.flags = {
            "Z": False,  # Zero
            "S": False,  # Sign (Negative)
            "O": False,  # Overflow
            "E": False   # Error/Halt
        }

        # 3. MEMORY
        self.ram = [0] * MEM_SIZE 
        self.program = []
        self.video_ram = [' '] * VIDEO_RAM_SIZE
        self.labels = {}

    def reset(self):
        self.regs = {k: 0 for k in self.regs}
        self.regs["SP"] = MEM_SIZE - 1
        self.regs["BP"] = MEM_SIZE - 1
        self.ip = 0
        self.flags = {"Z": False, "S": False, "O": False, "E": False}
        self.ram = [0] * MEM_SIZE
        self.video_ram = [' '] * VIDEO_RAM_SIZE

    def load_program(self, asm_code):
        self.reset()
        lines = asm_code.split('\n')
        cleaned_lines = []
        ip_counter = 0
        for line in lines:
            line = line.strip()
            if not line or line.startswith(';'): continue
            if ';' in line: line = line.split(';')[0].strip()
            if line.endswith(':'):
                self.labels[line[:-1]] = ip_counter
            else:
                cleaned_lines.append(line)
                ip_counter += 1
        self.program = cleaned_lines

    def get_val(self, operand):
        """Advanced getter: handles Registers, Numbers, and [Memory]"""
        if operand in self.regs:
            return self.regs[operand]
        
        # Handle Dereferencing [AX] or [100]
        if operand.startswith("[") and operand.endswith("]"):
            inner = operand[1:-1]
            addr = 0
            if inner in self.regs:
                addr = self.regs[inner]
            else:
                try: addr = int(inner)
                except: addr = 0
            
            if 0 <= addr < MEM_SIZE:
                return self.ram[addr]
            return 0

        try: return int(operand)
        except ValueError: return 0

    def set_val(self, dest, val):
        """Advanced setter: handles Register and [Memory] assignment"""
        val = int(val) # Ensure integer
        if dest in self.regs:
            self.regs[dest] = val
        elif dest.startswith("[") and dest.endswith("]"):
            inner = dest[1:-1]
            addr = 0
            if inner in self.regs:
                addr = self.regs[inner]
            else:
                try: addr = int(inner)
                except: addr = 0
            
            if 0 <= addr < MEM_SIZE:
                self.ram[addr] = val

    def _update_flags(self, result):
        self.flags["Z"] = (result == 0)
        self.flags["S"] = (result < 0)
        # Simple overflow check for 16-bit-ish limits
        self.flags["O"] = (result > 32767 or result < -32768)

    def step(self):
        if self.flags["E"]: return 
        if self.ip >= len(self.program):
            self.flags["E"] = True
            return

        line = self.program[self.ip]
        parts = line.replace(',', ' ').split()
        if not parts: 
            self.ip += 1
            return
            
        opcode = parts[0].upper()
        args = parts[1:]
        
        # Helper for Argument counts (prevents index errors)
        arg1 = args[0] if len(args) > 0 else None
        arg2 = args[1] if len(args) > 1 else None
        
        # =========================================================
        # 1. DATA TRANSFER
        # =========================================================
        if opcode == "MOV":
            self.set_val(arg1, self.get_val(arg2))
        
        elif opcode == "XCHG": # Exchange two registers
            v1 = self.get_val(arg1)
            v2 = self.get_val(arg2)
            self.set_val(arg1, v2)
            self.set_val(arg2, v1)

        elif opcode == "CLR": # Clear register (Set to 0)
            self.set_val(arg1, 0)
            self._update_flags(0)

        # =========================================================
        # 2. STACK OPERATIONS (PUSH/POP)
        # =========================================================
        elif opcode == "PUSH":
            val = self.get_val(arg1)
            self.regs["SP"] -= 1
            if 0 <= self.regs["SP"] < MEM_SIZE:
                self.ram[self.regs["SP"]] = val
        
        elif opcode == "POP":
            if 0 <= self.regs["SP"] < MEM_SIZE:
                val = self.ram[self.regs["SP"]]
                self.set_val(arg1, val)
                self.regs["SP"] += 1
        
        elif opcode == "PUSHA": # Push All General Registers
            for r in ["AX", "BX", "CX", "DX"]:
                self.regs["SP"] -= 1
                self.ram[self.regs["SP"]] = self.regs[r]

        elif opcode == "POPA": # Pop All General Registers (Reverse order)
            for r in ["DX", "CX", "BX", "AX"]:
                self.regs[r] = self.ram[self.regs["SP"]]
                self.regs["SP"] += 1

        # =========================================================
        # 3. ARITHMETIC (MATH)
        # =========================================================
        elif opcode == "ADD":
            res = self.get_val(arg1) + self.get_val(arg2)
            self.set_val(arg1, res)
            self._update_flags(res)
        
        elif opcode == "SUB":
            res = self.get_val(arg1) - self.get_val(arg2)
            self.set_val(arg1, res)
            self._update_flags(res)
        
        elif opcode == "INC":
            res = self.get_val(arg1) + 1
            self.set_val(arg1, res)
            self._update_flags(res)

        elif opcode == "DEC":
            res = self.get_val(arg1) - 1
            self.set_val(arg1, res)
            self._update_flags(res)

        elif opcode == "MUL":
            res = self.get_val(arg1) * self.get_val(arg2)
            self.set_val(arg1, res)
            self._update_flags(res)

        elif opcode == "DIV":
            denom = self.get_val(arg2)
            if denom == 0: self.flags["E"] = True # Crash on zero
            else:
                res = self.get_val(arg1) // denom
                self.set_val(arg1, res)
                self._update_flags(res)

        elif opcode == "MOD": # Modulo (Remainder)
            denom = self.get_val(arg2)
            if denom != 0:
                res = self.get_val(arg1) % denom
                self.set_val(arg1, res)
                self._update_flags(res)

        elif opcode == "NEG": # Negate (Multiply by -1)
            res = -self.get_val(arg1)
            self.set_val(arg1, res)
            self._update_flags(res)

        elif opcode == "ABS": # Absolute value
            res = abs(self.get_val(arg1))
            self.set_val(arg1, res)
            self._update_flags(res)
        
        elif opcode == "SQRT":
            res = int(math.sqrt(abs(self.get_val(arg1))))
            self.set_val(arg1, res)

        elif opcode == "POW": # Power: POW AX, 2 (AX = AX^2)
            res = int(math.pow(self.get_val(arg1), self.get_val(arg2)))
            self.set_val(arg1, res)

        elif opcode == "MIN":
            res = min(self.get_val(arg1), self.get_val(arg2))
            self.set_val(arg1, res)

        elif opcode == "MAX":
            res = max(self.get_val(arg1), self.get_val(arg2))
            self.set_val(arg1, res)

        # =========================================================
        # 4. BITWISE LOGIC
        # =========================================================
        elif opcode == "AND":
            res = self.get_val(arg1) & self.get_val(arg2)
            self.set_val(arg1, res)
            self._update_flags(res)
        
        elif opcode == "OR":
            res = self.get_val(arg1) | self.get_val(arg2)
            self.set_val(arg1, res)
            self._update_flags(res)

        elif opcode == "XOR":
            res = self.get_val(arg1) ^ self.get_val(arg2)
            self.set_val(arg1, res)
            self._update_flags(res)

        elif opcode == "NOT":
            res = ~self.get_val(arg1)
            self.set_val(arg1, res)
            self._update_flags(res)

        elif opcode == "SHL": # Shift Left
            res = self.get_val(arg1) << self.get_val(arg2)
            self.set_val(arg1, res)
            self._update_flags(res)

        elif opcode == "SHR": # Shift Right
            res = self.get_val(arg1) >> self.get_val(arg2)
            self.set_val(arg1, res)
            self._update_flags(res)

        # =========================================================
        # 5. CONTROL FLOW & JUMPS
        # =========================================================
        elif opcode == "CMP":
            res = self.get_val(arg1) - self.get_val(arg2)
            self._update_flags(res)

        elif opcode == "TEST": # Logical Compare (AND)
            res = self.get_val(arg1) & self.get_val(arg2)
            self._update_flags(res)

        elif opcode == "JMP":
            if arg1 in self.labels: self.ip = self.labels[arg1]; return
        
        elif opcode == "JE" or opcode == "JZ": # Equal / Zero
            if self.flags["Z"] and arg1 in self.labels: self.ip = self.labels[arg1]; return

        elif opcode == "JNE" or opcode == "JNZ": # Not Equal / Not Zero
            if not self.flags["Z"] and arg1 in self.labels: self.ip = self.labels[arg1]; return

        elif opcode == "JG": # Greater
            if not self.flags["S"] and not self.flags["Z"] and arg1 in self.labels: 
                self.ip = self.labels[arg1]; return
        
        elif opcode == "JGE": # Greater or Equal
            if (not self.flags["S"] or self.flags["Z"]) and arg1 in self.labels:
                 self.ip = self.labels[arg1]; return

        elif opcode == "JL": # Less
            if self.flags["S"] and arg1 in self.labels: self.ip = self.labels[arg1]; return

        elif opcode == "JLE": # Less or Equal
            if (self.flags["S"] or self.flags["Z"]) and arg1 in self.labels:
                 self.ip = self.labels[arg1]; return

        # =========================================================
        # 6. SUBROUTINES (CALL / RET)
        # =========================================================
        elif opcode == "CALL":
            # Push next IP onto stack
            ret_addr = self.ip + 1
            self.regs["SP"] -= 1
            self.ram[self.regs["SP"]] = ret_addr
            # Jump to label
            if arg1 in self.labels: 
                self.ip = self.labels[arg1]
                return

        elif opcode == "RET":
            # Pop IP from stack
            ret_addr = self.ram[self.regs["SP"]]
            self.regs["SP"] += 1
            self.ip = ret_addr
            return

        # =========================================================
        # 7. SPECIAL / SYSTEM / VIDEO
        # =========================================================
        elif opcode == "HLT":
            self.flags["E"] = True; return

        elif opcode == "NOP": # No Operation
            pass

        elif opcode == "PRINT":
            char = self.get_val(arg1)
            pos = self.get_val(arg2)
            if 0 <= pos < VIDEO_RAM_SIZE: self.video_ram[pos] = chr(char)

        elif opcode == "CLS": # Clear Screen
            self.video_ram = [' '] * VIDEO_RAM_SIZE

        elif opcode == "RAND": # RAND AX, 100 (AX = Random 0-99)
            limit = self.get_val(arg2)
            self.set_val(arg1, random.randint(0, limit))

        elif opcode == "WAIT": 
            pass 

        elif opcode == "DEBUG": 
            print(f"DEBUG: AX={self.regs['AX']} BX={self.regs['BX']}")

        # Move to next instruction
        self.ip += 1

# ==========================================
# GUI IMPLEMENTATION
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Szymdows VM – CPU-VM")
        self.resize(1000, 720)
        
        self.cpu = VirtualCPU()
        self.timer = QTimer()
        self.timer.setInterval(20) # 20ms = ~50Hz refresh
        self.timer.timeout.connect(self.run_cycle)

        self.init_ui()
        self.load_font()

    def load_font(self):
        # Attempts to load the DOS font, falls back if missing
        font_id = QFontDatabase.addApplicationFont(FONT_FILE)
        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            self.dos_font = QFont(families[0], 16)
        else:
            self.dos_font = QFont("Courier New", 14)
        
        self.screen_display.setFont(self.dos_font)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # --- LEFT SIDE: THE SCREEN ---
        screen_frame = QFrame()
        screen_frame.setFrameShape(QFrame.Shape.StyledPanel)
        screen_frame.setStyleSheet("background-color: #000000; border: 4px solid #333;")
        screen_layout = QVBoxLayout(screen_frame)
        screen_layout.setContentsMargins(5, 5, 5, 5)
        
        # Using QTextEdit for authentic character rendering
        self.screen_display = QTextEdit()
        self.screen_display.setReadOnly(True)
        self.screen_display.setFrameStyle(QFrame.Shape.NoFrame)
        self.screen_display.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.screen_display.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.screen_display.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        
        self.screen_display.setStyleSheet("""
            QTextEdit {
                background-color: black;
                color: #AAAAAA;
                border: none;
            }
        """)
        
        screen_layout.addWidget(self.screen_display)
        main_layout.addWidget(screen_frame, stretch=2)

        # --- RIGHT SIDE: CONTROLS ---
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_load = QPushButton("Load ASM")
        self.btn_load.clicked.connect(self.load_file)
        self.btn_run = QPushButton("Run")
        self.btn_run.clicked.connect(self.toggle_run)
        self.btn_step = QPushButton("Step")
        self.btn_step.clicked.connect(self.step_once)
        self.btn_reset = QPushButton("Reset")
        self.btn_reset.clicked.connect(self.reset_vm)
        
        btn_layout.addWidget(self.btn_load)
        btn_layout.addWidget(self.btn_run)
        btn_layout.addWidget(self.btn_step)
        btn_layout.addWidget(self.btn_reset)
        control_layout.addLayout(btn_layout)

        # Register View
        self.lbl_debug = QLabel("Registers:")
        self.lbl_debug.setFont(QFont("Courier New", 10))
        self.lbl_debug.setStyleSheet("background-color: #222; color: #0F0; padding: 10px;")
        control_layout.addWidget(self.lbl_debug)

        # Source Code View
        lbl_code = QLabel("Source Code:")
        control_layout.addWidget(lbl_code)
        self.txt_source = QTextEdit()
        self.txt_source.setReadOnly(True)
        self.txt_source.setFont(QFont("Courier New", 10))
        self.txt_source.setStyleSheet("background-color: #EEE; color: #333;")
        control_layout.addWidget(self.txt_source)

        main_layout.addWidget(control_panel, stretch=1)
        
        self.update_debug_view()
        self.update_screen_display()

    def load_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Open Assembly File', '.', "Assembly (*.asm *.txt)")
        if fname:
            try:
                with open(fname, 'r') as f:
                    code = f.read()
                    self.txt_source.setText(code)
                    self.cpu.load_program(code)
                    self.update_debug_view()
                    self.update_screen_display()
                    self.status_bar_msg(f"Loaded {os.path.basename(fname)}")
            except Exception as e:
                self.status_bar_msg(f"Error: {str(e)}")

    def toggle_run(self):
        if self.timer.isActive():
            self.timer.stop()
            self.btn_run.setText("Run")
            self.status_bar_msg("Paused")
        else:
            self.timer.start()
            self.btn_run.setText("Pause")
            self.status_bar_msg("Running...")

    def step_once(self):
        self.run_cycle()

    def reset_vm(self):
        self.timer.stop()
        self.btn_run.setText("Run")
        self.cpu.reset()
        code = self.txt_source.toPlainText()
        if code: self.cpu.load_program(code)
        self.update_debug_view()
        self.update_screen_display()
        self.status_bar_msg("VM Reset")

    def run_cycle(self):
        if self.cpu.flags["E"]:
            self.timer.stop()
            self.btn_run.setText("Run")
            self.status_bar_msg("Program Halted")
            return
        
        # Execute multiple instructions per GUI update for speed
        # Adjust range for faster/slower execution
        for _ in range(5): 
            self.cpu.step()
            if self.cpu.flags["E"]: break
            
        self.update_debug_view()
        self.update_screen_display()

    def update_debug_view(self):
        reg_txt = "REGISTERS:\n"
        # Print first 4 regs
        for r in ["AX", "BX", "CX", "DX"]:
            v = self.cpu.regs[r]
            reg_txt += f"{r}: {v:04X} ({v})\n"
        
        # Print Pointers
        reg_txt += f"\nSP: {self.cpu.regs['SP']:04X}  BP: {self.cpu.regs['BP']:04X}\n"
        
        flags_txt = "\nFLAGS:\n"
        flags_txt += f"Z:{int(self.cpu.flags['Z'])} S:{int(self.cpu.flags['S'])} O:{int(self.cpu.flags['O'])} E:{int(self.cpu.flags['E'])}\n"
        
        instr_txt = "\nNEXT INSTRUCTION:\n"
        if not self.cpu.flags["E"] and self.cpu.ip < len(self.cpu.program):
            instr_txt += f"{self.cpu.ip}: {self.cpu.program[self.cpu.ip]}"
        else:
            instr_txt += "HALTED"

        self.lbl_debug.setText(reg_txt + flags_txt + instr_txt)

    def update_screen_display(self):
        # Convert video ram list to string
        raw_chars = "".join(self.cpu.video_ram)
        # Split into rows
        rows = [raw_chars[i:i+VIDEO_COLS] for i in range(0, VIDEO_RAM_SIZE, VIDEO_COLS)]
        display_text = "\n".join(rows)
        self.screen_display.setPlainText(display_text)

    def status_bar_msg(self, msg):
        self.statusBar().showMessage(msg)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
