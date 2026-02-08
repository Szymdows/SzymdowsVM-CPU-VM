; ==========================================
; SZYMDOWS DOS SIMULATION
; ==========================================
; This program simulates a user typing commands.
; Since there is no Keyboard Input instruction,
; this is a scripted sequence.

; --- MEMORY MAP ---
; [0] = Cursor Position (Video RAM Index 0-1999)
; [1] = Temp storage for math

; --- BOOT SEQUENCE ---
CLS
MOV [0], 0          ; Reset Cursor to top-left

; Print "Starting..."
MOV AX, 83          ; 'S'
CALL print_char
MOV AX, 116         ; 't'
CALL print_char
MOV AX, 97          ; 'a'
CALL print_char
MOV AX, 114         ; 'r'
CALL print_char
MOV AX, 116         ; 't'
CALL print_char
MOV AX, 105         ; 'i'
CALL print_char
MOV AX, 110         ; 'n'
CALL print_char
MOV AX, 103         ; 'g'
CALL print_char
MOV AX, 46          ; '.'
CALL print_char
MOV AX, 46          ; '.'
CALL print_char
MOV AX, 46          ; '.'
CALL print_char

CALL delay_long
CALL new_line

; Print "Memory: 4KB OK"
MOV AX, 77          ; 'M'
CALL print_char
MOV AX, 101         ; 'e'
CALL print_char
MOV AX, 109         ; 'm'
CALL print_char
MOV AX, 58          ; ':'
CALL print_char
MOV AX, 32          ; Space
CALL print_char
MOV AX, 52          ; '4'
CALL print_char
MOV AX, 75          ; 'K'
CALL print_char
MOV AX, 66          ; 'B'
CALL print_char
MOV AX, 32          ; Space
CALL print_char
MOV AX, 79          ; 'O'
CALL print_char
MOV AX, 75          ; 'K'
CALL print_char

CALL delay_long
CALL new_line
CALL new_line

; ==========================================
; COMMAND 1: VER
; ==========================================
CALL print_prompt   ; C:\>
CALL delay_short

; User types 'ver'
MOV AX, 118         ; 'v'
CALL type_char      ; Type with delay
MOV AX, 101         ; 'e'
CALL type_char
MOV AX, 114         ; 'r'
CALL type_char

CALL delay_short
CALL new_line       ; Enter key pressed

; System responds: "Szymdows v1.0"
MOV AX, 83          ; 'S'
CALL print_char
MOV AX, 122         ; 'z'
CALL print_char
MOV AX, 121         ; 'y'
CALL print_char
MOV AX, 109         ; 'm'
CALL print_char
MOV AX, 100         ; 'd'
CALL print_char
MOV AX, 111         ; 'o'
CALL print_char
MOV AX, 119         ; 'w'
CALL print_char
MOV AX, 115         ; 's'
CALL print_char
MOV AX, 32          ; Space
CALL print_char
MOV AX, 118         ; 'v'
CALL print_char
MOV AX, 49          ; '1'
CALL print_char
MOV AX, 46          ; '.'
CALL print_char
MOV AX, 48          ; '0'
CALL print_char

CALL new_line
CALL new_line

; ==========================================
; COMMAND 2: DIR
; ==========================================
CALL print_prompt
CALL delay_short

; User types 'dir'
MOV AX, 100         ; 'd'
CALL type_char
MOV AX, 105         ; 'i'
CALL type_char
MOV AX, 114         ; 'r'
CALL type_char

CALL delay_short
CALL new_line

; List Files
; "GAME.EXE"
MOV AX, 71          ; 'G'
CALL print_char
MOV AX, 65          ; 'A'
CALL print_char
MOV AX, 77          ; 'M'
CALL print_char
MOV AX, 69          ; 'E'
CALL print_char
MOV AX, 46          ; '.'
CALL print_char
MOV AX, 69          ; 'E'
CALL print_char
MOV AX, 88          ; 'X'
CALL print_char
MOV AX, 69          ; 'E'
CALL print_char
MOV AX, 32          ; Space
CALL print_char
MOV AX, 32          ; Space
CALL print_char
MOV AX, 50          ; '2'
CALL print_char
MOV AX, 75          ; 'K'
CALL print_char
CALL new_line

; "TEXT.TXT"
MOV AX, 84          ; 'T'
CALL print_char
MOV AX, 69          ; 'E'
CALL print_char
MOV AX, 88          ; 'X'
CALL print_char
MOV AX, 84          ; 'T'
CALL print_char
MOV AX, 46          ; '.'
CALL print_char
MOV AX, 84          ; 'T'
CALL print_char
MOV AX, 88          ; 'X'
CALL print_char
MOV AX, 84          ; 'T'
CALL print_char
MOV AX, 32          ; Space
CALL print_char
MOV AX, 32          ; Space
CALL print_char
MOV AX, 49          ; '1'
CALL print_char
MOV AX, 75          ; 'K'
CALL print_char
CALL new_line
CALL new_line

; ==========================================
; COMMAND 3: CLS
; ==========================================
CALL print_prompt
CALL delay_short

; User types 'cls'
MOV AX, 99          ; 'c'
CALL type_char
MOV AX, 108         ; 'l'
CALL type_char
MOV AX, 115         ; 's'
CALL type_char
CALL delay_short

; Execute Clear Screen
CLS
MOV [0], 0          ; Reset cursor pos
CALL print_prompt   ; Print fresh prompt

HLT                 ; End of Simulation


; ==========================================
; SUBROUTINES
; ==========================================

; --- PRINT PROMPT (C:\>) ---
print_prompt:
    MOV AX, 67      ; 'C'
    CALL print_char
    MOV AX, 58      ; ':'
    CALL print_char
    MOV AX, 92      ; '\'
    CALL print_char
    MOV AX, 62      ; '>'
    CALL print_char
    RET

; --- TYPE CHAR (Print + Delay) ---
type_char:
    CALL print_char
    CALL delay_type
    RET

; --- PRINT CHAR ---
; Input: AX = ASCII Code
; Updates: [0] (Cursor Pos)
print_char:
    MOV BX, [0]     ; Load Cursor Pos
    PRINT AX, BX    ; Print to Screen
    INC BX          ; Move Cursor Forward
    MOV [0], BX     ; Save Cursor Pos
    RET

; --- NEW LINE ---
; Moves cursor to start of next row
new_line:
    MOV AX, [0]     ; Load Cursor
    DIV AX, 80      ; AX = AX / 80 (Get Row Number)
    INC AX          ; Next Row
    MUL AX, 80      ; AX = Row * 80 (Start of new line)
    MOV [0], AX     ; Save new position
    RET

; --- DELAY (Typewriter feel) ---
delay_type:
    MOV CX, 25      ; Loop count
loop_t:
    DEC CX
    JNZ loop_t      ; Jump if Not Zero
    RET

; --- DELAY SHORT ---
delay_short:
    MOV CX, 100
loop_s:
    DEC CX
    JNZ loop_s
    RET

; --- DELAY LONG ---
delay_long:
    MOV CX, 400
loop_l:
    DEC CX
    JNZ loop_l
    RET