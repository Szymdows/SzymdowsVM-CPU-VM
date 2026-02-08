# Szymdows VM – CPU-VM 1.0

## Overview

**Szymdows VM – CPU-VM** is a custom virtual machine and CPU emulator written in **Python**, featuring a DOS-style text display and a simplified Intel-syntax assembly language. Users can **open and run assembly code files**, view registers, and execute instructions step by step or continuously in a graphical interface.

This project is designed to be **educational, extendable, and modular**, making it ideal for learning low-level programming and CPU architecture.

---

## Features

- Virtual CPU with general-purpose registers and stack pointers
- Expandable **instruction set** (arithmetic, logic, stack, control flow, and system instructions)
- DOS-style text display using the CP437 font (`PerfectDOSVGA437.ttf`)
- GUI interface implemented with **PyQt6**
- Load assembly code files (`.asm` or `.txt`) and execute them
- Step-by-step instruction execution or continuous execution
- Register and flags viewer for debugging
- Screen output viewer simulating a classic 80×25 character display
- Status messages for program state and halting
- Example programs are included in the folder `ExamplePrograms`

---

## Current Instruction Set

The emulator currently supports the following instructions:

### Data Transfer
- `MOV dest, src` – Move value from `src` to `dest` (register or memory)
- `XCHG reg1, reg2` – Swap values of two registers
- `CLR reg` – Clear a register

### Stack Operations
- `PUSH reg/mem` – Push value onto stack
- `POP reg/mem` – Pop value from stack
- `PUSHA` – Push all general registers (AX, BX, CX, DX)
- `POPA` – Pop all general registers (reverse order)

### Arithmetic Operations
- `ADD`, `SUB`, `INC`, `DEC`, `MUL`, `DIV`, `MOD`
- `NEG`, `ABS`, `SQRT`, `POW`, `MIN`, `MAX`

### Bitwise Logic
- `AND`, `OR`, `XOR`, `NOT`
- `SHL` – Shift left
- `SHR` – Shift right

### Control Flow
- `CMP`, `TEST`
- `JMP`, `JE/JZ`, `JNE/JNZ`
- `JG`, `JGE`, `JL`, `JLE`

### Subroutines
- `CALL label` – Call subroutine
- `RET` – Return from subroutine

### Special / System Instructions
- `HLT` – Halt execution
- `NOP` – No operation
- `PRINT char, pos` – Display character at video memory position
- `CLS` – Clear screen
- `RAND reg, n` – Generate random integer 0 to n-1
- `WAIT` – Placeholder for delay
- `DEBUG` – Print register debug info

---

## CPU Architecture

- **Registers:** AX, BX, CX, DX (general purpose); SP (stack pointer); BP (base pointer); SI/DI (index registers)
- **Instruction Pointer (IP):** Tracks the current instruction
- **Flags:** Z (zero), S (sign), O (overflow), E (error/halt)
- **Memory:** 4 KB RAM + video memory (80×25 characters)
- **Stack:** Implemented in RAM, growing downward

---

## GUI Interface

- PyQt6-based window
- **Left panel:** DOS-style text screen
- **Right panel:** Controls and debugging info
  - Load ASM file
  - Run / Pause
  - Step instruction
  - Reset CPU
  - Registers and flags display
  - Source code viewer
- Supports real-time updates with the DOS font

---

## How to Run

1. Install Python 3.10+ (or compatible)
2. Install PyQt6:
   ```bash
   pip install PyQt6
3. Run the emulator:
   ```bash
   python main.py
4. Use the GUI to load an assembly file and execute it.

## Example Programs

- Example assembly programs are provided in the folder:
   ```bash
   ExamplePrograms/
- These demonstrate basic CPU operations, screen output, and control flow.

## How to Contribute

- Contributions are welcome.

### Setup

- Fork the repository or download the source.
- Install:
  - Python 3.10+
  - PyQt6

### Development Guidelines

- Study the `VirtualCPU` class, registers, RAM, and flags.
- Understand the current instruction set.
- Add new instructions inside the `step()` function.
- Update `_update_flags()` when required.
- Improve the GUI (screen rendering, debugger, source viewer).

### Contribution Rules

- Follow **PEP8** coding style.
- Comment code clearly.
- Test new instructions using small assembly programs.
- Preserve existing functionality.
- Submit a pull request with a clear description of changes.

## License

This project is licensed under the **MIT License**, allowing:
- Free use, modification, and distribution.
- Community contributions.
- Forking and commercial use.

## Future Plans

- Expand instruction set with advanced math and logic
- Memory-mapped I/O for simulated devices
- Keyboard input and real-time interaction
- Graphics modes beyond text
- Advanced debugging tools:
  - Breakpoints
  - Step-back execution
  - Watchpoints
- Save/load RAM state
- Multiple ISA versions with backward compatibility

## Notes

This project is intended as an educational emulator and a foundation for experimenting with virtual computer systems and CPU design.