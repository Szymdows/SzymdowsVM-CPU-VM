; ==========================================
; BOUNCING BALL & STARFIELD DEMO
; For Szymdows VM
; ==========================================

; --- INITIALIZATION ---
CLS                 ; Clear the screen

; Initialize Variables in RAM
; [0] = Ball X Position
; [1] = Ball Y Position
; [2] = Velocity X
; [3] = Velocity Y

MOV [0], 40         ; Start X in middle
MOV [1], 12         ; Start Y in middle
MOV [2], 1          ; Velocity X = 1
MOV [3], 1          ; Velocity Y = 1

; ==========================================
; MAIN LOOP
; ==========================================
loop_start:

    ; ---------------------------
    ; 1. ERASE OLD BALL
    ; ---------------------------
    CALL calc_offset    ; Calculate memory address for current X,Y into SI
    PRINT 32, SI        ; Print SPACE (ASCII 32) to erase old ball

    ; ---------------------------
    ; 2. DRAW STARFIELD (Random noise)
    ; ---------------------------
    ; Draw a random star '.'
    RAND AX, 2000       ; Random position 0-1999
    PRINT 46, AX        ; Print '.' (ASCII 46)

    ; Occasionally clear a random spot to prevent screen filling up
    RAND AX, 2000
    PRINT 32, AX        ; Print ' '

    ; ---------------------------
    ; 3. UPDATE POSITION
    ; ---------------------------
    ; X = X + VelX
    MOV AX, [0]         ; Load X
    ADD AX, [2]         ; Add VelX
    MOV [0], AX         ; Store X

    ; Y = Y + VelY
    MOV BX, [1]         ; Load Y
    ADD BX, [3]         ; Add VelY
    MOV [1], BX         ; Store Y

    ; ---------------------------
    ; 4. COLLISION DETECTION X
    ; ---------------------------
    CMP AX, 79          ; Compare X with Right Edge
    JGE bounce_x        ; If >= 79, bounce
    CMP AX, 0           ; Compare X with Left Edge
    JLE bounce_x        ; If <= 0, bounce
    JMP check_y         ; Otherwise check Y

bounce_x:
    MOV CX, [2]         ; Load VelX
    NEG CX              ; Invert it
    MOV [2], CX         ; Store new VelX
    ; Push ball out of wall to prevent getting stuck
    ADD AX, CX          
    MOV [0], AX

    ; ---------------------------
    ; 5. COLLISION DETECTION Y
    ; ---------------------------
check_y:
    CMP BX, 24          ; Compare Y with Bottom Edge
    JGE bounce_y
    CMP BX, 0           ; Compare Y with Top Edge
    JLE bounce_y
    JMP draw_ball

bounce_y:
    MOV DX, [3]         ; Load VelY
    NEG DX              ; Invert it
    MOV [3], DX         ; Store new VelY
    ; Push ball out of wall
    ADD BX, DX
    MOV [1], BX

    ; ---------------------------
    ; 6. DRAW NEW BALL
    ; ---------------------------
draw_ball:
    CALL calc_offset    ; Recalculate SI for new position
    PRINT 79, SI        ; Print 'O' (ASCII 79)

    JMP loop_start      ; Infinite Loop

; ==========================================
; SUBROUTINE: CALCULATE VIDEO OFFSET
; Input:  [0] is X, [1] is Y
; Output: SI = (Y * 80) + X
; ==========================================
calc_offset:
    MOV SI, [1]         ; Load Y
    MUL SI, 80          ; SI = Y * 80
    ADD SI, [0]         ; SI = SI + X
    RET