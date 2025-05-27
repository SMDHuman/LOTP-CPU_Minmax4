# LOTP-CPU_Minmax4
A Simple 8 bit, 1 instruction per pulse CPU with expandable data bus. It executes every instruction in 1 clock pulse and every instruction occupies 1 or 2 bytes in memory, based on if it has immediate value. All registers can be bigger that 8 bit word size and must be equal as size. Stack word size is same as registers. has 16 bit program counter.

## Instructions

### Byte Layout
| Opcode | Arg A | Arg B | Extra Data Byte |
|--------|-----------|--|------------|
|  [0:3]      | [4:5]     | [6:7] | [8:15]  |

### Description
| Name | Opcode | Arg A | Arg B | Extra Data Byte | Description |
|------|---|-----------|-------------|------------|-------------|
| NOP  | 0 | None      | None        | No         | No operation |
| MOV  | 1 | target    | register    | Optional   | Move data register to register, or push 1 byte data to a register |
| LOD  | 2 | target    | register    | Yes        | Load to target from ram using register as pointer + offset |
| STR  | 3 | target    | register    | Yes        | Store target to ram using register as pointer + offset |
| ADD  | 4 | target    | register    | Optional   | Add target with register or immediate data and store to target |
| SUB  | 5 | target    | register    | Optional   | Subtract register or immediate data from target and store to target |
| AND  | 6 | target    | register    | Optional   | Bitwise and operation with target and register or immediate data |
| OR   | 7 | target    | register    | Optional   | Bitwise or operation with target and register or immediate data |
| XOR  | 8 | target    | register    | Optional   | Bitwise xor operation with target and register or immediate data |
| INV  | 9 | target    | None        | No         | Bitwise not operation on target |
| ROT  | A | target    | register    | Optional   | Rotate bits to left given ammount by register or immediate data |
| BRC  | B | condition | register    | Optional   | If condition is true, makes relative jump |
| PSH  | C | target    | None        | No         | Push target to stack   |
| POP  | D | target    | None        | No         | Pop stack to target   |
| IN   | E | target    | port        | No         | Set target value with selected port |
| OUT  | F | port      | register    | Optional   | Set output value with a register value or immediate data |

> **Special Use Cases:**
> - Relative jump with range of [-128, 127] 
>   ```
>   MOV PC 'value'
>   ```
> - Jumping to last address of the memory will make the cpu halt
>   ``` 
>   MOV R0 0  ; Set Register 0 to value 0
>   INV R0    ; Inverse all bits to make the value as big as it can 
>   MOV PC R0 ; Jump to there
>   ```
> - Unlike other operations, `PSH` instruction can read Program Counter register


### Registers and Arguments

| Name | 00 | 01 | 10 | 11 |
|------|---|---|---|---|
| target | `Program Counter` | `R0` | `R1` | `R2` |
| registers | `Immediate` | `R0` | `R1` | `R2` |
| condition | `Carry Flag` | `R0 == 0` | `!Carry Flag` | `R0 != 0` |
| port | `A` | `B` | `C` | `D` |