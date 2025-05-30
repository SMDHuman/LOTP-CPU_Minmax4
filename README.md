# LOTP-CPU_Minmax4.5
A Simple 8 bit, 1 instruction per pulse CPU. It executes every instruction in 1 clock pulse and every instruction occupies 1 or 2 bytes in memory, based on if it has immediate value. has 16 bit program counter.

## Instructions

### Byte Layout
| Opcode | Arg A | Arg B | Extra Data Byte |
|--------|-----------|--|------------|
|  [0:3]      | [4:5]     | [6:7] | [8:15]  |

### Description
| Name | Opcode | Arg A | Arg B | Extra Data Byte |Def Val| Description |
|------|---|-----------|-------------|------------|-------|-------------|
| HLT  | 0 | X         | X           | No         |  0    | Halt the cpu clock to stop |
| MOV  | 1 | target    | register    | Optional   |  0    | Move data register to register, or push 1 byte data to a register |
| LOD  | 2 | target    | register    | Optional   |  0    | Load to target from memory using $YX registers as pointer + offset |
| STR  | 3 | target    | register    | Optional   |  0    | Store target to memory using $YX registers as pointer + offset |
| ADD  | 4 | target    | register    | Optional   |  1    | Add target with register or immediate data and store to target |
| SUB  | 5 | target    | register    | Optional   |  1    | Subtract register or immediate data from target and store to target |
| AND  | 6 | target    | register    | Optional   |  128  | Bitwise and operation with target and register or immediate data |
| OR   | 7 | target    | register    | Optional   |  0    | Bitwise or operation with target and register or immediate data |
| XOR  | 8 | target    | register    | Optional   |  255  | Bitwise xor operation with target and register or immediate data |
| ROT  | 9 | target    | register    | Optional   |  1    | Rotate bits to left given ammount by register or immediate data |
| JMP  | A | X         | register    | Optional   |  0    | Set PC to $YX +  Offset|
| BRC  | B | condition | register    | Optional   |  2    | If condition is true, makes relative jump |
| PSH  | C | target    | X           | No         |  255  | Push target to memory at SP as rightmost and 255 as leftmost|
| POP  | D | target    | X           | No         |  255  | Pop memory to target at SP as rightmost and 255 as leftmost|
| IN   | E | target    | port        | No         |  X    | Set target value with selected port |
| OUT  | F | port      | register    | Optional   |  0    | Set output value with a register value or immediate data |

### Registers and Arguments

| Name | 00 | 01 | 10 | 11 |
|------|---|---|---|---|
| target | `R0` | `R1` | `X` | `Y` |
| registers | `R0` | `R1` | `Immediate` | `Default Value` |
| condition | `Carry Flag` | `Overflow Flag` | `R0 == 0` | `R0 == 255` |
| port | `A` | `B` | `C` | `D` |