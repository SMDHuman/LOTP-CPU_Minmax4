import sys, os
import argparse

class MINMAX4():
  def __init__(self, input_file: str = None, register_size: int = 1):
    self.ROM: dict = {}
    self.register_size = register_size
    self.register_mask = (1 << (self.register_size * 8)) - 1
    self.output_cb: callable = None
    #...
    self.reset()
    if(input_file):
      self.load_file(input_file)

  def load_file(self, input_file: str) -> str|None:
    self.reset()
    #...
    if not os.path.isfile(input_file):
      return(f"Error: File '{input_file}' not found.")
    #...
    magic = "MNMX"
    version = 0x04
    self.register_size = 0
    self.ROM.clear()
    with open(input_file, 'rb') as f:
      header = f.read(6)
      if header[:4] != magic.encode():
        return(f"Error: Invalid file format. Expected '{magic}', got '{header.decode()}'")
      if header[4] != version:
        return(f"Error: Unsupported version. Expected {version}, got {header[4]}")
      self.register_size = header[5]
      if self.register_size < 1:
        return(f"Error: Invalid byte length. Expected at least 1, got {self.register_size}")
    
      # Read the rest of the file and process it
      for i, data in enumerate(f.read()):
        self.ROM[i] = data

  def load_bytes(self, bytes_data: bytes):
    self.reset()
    self.ROM.clear()
    for i, data in enumerate(bytes_data):
      self.ROM[i] = data

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
    self.port_A_update = False
    self.port_B_update = False
    self.port_C_update = False
    self.port_D_update = False
    self.stack = []

  def set_target(self, target, value):
    if target == 0:
      self.reg_pc = value & self.register_mask
    elif target == 1:
      self.reg_r0 = value & self.register_mask
    elif target == 2:
      self.reg_r1 = value & self.register_mask
    elif target == 3:
      self.reg_r2 = value & self.register_mask

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
      self.port_A = value & self.register_mask
      self.port_A_update = True
      self.output_cb(0, self.port_A)
    elif port == 1:
      self.port_B = value & self.register_mask
      self.port_B_update = True
      self.output_cb(1, self.port_B)
    elif port == 2:
      self.port_C = value & self.register_mask
      self.port_C_update = True
      self.output_cb(2, self.port_C)
    elif port == 3:
      self.port_D = value & self.register_mask
      self.port_D_update = True
      self.output_cb(3, self.port_D)

  def set_output_callback(self, callback: callable):
    self.output_cb = callback
  
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
    if address < 0 or address > self.register_mask:
      raise ValueError("Address out of range")
    elif(address not in self.ROM):
      return(0x00)
    else:
      return self.ROM[address]
  
  def write_memory(self, address, value):
    if address < 0 or address >= self.register_mask:
      raise ValueError("Address out of range")
    self.ROM[address] = bytes([value & 0xFF])
  
  def advence_pc(self, offset = 1):
    if(offset + self.reg_pc > self.register_mask):
      self.halt = True
    else:
      self.reg_pc = (self.reg_pc + offset) & self.register_mask

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
          self.set_target(arg1, self.read_memory(self.reg_pc))
          self.advence_pc()
        else:
          self.set_target(arg1, self.get_register(arg2))
      #---------------------------------------------------------------
      # LOD
      case 0x2:
        _offset = self.get_register(arg2)
        _adrs = self.read_memory(self.reg_pc)
        self.set_target(arg1, self.read_memory(_offset + _adrs))
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
        if(_c > self.register_mask):
          self.carry_flag = True
        else:
          self.carry_flag = False
        self.set_target(arg1, _c & self.register_mask)
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
          _c = self.register_mask + _c + 1
          self.carry_flag = True
        else:
          self.carry_flag = False
        self.set_target(arg1, _c & self.register_mask)
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
        self.set_target(arg1, _c & self.register_mask)
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
        self.set_target(arg1, _c & self.register_mask)
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
        self.set_target(arg1, _c & self.register_mask)
      #----------------------------------------------------------------
      # INV
      case 0x9:
        _a = self.get_register(arg1)
        _c = ~_a
        self.set_target(arg1, _c & self.register_mask)
      #----------------------------------------------------------------
      # ROT
      case 0xA:
        _a = self.get_register(arg1)
        if(arg2 == 0x0):
          _b = self.read_memory(self.reg_pc)
          self.advence_pc()
        else:
          _b = self.get_register(arg2)
        _c = (_a << _b) | (_a >> (self.register_size*8 - _b))
        self.set_target(arg1, _c & self.register_mask)
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
            self.reg_pc = self.get_register(arg2) & self.register_mask
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
          self.set_port(arg1, self.read_memory(self.reg_pc))
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
  while not mm4.halt:
    mm4.tick()
    #print(f"PC: {mm4.reg_pc:04X}, R0: {mm4.reg_r0:04X}, R1: {mm4.reg_r1:04X}, R2: {mm4.reg_r2:04X}, CF: {mm4.carry_flag}")
    if(mm4.port_A_update):
      print(f"Port A: {mm4.port_A}, {chr(mm4.port_A)}")
    #input("Press Enter to continue...")
