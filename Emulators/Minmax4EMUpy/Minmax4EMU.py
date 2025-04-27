import sys, os
import argparse

class MINMAX4():
  def __init__(self, input_file: str):
    #...
    if not os.path.isfile(input_file):
      print(f"Error: File '{input_file}' not found.")
      sys.exit(1)
    #...
    magic = "MNMX"
    version = 0x04
    self.byte_length = 0
    self.ROM = open("./rom.bin", 'wb+')
    with open(input_file, 'rb') as f:
      header = f.read(6)
      if header[:4] != magic.encode():
        print(f"Error: Invalid file format. Expected '{magic}', got '{header.decode()}'")
        sys.exit(1)
      if header[4] != version:
        print(f"Error: Unsupported version. Expected {version}, got {header[4]}")
        sys.exit(1)
      self.byte_length = header[5]
      if self.byte_length < 1:
        print(f"Error: Invalid byte length. Expected at least 1, got {self.byte_length}")
        sys.exit(1)
    
      # Read the rest of the file and process it
      self.ROM.write(f.read())
      self.ROM.seek(0)  # Reset the file pointer to the beginning
    #...
    self.byte_mask = (1 << (self.byte_length * 8)) - 1
    #----------------------------------------------------------------------------
    # Initialize registers and flags
    self.halt = False
    self.reg_pc = 0x0000
    self.reg_r0 = 0x0000
    self.reg_r1 = 0x0000
    self.reg_r2 = 0x0000
    self.carry_flag = False
    self.port_A = 0x00
    self.port_B = 0x00
    self.port_C = 0x00
    self.port_D = 0x00
    self.port_A_update = False
    self.port_B_update = False
    self.port_C_update = False
    self.port_D_update = False
    self.stack = []
    self.instructions = ["NOP", "MOV", "LOD", "STR", "ADD", "SUB", "AND", "OR", "XOR", "INV", "ROT", "BRC", "PSH", "POP", "IN", "OUT"]
    #RAM = bytearray(self.byte_mask)

  def reset(self):
    self.halt = False
    self.reg_pc = 0x0000
    self.reg_r0 = 0x0000
    self.reg_r1 = 0x0000
    self.reg_r2 = 0x0000
    self.carry_flag = False
    self.port_A = 0x00
    self.port_B = 0x00
    self.port_C = 0x00
    self.port_D = 0x00
    self.port_A_update = True
    self.port_B_update = True
    self.port_C_update = True
    self.port_D_update = True
    self.stack.clear()

  def set_target(self, target, value):
    if target == 0:
      self.reg_pc = value & self.byte_mask
    elif target == 1:
      self.reg_r0 = value & self.byte_mask
    elif target == 2:
      self.reg_r1 = value & self.byte_mask
    elif target == 3:
      self.reg_r2 = value & self.byte_mask

  def push_target(self, target, value):
    if target == 0:
      self.reg_pc = (self.reg_pc + (value & 0xFF)) & self.byte_mask
    elif target == 1:
      self.reg_r0 = (self.reg_r0<< 8 | (value & 0xFF)) & self.byte_mask
    elif target == 2:
      self.reg_r1 = (self.reg_r1<< 8 | (value & 0xFF)) & self.byte_mask
    elif target == 3:
      self.reg_r2 = (self.reg_r2<< 8 | (value & 0xFF)) & self.byte_mask

  def get_register(self, reg):
    if reg == 0:
      return self.reg_pc
    elif reg == 1:
      return self.reg_r0
    elif reg == 2:
      return self.reg_r1
    elif reg == 3:
      return self.reg_r2
    
  def set_port(self, port, value):
    if port == 0:
      self.port_A = value & self.byte_mask
      self.port_A_update = True
    elif port == 1:
      self.port_B = value & self.byte_mask
      self.port_B_update = True
    elif port == 2:
      self.port_C = value & self.byte_mask
      self.port_C_update = True
    elif port == 3:
      self.port_D = value & self.byte_mask
      self.port_D_update = True

  def push_port(self, port, value):
    if port == 0:
      self.port_A = (self.port_A << 8 | (value & 0xFF)) & self.byte_mask
      self.port_A_update = True
    elif port == 1:
      self.port_B = (self.port_B << 8 | (value & 0xFF)) & self.byte_mask
      self.port_B_update = True
    elif port == 2:
      self.port_C = (self.port_C << 8 | (value & 0xFF)) & self.byte_mask
      self.port_C_update = True
    elif port == 3:
      self.port_D = (self.port_D << 8 | (value & 0xFF)) & self.byte_mask
      self.port_D_update = True
  
  def get_port(self, port):
    if port == 0:
      return self.port_A
    elif port == 1:
      return self.port_B
    elif port == 2:
      return self.port_C
    elif port == 3:
      return self.port_D
    
  def read_memory(self, address) -> int:
    if address < 0 or address > self.byte_mask:
      raise ValueError("Address out of range")
    elif(address >= self.ROM.__sizeof__()):
      return(0x00)
    self.ROM.seek(address)
    val = self.ROM.read(1)
    if(val == b''):
      return(0x00)
    else:
      return val[0]
  
  def write_memory(self, address, value):
    if address < 0 or address >= self.byte_mask:
      raise ValueError("Address out of range")
    self.ROM.seek(address)
    self.ROM.write(bytes([value & 0xFF]))
  
  def advence_pc(self, offset = 1):
    if(offset + self.reg_pc > self.byte_mask):
      self.halt = True
    else:
      self.reg_pc = (self.reg_pc + offset) & self.byte_mask

  def tick(self):
    #...
    self.port_A_update = False
    self.port_B_update = False
    self.port_C_update = False
    self.port_D_update = False
    #...
    instruction = self.read_memory(self.reg_pc) & 0x0F
    arg1, arg2 = (self.read_memory(self.reg_pc) & 0x30) >> 4, (self.read_memory(self.reg_pc) & 0xC0) >> 6
    self.advence_pc()
    #...
    match instruction:
      #---------------------------------------------------------------
      # NOP
      case 0x0: 
        pass
      #---------------------------------------------------------------
      # MOV
      case 0x1:
        if(arg2 == 0x0):
          self.push_target(arg1, self.read_memory(self.reg_pc))
          self.advence_pc()
        else:
          self.set_target(arg1, self.get_register(arg2))
      #---------------------------------------------------------------
      # LOD
      case 0x2:
        _offset = self.get_register(arg2)
        _adrs = self.read_memory(self.reg_pc)
        self.push_target(arg1, self.read_memory(_offset + _adrs))
        self.advence_pc()
      #---------------------------------------------------------------
      # STR
      case 0x3:
        _offset = self.get_register(arg2)
        _adrs = self.read_memory(self.reg_pc)
        self.write_memory(_offset + _adrs, self.get_register(arg1) & 0xFF)
        self.advence_pc()
      #---------------------------------------------------------------
      # ADD
      case 0x4:
        _a = self.get_register(arg1)
        if(arg2 == 0x0):
          _b = self.read_memory(self.reg_pc)
          self.advence_pc()
        else:
          _b = self.get_register(arg2)
        _c = _a + _b
        if(_c > self.byte_mask):
          self.carry_flag = True
        else:
          self.carry_flag = False
        self.set_target(arg1, _c & self.byte_mask)
      #----------------------------------------------------------------
      # SUB
      case 0x5:
        _a = self.get_register(arg1)
        if(arg2 == 0x0):
          _b = self.read_memory(self.reg_pc)
          self.advence_pc()
        else:
          _b = self.get_register(arg2)
        _c = _a - _b
        if(_c < 0):
          _c = self.byte_mask + _c + 1
          self.carry_flag = True
        else:
          self.carry_flag = False
        self.set_target(arg1, _c & self.byte_mask)
      #----------------------------------------------------------------
      # AND
      case 0x6:
        _a = self.get_register(arg1)
        if(arg2 == 0x0):
          _b = self.read_memory(self.reg_pc)
          self.advence_pc()
        else:
          _b = self.get_register(arg2)
        _c = _a & _b
        self.set_target(arg1, _c & self.byte_mask)
      #----------------------------------------------------------------
      # OR
      case 0x7:
        _a = self.get_register(arg1)
        if(arg2 == 0x0):
          _b = self.read_memory(self.reg_pc)
          self.advence_pc()
        else:
          _b = self.get_register(arg2)
        _c = _a | _b
        self.set_target(arg1, _c & self.byte_mask)
      #----------------------------------------------------------------
      # XOR
      case 0x8:
        _a = self.get_register(arg1)
        if(arg2 == 0x0):
          _b = self.read_memory(self.reg_pc)
          self.advence_pc()
        else:
          _b = self.get_register(arg2)
        _c = _a ^ _b
        self.set_target(arg1, _c & self.byte_mask)
      #----------------------------------------------------------------
      # INV
      case 0x9:
        _a = self.get_register(arg1)
        _c = ~_a
        self.set_target(arg1, _c & self.byte_mask)
      #----------------------------------------------------------------
      # ROT
      case 0xA:
        _a = self.get_register(arg1)
        if(arg2 == 0x0):
          _b = self.read_memory(self.reg_pc)
          self.advence_pc()
        else:
          _b = self.get_register(arg2)
        _c = (_a << _b) | (_a >> (self.byte_length*8 - _b))
        self.set_target(arg1, _c & self.byte_mask)
      #----------------------------------------------------------------
      # BRC
      case 0xB:
        cond = 0 
        cond += (self.carry_flag and arg1 == 0)
        cond += (self.reg_r0 == 0 and arg1 == 1)
        cond += ((not self.carry_flag) and arg1 == 2)
        cond += (self.reg_r0 != 0 and arg1 == 3)
        if(cond > 0):
          if(arg2 == 0x0):
            offset = self.read_memory(self.reg_pc)
            offset =  offset - 256 if offset > 127 else offset
            self.advence_pc()
          else:
            self.reg_pc = self.get_register(arg2) & self.byte_mask
        else:
          if(arg2 == 0x0):
            self.advence_pc()
      #----------------------------------------------------------------
      # PSH
      case 0xC:
        self.stack.append(self.get_register(arg1))
      #----------------------------------------------------------------
      # POP
      case 0xD:
        if(len(self.stack) > 0):
          self.set_target(arg1, self.stack.pop())
        else:
          self.set_target(arg1, 0x00)
      #----------------------------------------------------------------
      # IN
      case 0xE:
        self.set_target(arg1, self.get_port(arg2))
      #---------------------------------------------------------------- 
      # OUT
      case 0xF:
        if(arg2 == 0x0):
          self.push_port(arg1, self.read_memory(self.reg_pc))
          self.advence_pc()
        else:
          self.set_port(arg1, self.get_register(arg2))
      #----------------------------------------------------------------
      # Invalid instruction
      case _:
        print(f"Error: Invalid instruction {instruction} at address {self.reg_pc-1}")
        sys.exit(1)


if( __name__ == "__main__"):
  mm4 = MINMAX4("../Assembler/Examples/Hello_World_db")
  # Print content of the ROM
  for i in range(0, mm4.byte_mask):
    mm4.ROM.seek(i)
    byte = mm4.ROM.read(1)
    if byte == b'':
      break
    print(f"Address: {i:04X}, Value: {byte[0]:02X}")
  while not mm4.halt:
    mm4.tick()
    #print(f"PC: {mm4.reg_pc:04X}, R0: {mm4.reg_r0:04X}, R1: {mm4.reg_r1:04X}, R2: {mm4.reg_r2:04X}, CF: {mm4.carry_flag}")
    if(mm4.port_A_update):
      print(f"Port A: {mm4.port_A}, {chr(mm4.port_A)}")
    #input("Press Enter to continue...")
  mm4.ROM.close()
  os.remove("./rom.bin")
