import sys, os
import argparse

def main():
  parser = argparse.ArgumentParser(description='Minmax4EMUpy - Minmax4 Emulator')
  parser.add_argument('input', type=str, help='Input file path')
  parser.add_argument('-d', "--debug", action='store_true', help='Enable debug mode')
  parser.add_argument('-p', "--print_out", action='store_true', help='Print the output')
  parser.add_argument('-m', "--mem_print", help='Print sections of memory', type=str)
  args = parser.parse_args()
  #...
  input_file = args.input
  if not os.path.isfile(input_file):
    print(f"Error: File '{input_file}' not found.")
    sys.exit(1)
  #...
  magic = "MNMX"
  version = 0x04
  byte_length = 0
  ROM: bytearray = bytearray(0)
  with open(input_file, 'rb') as f:
    header = f.read(6)
    if header[:4] != magic.encode():
      print(f"Error: Invalid file format. Expected '{magic}', got '{header.decode()}'")
      sys.exit(1)
    if header[4] != version:
      print(f"Error: Unsupported version. Expected {version}, got {header[4]}")
      sys.exit(1)
    byte_length = header[5]
    if byte_length < 1:
      print(f"Error: Invalid byte length. Expected at least 1, got {byte_length}")
      sys.exit(1)
  
    # Read the rest of the file and process it
    ROM += f.read()
  #...
  byte_mask = (1 << (byte_length * 8)) - 1
  ROM += bytearray([0x00] * (byte_mask - len(ROM)))  # Pad with zeros if needed
  print("Ready to process the input data...")
  if(args.debug): print("ROM: ", [hex(x) for x in ROM])
  #----------------------------------------------------------------------------
  # Initialize registers and flags
  reg_pc = 0x0000
  reg_r0 = 0x0000
  reg_r1 = 0x0000
  reg_r2 = 0x0000
  carry_flag = False
  port_A = 0x00
  port_B = 0x00
  port_A_DIR = 0x00
  port_B_DIR = 0x00
  stack = []
  instructions = ["NOP", "MOV", "LOD", "STR", "ADD", "SUB", "AND", "OR", "XOR", "INV", "ROT", "BRC", "PSH", "POP", "IN", "OUT"]
  #RAM = bytearray(byte_mask)

  def set_target(target, value):
    nonlocal reg_pc, reg_r0, reg_r1, reg_r2
    if target == 0:
      reg_pc = value & byte_mask
    elif target == 1:
      reg_r0 = value & byte_mask
    elif target == 2:
      reg_r1 = value & byte_mask
    elif target == 3:
      reg_r2 = value & byte_mask

  def push_target(target, value):
    nonlocal reg_pc, reg_r0, reg_r1, reg_r2
    if target == 0:
      reg_pc = (reg_pc + (value & 0xFF)) & byte_mask
    elif target == 1:
      reg_r0 = (reg_r0<< 8 | (value & 0xFF)) & byte_mask
    elif target == 2:
      reg_r1 = (reg_r1<< 8 | (value & 0xFF)) & byte_mask
    elif target == 3:
      reg_r2 = (reg_r2<< 8 | (value & 0xFF)) & byte_mask

  def get_register(reg):
    if reg == 0:
      return reg_pc
    elif reg == 1:
      return reg_r0
    elif reg == 2:
      return reg_r1
    elif reg == 3:
      return reg_r2
    
  def set_port(port, value):
    nonlocal port_A, port_B, port_A_DIR, port_B_DIR
    if port == 0:
      port_A = value & byte_mask
    elif port == 1:
      port_B = value & byte_mask
    elif port == 2:
      port_A_DIR = value & byte_mask
    elif port == 3:
      port_B_DIR = value & byte_mask

  def push_port(port, value):
    nonlocal port_A, port_B, port_A_DIR, port_B_DIR
    if port == 0:
      port_A = (port_A << 8 | (value & 0xFF)) & byte_mask
    elif port == 1:
      port_B = (port_B << 8 | (value & 0xFF)) & byte_mask
    elif port == 2:
      port_A_DIR = (port_A_DIR << 8 | (value & 0xFF)) & byte_mask
    elif port == 3:
      port_B_DIR = (port_B_DIR << 8 | (value & 0xFF)) & byte_mask
  
  def get_port(port):
    if port == 0:
      return port_A
    elif port == 1:
      return port_B
    elif port == 2:
      return port_A_DIR
    elif port == 3:
      return port_B_DIR

  #----------------------------------------------------------------------------
  # Main loop
  while( reg_pc < len(ROM)):
    instruction = ROM[reg_pc] & 0x0F
    arg1, arg2 = (ROM[reg_pc] & 0x30) >> 4, (ROM[reg_pc] & 0xC0) >> 6
    reg_pc = (reg_pc+1) & byte_mask

    match instruction:
      #---------------------------------------------------------------
      # NOP
      case 0x0: 
        pass
      #---------------------------------------------------------------
      # MOV
      case 0x1:
        if(arg2 == 0x0):
          push_target(arg1, ROM[reg_pc])
          reg_pc = (reg_pc+1) & byte_mask
        else:
          set_target(arg1, get_register(arg2))
      #---------------------------------------------------------------
      # LOD
      case 0x2:
        push_target(arg1, ROM[get_register(arg2) + ROM[reg_pc]])
        reg_pc = (reg_pc+1) & byte_mask
      #---------------------------------------------------------------
      # STR
      case 0x3:
        ROM[get_register(arg2) + ROM[reg_pc]] = get_register(arg1) & 0xFF
        reg_pc = (reg_pc+1) & byte_mask
      #---------------------------------------------------------------
      # ADD
      case 0x4:
        _a = get_register(arg1)
        if(arg2 == 0x0):
          _b = ROM[reg_pc]
          reg_pc = (reg_pc+1) & byte_mask
        else:
          _b = get_register(arg2)
        _c = _a + _b
        if(_c > byte_mask):
          carry_flag = True
        else:
          carry_flag = False
        set_target(arg1, _c & byte_mask)
      #----------------------------------------------------------------
      # SUB
      case 0x5:
        _a = get_register(arg1)
        if(arg2 == 0x0):
          _b = ROM[reg_pc]
          reg_pc = (reg_pc+1) & byte_mask
        else:
          _b = get_register(arg2)
        _c = _a - _b
        if(_c < 0):
          _c = byte_mask + _c + 1
          carry_flag = True
        else:
          carry_flag = False
        set_target(arg1, _c & byte_mask)
      #----------------------------------------------------------------
      # AND
      case 0x6:
        _a = get_register(arg1)
        if(arg2 == 0x0):
          _b = ROM[reg_pc]
          reg_pc = (reg_pc+1) & byte_mask
        else:
          _b = get_register(arg2)
        _c = _a & _b
        set_target(arg1, _c & byte_mask)
      #----------------------------------------------------------------
      # OR
      case 0x7:
        _a = get_register(arg1)
        if(arg2 == 0x0):
          _b = ROM[reg_pc]
          reg_pc = (reg_pc+1) & byte_mask
        else:
          _b = get_register(arg2)
        _c = _a | _b
        set_target(arg1, _c & byte_mask)
      #----------------------------------------------------------------
      # XOR
      case 0x8:
        _a = get_register(arg1)
        if(arg2 == 0x0):
          _b = ROM[reg_pc]
          reg_pc = (reg_pc+1) & byte_mask
        else:
          _b = get_register(arg2)
        _c = _a ^ _b
        set_target(arg1, _c & byte_mask)
      #----------------------------------------------------------------
      # INV
      case 0x9:
        _a = get_register(arg1)
        _c = ~_a
        set_target(arg1, _c & byte_mask)
      #----------------------------------------------------------------
      # ROT
      case 0xA:
        _a = get_register(arg1)
        if(arg2 == 0x0):
          _b = ROM[reg_pc]
          reg_pc = (reg_pc+1) & byte_mask
        else:
          _b = get_register(arg2)
        _c = (_a << _b) | (_a >> (byte_length*8 - _b))
        set_target(arg1, _c & byte_mask)
      #----------------------------------------------------------------
      # BRC
      case 0xB:
        cond = 0 
        cond += (carry_flag and arg1 == 0)
        cond += (reg_r0 == 0 and arg1 == 1)
        cond += ((not carry_flag) and arg1 == 2)
        cond += (reg_r0 != 0 and arg1 == 3)
        if(cond > 0):
          if(arg2 == 0x0):
            offset = ROM[reg_pc]
            offset =  offset - 256 if offset > 127 else offset
            reg_pc = (reg_pc + offset-1) & byte_mask
          else:
            reg_pc = get_register(arg2) & byte_mask
        else:
          if(arg2 == 0x0):
            reg_pc = (reg_pc+1) & byte_mask
      #----------------------------------------------------------------
      # PSH
      case 0xC:
        stack.append(get_register(arg1))
      #----------------------------------------------------------------
      # POP
      case 0xD:
        if(len(stack) > 0):
          set_target(arg1, stack.pop())
        else:
          set_target(arg1, 0x00)
      #----------------------------------------------------------------
      # IN
      case 0xE:
        set_target(arg1, get_port(arg2))
      #---------------------------------------------------------------- 
      # OUT
      case 0xF:
        if(arg2 == 0x0):
          push_port(arg1, ROM[reg_pc])
          reg_pc = (reg_pc+1) & byte_mask
        else:
          set_port(arg1, get_register(arg2))
        if(args.print_out):
          value = get_port(arg1)
          print(f"Output: {value}, [{hex(value)}], '{chr(value)}'")
      #----------------------------------------------------------------
      # Invalid instruction
      case _:
        print(f"Error: Invalid instruction {instruction} at address {reg_pc-1}")
        sys.exit(1)
      
    # Print the final state of the registers and flags
    if(args.debug):
      print("-" * 40)
      print(f"Instruction: {instructions[instruction]}, Arg1: {hex(arg1)}, Arg2: {hex(arg2)}")
      print(f"PC: {hex(reg_pc)}, R0: {hex(reg_r0)}, R1: {hex(reg_r1)}, R2: {hex(reg_r2)}, Carry: {hex(carry_flag)}, Stack: {[hex(x) for x in stack]}")
      print(f"Port A: {hex(port_A)}, Port B: {hex(port_B)}, Port A DIR: {hex(port_A_DIR)}, Port B DIR: {hex(port_B_DIR)}")
      #print("ROM: ", [hex(x) for x in ROM])
      input("Press Enter to continue...")
  
  # Print the final state of the registers and flags
  print("-" * 40)
  print("Final State:")
  print(f"PC: {hex(reg_pc)}, R0: {hex(reg_r0)}, R1: {hex(reg_r1)}, R2: {hex(reg_r2)}, Carry: {hex(carry_flag)}, Stack: {[hex(x) for x in stack]}")
  print(f"Port A: {hex(port_A)}, Port B: {hex(port_B)}, Port A DIR: {hex(port_A_DIR)}, Port B DIR: {hex(port_B_DIR)}")
  if(args.mem_print):
    start, end = args.mem_print.split(":")
    start = int(start, 0)
    end = int(end, 0)
    print("Memory Dump:")
    for i in range(start, end + 1):
      print(f"0x{i:02X}: {hex(ROM[i])}")

if( __name__ == "__main__"):
  main()