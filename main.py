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
MEM_SIZE = 65536      # Increased to 64KB for better address space
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
            "SP": MEM_SIZE - 1,                 # Stack Pointer
            "BP": MEM_SIZE - 1,                 # Base Pointer
            "SI": 0, "DI": 0                    # Source/Dest Index
        }
        self.ip = 0  # Instruction Pointer
        
        # 2. EXTENDED FLAGS
        # Z=Zero, S=Sign, O=Overflow, E=Error, C=Carry, P=Parity, D=Direction
        self.flags = {
            "Z": False, "S": False, "O": False, "E": False,
            "C": False, "P": False, "D": False 
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
        self.flags = {
            "Z": False, "S": False, "O": False, "E": False,
            "C": False, "P": False, "D": False 
        }
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
        if operand is None: return 0
        if operand in self.regs:
            return self.regs[operand]
        
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
        if dest is None: return
        val = int(val)
        
        # Simulate 16-bit integer wrap-around for registers
        # (Optional, but makes flags like Carry more realistic)
        # val = val & 0xFFFF 
        
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
        # Basic flags
        self.flags["Z"] = (result == 0)
        self.flags["S"] = (result < 0)
        # 16-bit signed limit for Overflow
        self.flags["O"] = (result > 32767 or result < -32768)
        # Carry (Simulated for 16-bit unsigned limit 65535)
        self.flags["C"] = (result > 65535 or result < 0)
        
        # Parity (Is number of set bits even?)
        # Only checks lowest 8 bits usually
        low_byte = abs(int(result)) & 0xFF
        set_bits = bin(low_byte).count('1')
        self.flags["P"] = (set_bits % 2 == 0)

    def step(self):
        if self.flags["E"]: return 
        if self.ip >= len(self.program):
            self.flags["E"] = True
            return

        line = self.program[self.ip]
        # Normalize commas
        parts = line.replace(',', ' ').split()
        if not parts: 
            self.ip += 1
            return
            
        opcode = parts[0].upper()
        args = parts[1:]
        
        arg1 = args[0] if len(args) > 0 else None
        arg2 = args[1] if len(args) > 1 else None
        arg3 = args[2] if len(args) > 2 else None

        # =========================================================
        # 1. CORE DATA TRANSFER
        # =========================================================
        if opcode == "MOV":
            self.set_val(arg1, self.get_val(arg2))
        
        elif opcode == "XCHG":
            v1 = self.get_val(arg1)
            v2 = self.get_val(arg2)
            self.set_val(arg1, v2)
            self.set_val(arg2, v1)

        elif opcode == "CLR":
            self.set_val(arg1, 0)
            self._update_flags(0)
            
        elif opcode == "BSWAP": # Byte Swap (Endianness)
            val = self.get_val(arg1)
            # Simulate 16-bit swap
            swapped = ((val & 0xFF) << 8) | ((val & 0xFF00) >> 8)
            self.set_val(arg1, swapped)

        elif opcode == "CBW": # Convert Byte to Word (Sign extend AL -> AX)
            val = self.regs["AX"] & 0xFF
            if val & 0x80: self.regs["AX"] = val | 0xFF00 # Negative
            else: self.regs["AX"] = val
        
        elif opcode == "CWD": # Convert Word to Double (Sign extend AX -> DX:AX)
            if self.regs["AX"] & 0x8000: self.regs["DX"] = 0xFFFF
            else: self.regs["DX"] = 0

        elif opcode == "CDQ": # Convert Double to Quad (EAX->EDX:EAX style)
            # Treating AX as EAX for simplicity here
            if self.regs["AX"] < 0: self.regs["DX"] = -1
            else: self.regs["DX"] = 0

        # =========================================================
        # 2. STACK OPERATIONS
        # =========================================================
        elif opcode == "PUSH":
            val = self.get_val(arg1)
            self.regs["SP"] -= 1
            if 0 <= self.regs["SP"] < MEM_SIZE: self.ram[self.regs["SP"]] = val
        
        elif opcode == "POP":
            if 0 <= self.regs["SP"] < MEM_SIZE:
                val = self.ram[self.regs["SP"]]
                self.set_val(arg1, val)
                self.regs["SP"] += 1
        
        elif opcode == "PUSHA":
            for r in ["AX", "BX", "CX", "DX", "SI", "DI", "BP", "SP"]:
                self.regs["SP"] -= 1
                self.ram[self.regs["SP"]] = self.regs[r]

        elif opcode == "POPA":
            for r in ["SP", "BP", "DI", "SI", "DX", "CX", "BX", "AX"]:
                self.regs[r] = self.ram[self.regs["SP"]]
                self.regs["SP"] += 1

        elif opcode == "PUSHF": # Push Flags
            # Pack flags into a number
            f = (int(self.flags["C"]) << 0) | (int(self.flags["P"]) << 2) | \
                (int(self.flags["Z"]) << 6) | (int(self.flags["S"]) << 7) | \
                (int(self.flags["O"]) << 11)
            self.regs["SP"] -= 1
            self.ram[self.regs["SP"]] = f

        elif opcode == "POPF": # Pop Flags
            val = self.ram[self.regs["SP"]]
            self.regs["SP"] += 1
            self.flags["C"] = bool(val & (1 << 0))
            self.flags["P"] = bool(val & (1 << 2))
            self.flags["Z"] = bool(val & (1 << 6))
            self.flags["S"] = bool(val & (1 << 7))
            self.flags["O"] = bool(val & (1 << 11))

        # =========================================================
        # 3. ARITHMETIC (INTEGER & FLOAT SIM)
        # =========================================================
        elif opcode == "ADD":
            res = self.get_val(arg1) + self.get_val(arg2)
            self.set_val(arg1, res)
            self._update_flags(res)
        
        elif opcode == "ADC": # Add with Carry
            res = self.get_val(arg1) + self.get_val(arg2) + int(self.flags["C"])
            self.set_val(arg1, res)
            self._update_flags(res)

        elif opcode == "SUB":
            res = self.get_val(arg1) - self.get_val(arg2)
            self.set_val(arg1, res)
            self._update_flags(res)

        elif opcode == "SBB": # Subtract with Borrow
            res = self.get_val(arg1) - self.get_val(arg2) - int(self.flags["C"])
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

        elif opcode == "MUL" or opcode == "IMUL":
            res = self.get_val(arg1) * self.get_val(arg2)
            self.set_val(arg1, res)
            self._update_flags(res)

        elif opcode == "DIV" or opcode == "IDIV":
            denom = self.get_val(arg2)
            if denom == 0: self.flags["E"] = True
            else:
                res = self.get_val(arg1) // denom
                self.set_val(arg1, res)
                self._update_flags(res)

        elif opcode == "MOD":
            denom = self.get_val(arg2)
            if denom != 0:
                res = self.get_val(arg1) % denom
                self.set_val(arg1, res)
                self._update_flags(res)

        elif opcode == "NEG":
            res = -self.get_val(arg1)
            self.set_val(arg1, res)
            self._update_flags(res)
        
        elif opcode == "XADD": # Exchange and Add
            v1 = self.get_val(arg1) # Dest
            v2 = self.get_val(arg2) # Src
            self.set_val(arg1, v1 + v2)
            self.set_val(arg2, v1)
            self._update_flags(v1 + v2)

        # FPU Emulation (Using standard regs as output)
        elif opcode == "ABS" or opcode == "FABS":
            res = abs(self.get_val(arg1))
            self.set_val(arg1, res)
            self._update_flags(res)

        elif opcode == "SQRT" or opcode == "FSQRT":
            res = int(math.sqrt(abs(self.get_val(arg1))))
            self.set_val(arg1, res)
        
        elif opcode == "FSIN":
            res = int(math.sin(self.get_val(arg1)))
            self.set_val(arg1, res)
        
        elif opcode == "FCOS":
            res = int(math.cos(self.get_val(arg1)))
            self.set_val(arg1, res)

        elif opcode == "FADD":
             # Basic int add simulating float add
             self.set_val(arg1, self.get_val(arg1) + self.get_val(arg2))

        # =========================================================
        # 4. BITWISE & SHIFTS
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

        elif opcode == "SHL" or opcode == "SAL":
            res = self.get_val(arg1) << self.get_val(arg2)
            self.set_val(arg1, res)
            self._update_flags(res)

        elif opcode == "SHR":
            res = self.get_val(arg1) >> self.get_val(arg2)
            self.set_val(arg1, res)
            self._update_flags(res)

        elif opcode == "SAR": # Arithmetic Shift Right (preserves sign)
            val = self.get_val(arg1)
            shift = self.get_val(arg2)
            # Simulate 32bit int behavior for Python
            if val < 0: res = val >> shift | ~(~0 >> shift)
            else: res = val >> shift
            self.set_val(arg1, res)
            self._update_flags(res)

        elif opcode == "ROL": # Rotate Left
            val = self.get_val(arg1) & 0xFFFF
            shift = self.get_val(arg2) % 16
            res = ((val << shift) | (val >> (16 - shift))) & 0xFFFF
            self.set_val(arg1, res)
            self._update_flags(res)

        elif opcode == "ROR": # Rotate Right
            val = self.get_val(arg1) & 0xFFFF
            shift = self.get_val(arg2) % 16
            res = ((val >> shift) | (val << (16 - shift))) & 0xFFFF
            self.set_val(arg1, res)
            self._update_flags(res)

        elif opcode == "RCL": # Rotate through Carry Left
            val = self.get_val(arg1) & 0xFFFF
            shift = self.get_val(arg2) % 17 # 16 bits + 1 carry
            c = 1 if self.flags["C"] else 0
            temp = (val << 1) | c
            # Simple simulation logic for 1 shift
            if shift > 0:
                self.flags["C"] = bool((val >> (16 - shift)) & 1)
                res = ((val << shift) | c) & 0xFFFF # Simplified
                self.set_val(arg1, res)

        elif opcode == "RCR": # Rotate through Carry Right
            val = self.get_val(arg1) & 0xFFFF
            # Simplified RCR
            shift = self.get_val(arg2)
            if shift > 0:
                new_c = (val >> (shift - 1)) & 1
                res = (val >> shift)
                if self.flags["C"]: res |= (1 << (16-shift))
                self.flags["C"] = bool(new_c)
                self.set_val(arg1, res)

        # =========================================================
        # 5. CONTROL FLOW & JUMPS (MASSIVE EXPANSION)
        # =========================================================
        elif opcode == "CMP":
            res = self.get_val(arg1) - self.get_val(arg2)
            self._update_flags(res)

        elif opcode == "TEST":
            res = self.get_val(arg1) & self.get_val(arg2)
            self._update_flags(res)

        elif opcode == "JMP":
            if arg1 in self.labels: self.ip = self.labels[arg1]; return
        
        # --- Unsigned Jumps ---
        elif opcode == "JA" or opcode == "JNBE": # Jump Above ( > )
            if not self.flags["C"] and not self.flags["Z"] and arg1 in self.labels: self.ip = self.labels[arg1]; return
        elif opcode == "JAE" or opcode == "JNB": # Jump Above or Equal ( >= )
            if not self.flags["C"] and arg1 in self.labels: self.ip = self.labels[arg1]; return
        elif opcode == "JB" or opcode == "JNAE" or opcode == "JC": # Jump Below / Carry ( < )
            if self.flags["C"] and arg1 in self.labels: self.ip = self.labels[arg1]; return
        elif opcode == "JBE" or opcode == "JNA": # Jump Below or Equal ( <= )
            if (self.flags["C"] or self.flags["Z"]) and arg1 in self.labels: self.ip = self.labels[arg1]; return

        # --- Signed Jumps ---
        elif opcode == "JE" or opcode == "JZ":
            if self.flags["Z"] and arg1 in self.labels: self.ip = self.labels[arg1]; return
        elif opcode == "JNE" or opcode == "JNZ":
            if not self.flags["Z"] and arg1 in self.labels: self.ip = self.labels[arg1]; return
        elif opcode == "JG" or opcode == "JNLE": # Greater (Signed)
            if not self.flags["Z"] and (self.flags["S"] == self.flags["O"]) and arg1 in self.labels: self.ip = self.labels[arg1]; return
        elif opcode == "JGE" or opcode == "JNL": # Greater or Equal (Signed)
            if (self.flags["S"] == self.flags["O"]) and arg1 in self.labels: self.ip = self.labels[arg1]; return
        elif opcode == "JL" or opcode == "JNGE": # Less (Signed)
            if (self.flags["S"] != self.flags["O"]) and arg1 in self.labels: self.ip = self.labels[arg1]; return
        elif opcode == "JLE" or opcode == "JNG": # Less or Equal (Signed)
            if (self.flags["Z"] or (self.flags["S"] != self.flags["O"])) and arg1 in self.labels: self.ip = self.labels[arg1]; return

        # --- Flag specific Jumps ---
        elif opcode == "JO": # Overflow
            if self.flags["O"] and arg1 in self.labels: self.ip = self.labels[arg1]; return
        elif opcode == "JNO":
            if not self.flags["O"] and arg1 in self.labels: self.ip = self.labels[arg1]; return
        elif opcode == "JS": # Sign (Negative)
            if self.flags["S"] and arg1 in self.labels: self.ip = self.labels[arg1]; return
        elif opcode == "JNS":
            if not self.flags["S"] and arg1 in self.labels: self.ip = self.labels[arg1]; return
        elif opcode == "JP" or opcode == "JPE": # Parity (Even)
            if self.flags["P"] and arg1 in self.labels: self.ip = self.labels[arg1]; return
        elif opcode == "JNP" or opcode == "JPO": # Parity (Odd)
            if not self.flags["P"] and arg1 in self.labels: self.ip = self.labels[arg1]; return
        elif opcode == "JNC": # Not Carry
            if not self.flags["C"] and arg1 in self.labels: self.ip = self.labels[arg1]; return
        
        elif opcode == "JCXZ": # Jump if CX is Zero
            if self.regs["CX"] == 0 and arg1 in self.labels: self.ip = self.labels[arg1]; return

        # =========================================================
        # 6. CONDITIONAL MOVES (CMOVcc)
        # =========================================================
        elif opcode.startswith("CMOV"):
            condition_met = False
            suffix = opcode[4:]
            if suffix == "Z" or suffix == "E": condition_met = self.flags["Z"]
            elif suffix == "NZ" or suffix == "NE": condition_met = not self.flags["Z"]
            elif suffix == "S": condition_met = self.flags["S"]
            elif suffix == "NS": condition_met = not self.flags["S"]
            elif suffix == "C" or suffix == "B": condition_met = self.flags["C"]
            elif suffix == "NC" or suffix == "AE": condition_met = not self.flags["C"]
            elif suffix == "O": condition_met = self.flags["O"]
            elif suffix == "NO": condition_met = not self.flags["O"]
            elif suffix == "G": condition_met = not self.flags["Z"] and (self.flags["S"] == self.flags["O"])
            elif suffix == "GE": condition_met = (self.flags["S"] == self.flags["O"])
            elif suffix == "L": condition_met = (self.flags["S"] != self.flags["O"])
            elif suffix == "LE": condition_met = self.flags["Z"] or (self.flags["S"] != self.flags["O"])
            
            if condition_met:
                self.set_val(arg1, self.get_val(arg2))

        # =========================================================
        # 7. SET BYTE ON CONDITION (SETcc) - Sets arg1 to 1 or 0
        # =========================================================
        elif opcode.startswith("SET"):
            condition_met = False
            suffix = opcode[3:]
            if suffix == "Z" or suffix == "E": condition_met = self.flags["Z"]
            elif suffix == "NZ" or suffix == "NE": condition_met = not self.flags["Z"]
            elif suffix == "S": condition_met = self.flags["S"]
            elif suffix == "NS": condition_met = not self.flags["S"]
            elif suffix == "C" or suffix == "B": condition_met = self.flags["C"]
            elif suffix == "NC" or suffix == "AE": condition_met = not self.flags["C"]
            elif suffix == "O": condition_met = self.flags["O"]
            elif suffix == "NO": condition_met = not self.flags["O"]
            elif suffix == "G": condition_met = not self.flags["Z"] and (self.flags["S"] == self.flags["O"])
            elif suffix == "GE": condition_met = (self.flags["S"] == self.flags["O"])
            elif suffix == "L": condition_met = (self.flags["S"] != self.flags["O"])
            elif suffix == "LE": condition_met = self.flags["Z"] or (self.flags["S"] != self.flags["O"])
            elif suffix == "P": condition_met = self.flags["P"]
            elif suffix == "NP": condition_met = not self.flags["P"]
            
            self.set_val(arg1, 1 if condition_met else 0)

        # =========================================================
        # 8. LOOPS
        # =========================================================
        elif opcode == "LOOP":
            self.regs["CX"] -= 1
            if self.regs["CX"] != 0 and arg1 in self.labels: self.ip = self.labels[arg1]; return
        
        elif opcode == "LOOPE" or opcode == "LOOPZ":
            self.regs["CX"] -= 1
            if self.regs["CX"] != 0 and self.flags["Z"] and arg1 in self.labels: 
                self.ip = self.labels[arg1]; return

        elif opcode == "LOOPNE" or opcode == "LOOPNZ":
            self.regs["CX"] -= 1
            if self.regs["CX"] != 0 and not self.flags["Z"] and arg1 in self.labels:
                self.ip = self.labels[arg1]; return

        # =========================================================
        # 9. STRING OPERATIONS (Uses SI, DI, Direction Flag)
        # =========================================================
        elif opcode in ["MOVS", "MOVSB", "MOVSW"]:
            # Move [SI] to [DI], inc/dec SI, DI based on D flag
            val = self.ram[self.regs["SI"]]
            self.ram[self.regs["DI"]] = val
            step = -1 if self.flags["D"] else 1
            self.regs["SI"] += step
            self.regs["DI"] += step

        elif opcode in ["LODS", "LODSB", "LODSW"]:
            # Load [SI] to AX
            val = self.ram[self.regs["SI"]]
            self.regs["AX"] = val
            step = -1 if self.flags["D"] else 1
            self.regs["SI"] += step

        elif opcode in ["STOS", "STOSB", "STOSW"]:
            # Store AX to [DI]
            val = self.regs["AX"]
            self.ram[self.regs["DI"]] = val
            step = -1 if self.flags["D"] else 1
            self.regs["DI"] += step

        elif opcode in ["CMPS", "CMPSB", "CMPSW"]:
            # Compare [SI] with [DI]
            v1 = self.ram[self.regs["SI"]]
            v2 = self.ram[self.regs["DI"]]
            self._update_flags(v1 - v2)
            step = -1 if self.flags["D"] else 1
            self.regs["SI"] += step
            self.regs["DI"] += step
        
        elif opcode in ["SCAS", "SCASB", "SCASW"]:
            # Compare AX with [DI]
            v1 = self.regs["AX"]
            v2 = self.ram[self.regs["DI"]]
            self._update_flags(v1 - v2)
            step = -1 if self.flags["D"] else 1
            self.regs["DI"] += step

        # =========================================================
        # 10. FLAG CONTROL
        # =========================================================
        elif opcode == "CLC": self.flags["C"] = False
        elif opcode == "STC": self.flags["C"] = True
        elif opcode == "CMC": self.flags["C"] = not self.flags["C"]
        elif opcode == "CLD": self.flags["D"] = False
        elif opcode == "STD": self.flags["D"] = True
        elif opcode == "CLI": pass # Interrupts not implemented
        elif opcode == "STI": pass 
        elif opcode == "LAHF": # Load Flags into AH (High byte AX)
             # Basic emulation
             pass
        elif opcode == "SAHF": # Store AH into Flags
             pass

        # =========================================================
        # 11. SUBROUTINES
        # =========================================================
        elif opcode == "CALL":
            ret_addr = self.ip + 1
            self.regs["SP"] -= 1
            self.ram[self.regs["SP"]] = ret_addr
            if arg1 in self.labels: self.ip = self.labels[arg1]; return

        elif opcode == "RET":
            ret_addr = self.ram[self.regs["SP"]]
            self.regs["SP"] += 1
            self.ip = ret_addr
            return

        # =========================================================
        # 12. SPECIAL / VIDEO / SYSTEM
        # =========================================================
        elif opcode == "HLT": self.flags["E"] = True; return
        elif opcode == "NOP": pass

        elif opcode == "PRINT":
            char = self.get_val(arg1)
            pos = self.get_val(arg2)
            if 0 <= pos < VIDEO_RAM_SIZE: self.video_ram[pos] = chr(char)

        elif opcode == "CLS": self.video_ram = [' '] * VIDEO_RAM_SIZE
        
        elif opcode == "RAND":
            limit = self.get_val(arg2)
            self.set_val(arg1, random.randint(0, limit))

        elif opcode == "DEBUG": 
            print(f"DEBUG: AX={self.regs['AX']} BX={self.regs['BX']}")

        elif opcode == "CPUID":
            self.regs["AX"] = 0x1234
            self.regs["BX"] = 0x5678
            
        elif opcode == "RDTSC": # Read Time Stamp Counter
            t = int(time.time() * 1000)
            self.regs["AX"] = t & 0xFFFF
            self.regs["DX"] = (t >> 16) & 0xFFFF
        
        elif opcode == "LEAVE":
            self.regs["SP"] = self.regs["BP"]
            self.regs["BP"] = self.ram[self.regs["SP"]]
            self.regs["SP"] += 1

        elif opcode == "LEA":
             # Load Effective Address - Emulated by just moving value if register,
             # or address if it's a pointer. Simplified here.
             pass

        elif opcode == "INT":
            # Very basic Interrupt handler
            num = self.get_val(arg1)
            if num == 3: print("Break Point")
            elif num == 21: pass # DOS interrupt simulation
        
        elif opcode == "SLEEP":
            pass # Just consumes a cycle

        # Move to next instruction
        self.ip += 1

# ==========================================
# GUI IMPLEMENTATION
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Szymdows VM – CPU-VM Extended")
        self.resize(1000, 720)
        
        self.cpu = VirtualCPU()
        self.timer = QTimer()
        self.timer.setInterval(20) # 20ms = ~50Hz refresh
        self.timer.timeout.connect(self.run_cycle)

        self.init_ui()
        self.load_font()

    def load_font(self):
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
        
        for _ in range(5): 
            self.cpu.step()
            if self.cpu.flags["E"]: break
            
        self.update_debug_view()
        self.update_screen_display()

    def update_debug_view(self):
        reg_txt = "REGISTERS (Hex/Dec):\n"
        for r in ["AX", "BX", "CX", "DX", "SI", "DI"]:
            v = self.cpu.regs[r]
            reg_txt += f"{r}: {v:04X} ({v})\n"
        
        reg_txt += f"\nSP: {self.cpu.regs['SP']:04X}  BP: {self.cpu.regs['BP']:04X}\n"
        
        # Extended Flags Display
        flags_txt = "\nFLAGS: [Z S O E C P D]\n       "
        flags_txt += f"[{int(self.cpu.flags['Z'])} {int(self.cpu.flags['S'])} {int(self.cpu.flags['O'])} "
        flags_txt += f"{int(self.cpu.flags['E'])} {int(self.cpu.flags['C'])} {int(self.cpu.flags['P'])} {int(self.cpu.flags['D'])}]\n"
        
        instr_txt = "\nNEXT INSTRUCTION:\n"
        if not self.cpu.flags["E"] and self.cpu.ip < len(self.cpu.program):
            instr_txt += f"{self.cpu.ip}: {self.cpu.program[self.cpu.ip]}"
        else:
            instr_txt += "HALTED"

        self.lbl_debug.setText(reg_txt + flags_txt + instr_txt)

    def update_screen_display(self):
        raw_chars = "".join(self.cpu.video_ram)
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
