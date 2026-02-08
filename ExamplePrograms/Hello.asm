; SZYMDOWS VM - TEST PROGRAM
; Prints "HELLO" diagonally and counts in AX

MOV AX, 0       ; Initialize Counter
MOV CX, 0       ; Initialize Screen Index

START:
    ; Print 'H' (72)
    PRINT 72, CX    
    ADD CX, 82      ; Move down 1 line + 2 chars right
    
    ; Print 'E' (69)
    PRINT 69, CX
    ADD CX, 82
    
    ; Print 'L' (76)
    PRINT 76, CX
    ADD CX, 82

    ; Print 'L' (76)
    PRINT 76, CX
    ADD CX, 82

    ; Print 'O' (79)
    PRINT 79, CX
    
    ; Logic Check
    ADD AX, 1       ; Increment counter
    CMP AX, 5       ; Have we done this 5 times?
    JE FINISH       ; If yes, jump to finish
    
    ; Reset screen pos for next batch slightly offset
    MOV CX, AX
    ADD CX, AX      ; Simple math to shift starting position
    
    JMP START       ; Loop

FINISH:
    HLT             ; Stop CPU