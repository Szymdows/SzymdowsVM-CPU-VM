# Szymdows VM – CPU-VM 1.0

## Overview

**Szymdows VM – CPU-VM Extended** is a **Python-based virtual machine and CPU emulator** with an expanded instruction set, enhanced stack operations, advanced control flow, and DOS-style text display. Users can **load, step through, and run assembly code**, view registers and flags, and interact with a classic 80×25 character text display via a **PyQt6 GUI**.

This VM is designed to be **educational, extendable, and modular**, ideal for learning CPU architecture, low-level programming, and assembly language concepts.

---

## Features

- Virtual CPU with general-purpose registers (`AX`, `BX`, `CX`, `DX`) and pointer registers (`SP`, `BP`, `SI`, `DI`)
- Expanded **instruction set**: arithmetic, logic, floating-point simulation, stack, control flow, string operations, and system instructions
- Extended flags: Zero (`Z`), Sign (`S`), Overflow (`O`), Error (`E`), Carry (`C`), Parity (`P`), Direction (`D`)
- DOS-style text display using **CP437 font** (`PerfectDOSVGA437.ttf`)
- GUI interface built with **PyQt6**
- Load `.asm` or `.txt` assembly files and execute them
- Step-by-step or continuous execution mode
- Registers, flags, and next instruction viewer for debugging
- 80×25 text screen simulation
- Status bar messages for program state, halting, or errors
- Example programs included in the `ExamplePrograms` folder

---

## Instruction Set

### 1. Data Transfer
- `MOV dest, src` – Move value to register or memory
- `XCHG reg1, reg2` – Swap two registers
- `CLR reg` – Clear register
- `BSWAP reg` – Swap bytes in 16-bit register
- `CBW`, `CWD`, `CDQ` – Convert byte to word / word to double / double to quad
- `LEA` – Load effective address (simplified)

### 2. Stack Operations
- `PUSH reg/mem` – Push value onto stack
- `POP reg/mem` – Pop value from stack
- `PUSHA` – Push all general registers and pointers
- `POPA` – Pop all registers (reverse order)
- `PUSHF`, `POPF` – Push/Pop flags
- `LEAVE` – Restore base pointer and stack pointer

### 3. Arithmetic
- `ADD`, `ADC` – Addition (+ carry)
- `SUB`, `SBB` – Subtraction (- borrow)
- `INC`, `DEC` – Increment / Decrement
- `MUL`, `IMUL` – Multiply
- `DIV`, `IDIV` – Divide
- `MOD` – Modulus
- `NEG` – Negate
- `XADD` – Exchange and add
- Floating-point simulations: `FADD`, `ABS/FABS`, `SQRT/FSQRT`, `FSIN`, `FCOS`

### 4. Bitwise & Shifts
- `AND`, `OR`, `XOR`, `NOT`
- `SHL/SAL` – Shift left
- `SHR` – Logical shift right
- `SAR` – Arithmetic shift right
- `ROL`, `ROR` – Rotate left/right
- `RCL`, `RCR` – Rotate through carry left/right

### 5. Control Flow & Jumps
- `CMP`, `TEST` – Compare values
- Unconditional: `JMP label`
- Conditional (Unsigned): `JA/JNBE`, `JAE/JNB`, `JB/JNAE/JC`, `JBE/JNA`
- Conditional (Signed): `JE/JZ`, `JNE/JNZ`, `JG/JNLE`, `JGE/JNL`, `JL/JNGE`, `JLE/JNG`
- Flag-specific: `JO`, `JNO`, `JS`, `JNS`, `JP/JPE`, `JNP/JPO`, `JNC`, `JC`
- `JCXZ` – Jump if `CX` is zero

### 6. Conditional Moves
- `CMOVcc dest, src` – Move if condition (`Z`, `NZ`, `S`, `NS`, `C`, `NC`, `O`, `NO`, `G`, `GE`, `L`, `LE`) is met

### 7. Set Byte on Condition
- `SETcc reg` – Set to 1 or 0 based on condition (`Z`, `NZ`, `S`, `NS`, `C`, `NC`, `O`, `NO`, `G`, `GE`, `L`, `LE`, `P`, `NP`)

### 8. Loops
- `LOOP label` – Decrement `CX` and loop if not zero
- `LOOPE/LOOPZ label` – Loop if `CX != 0` and `Z=1`
- `LOOPNE/LOOPNZ label` – Loop if `CX != 0` and `Z=0`

### 9. String Operations
- `MOVS/MOVSB/MOVSW` – Move memory from `[SI]` to `[DI]`
- `LODS/LODSB/LODSW` – Load from `[SI]` to `AX`
- `STOS/STOSB/STOSW` – Store `AX` to `[DI]`
- `CMPS/CMPSB/CMPSW` – Compare `[SI]` with `[DI]`
- `SCAS/SCASB/SCASW` – Compare `AX` with `[DI]`

### 10. Flag Control
- `CLC`, `STC`, `CMC` – Clear, set, or complement carry
- `CLD`, `STD` – Clear or set direction flag
- `CLI`, `STI` – Interrupt control (not implemented)
- `LAHF`, `SAHF` – Load/Store flags (basic simulation)

### 11. Subroutines
- `CALL label` – Call a subroutine
- `RET` – Return from subroutine

### 12. Special / Video / System
- `HLT` – Halt execution
- `NOP` – No operation
- `PRINT char, pos` – Print ASCII character at video memory
- `CLS` – Clear screen
- `RAND reg, n` – Generate random integer
- `DEBUG` – Print debug info
- `CPUID` – CPU identification
- `RDTSC` – Read timestamp counter
- `INT n` – Basic interrupt handling
- `SLEEP` – Consume CPU cycle

---

## CPU Architecture

- **Registers:** 
  - General purpose: `AX`, `BX`, `CX`, `DX`  
  - Stack and base: `SP` (stack pointer), `BP` (base pointer)  
  - Index: `SI`, `DI`  
  - The virtual CPU is **16-bit–inspired**, using classic x86-style registers. Internally, registers use unbounded integers, with **16-bit signed overflow detection** for educational clarity.
- **Instruction Pointer (`IP`):** Tracks the current instruction to execute.
- **Flags:** 
  - `Z` (Zero), `S` (Sign), `O` (Overflow), `E` (Error/Halt), `C` (Carry), `P` (Parity), `D` (Direction)
- **Memory:** 
  - 64 KB RAM for program and data  
  - Video memory for **80×25 character display**
- **Stack:** 
  - Implemented in RAM, growing downward  
  - Supports `PUSH`, `POP`, `PUSHA`, `POPA`, `PUSHF`, `POPF`, and `LEAVE`

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

- Optional strict 16-bit wrapping mode
- More accurate flag behavior
- Expand instruction set with advanced math and logic
- Memory-mapped I/O devices
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