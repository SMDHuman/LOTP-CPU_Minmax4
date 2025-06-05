import sys, os
import argparse

class MINMAX4():
  def __init__(self, input_file: str = None, register_size: int = 1):
    self.ROM: dict = {}
    self.register_mask = 255
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
    version = 0x45
    self.register_size = 0
    self.ROM.clear()
    with open(input_file, 'rb') as f:
      header = f.read(5)
      if header[:4] != magic.encode():
        return(f"Error: Invalid file format. Expected '{magic}', got '{header.decode()}'")
      if header[4] != version:
        return(f"Error: Unsupported version. Expected {version}, got {header[4]}")
    
      # Read the rest of the file and process it
      for i, data in enumerate(f.read()):
        self.ROM[i] = data

  def load_bytes(self, bytes_data: bytes):
    self.reset()
    self.ROM.clear()
    for i, data in enumerate(bytes_data):
      self.ROM[i] = data

  def reset(self):
    self.pc = 0x0000
    self.sp = 0x00
    self.r0 = 0x00
    self.r1 = 0x00
    self.x = 0x00
    self.y = 0x00
    self.carry_flag = False
    self.overflow_flag = False
    self.halt_flag = False
    self.A = 0x00
    self.B = 0x00
    self.C = 0x00
    self.D = 0x00
    self.A_update = False
    self.B_update = False
    self.C_update = False
    self.D_update = False

    for i in range(255):
      self.ROM[ 0xff00 | i] = 0x00

  def set_target(self, target, value):
    if target == 0:
      self.r0 = value & self.register_mask
    elif target == 1:
      self.r1 = value & self.register_mask
    elif target == 2:
      self.x = value & self.register_mask
    elif target == 3:
      self.y = value & self.register_mask

  def get_register(self, reg):
    if reg == 0:
      return self.r0
    elif reg == 1:
      return self.r1
    elif reg == 2:
      return self.x
    elif reg == 3:
      return self.y
    
  def set_port(self, port, value):
    if port == 0:
      self.A = value & self.register_mask
      self.A_update = True
      if(self.output_cb):
        self.output_cb(0, self.A)
    elif port == 1:
      self.B = value & self.register_mask
      self.B_update = True
      if(self.output_cb):
        self.output_cb(1, self.B)
    elif port == 2:
      self.C = value & self.register_mask
      self.C_update = True
      if(self.output_cb):
        self.output_cb(2, self.C)
    elif port == 3:
      self.D = value & self.register_mask
      self.D_update = True
      if(self.output_cb):
        self.output_cb(3, self.D)

  def set_output_callback(self, callback: callable):
    self.output_cb = callback
  
  def get_port(self, port):
    if port == 0:
      return self.A
    elif port == 1:
      return self.B
    elif port == 2:
      return self.C
    elif port == 3:
      return self.D
    
  def read_memory(self, address) -> int:
    if address < 0 or address > 0xffff:
      raise ValueError("Address out of range")
    elif(address not in self.ROM):
      return(0x00)
    else:
      return self.ROM[address]
  
  def write_memory(self, address, value):
    if address < 0 or address > 0xffff:
      raise ValueError("Address out of range")
    self.ROM[address] = value & 0xFF
  
  def advence_pc(self, offset = 1):
    self.pc = (self.pc + offset) & 0xffff

  def get_arg_b(self, arg, default = 0x00):
    if(arg == 0x2):
      self.advence_pc()
      return self.read_memory(self.pc-1)
    elif(arg == 0x3):
      return default
    else:
      return self.get_register(arg)

  def tick(self):
    if(self.halt_flag): return 0
    #...
    self.A_update = False
    self.B_update = False
    self.C_update = False
    self.D_update = False
    #...
    instruction = self.read_memory(self.pc) & 0x0F
    arg1, arg2 = (self.read_memory(self.pc) & 0x30) >> 4, (self.read_memory(self.pc) & 0xC0) >> 6
    print(f"PC: {self.pc:04X}, Instruction: {instruction:02X}, Args: {arg1:02X}, {arg2:02X}")
    self.advence_pc()
    #...
    match instruction:
      #---------------------------------------------------------------
      # HLT
      case 0x0: 
        self.halt_flag = True
      #---------------------------------------------------------------
      # MOV
      case 0x1:
        if(arg2 == 0x2):
          self.set_target(arg1, self.read_memory(self.pc))
          self.advence_pc()
        elif(arg2 == 0x3):
          self.set_target(arg1, 0)
        else:
          self.set_target(arg1, self.get_arg_b(arg2))
      #---------------------------------------------------------------
      # LOD
      case 0x2:
        _offset = self.get_arg_b(arg2)
        _adrs = (self.y << 8) | self.x
        self.set_target(arg1, self.read_memory(_offset + _adrs))
      #---------------------------------------------------------------
      # STR
      case 0x3:
        _offset = self.get_arg_b(arg2)
        _adrs = (self.y << 8) | self.x
        self.write_memory(_offset + _adrs, self.get_register(arg1) & 0xFF)
      #---------------------------------------------------------------
      # ADD
      case 0x4:
        _a = self.get_register(arg1)
        _b = self.get_arg_b(arg2, 1)
        _c = _a + _b
        # Check for carry
        if(_c > self.register_mask):
          self.carry_flag = True
        else:
          self.carry_flag = False
        # Check for overflow
        if( ((_a&0x80) & (_b&0x80) & (not _c&0x80))
           or ((not _a&0x80) & (not _b&0x80) & (_c&0x80))):
          self.overflow_flag = True
        else:
          self.overflow_flag = False
        self.set_target(arg1, _c & self.register_mask)
      #----------------------------------------------------------------
      # SUB
      case 0x5:
        _a = self.get_register(arg1)
        _b = self.get_arg_b(arg2, 1)
        _c = _a - _b
        # Check for carry
        if(_c > self.register_mask):
          self.carry_flag = True
        else:
          self.carry_flag = False
        # Check for overflow
        if( ((_a&0x80) & (_b&0x80) & (not _c&0x80))
           or ((not _a&0x80) & (not _b&0x80) & (_c&0x80))):
          self.overflow_flag = True
        else:
          self.overflow_flag = False
        self.set_target(arg1, _c & self.register_mask)
      #----------------------------------------------------------------
      # AND
      case 0x6:
        _a = self.get_register(arg1)
        _b = self.get_arg_b(arg2, 128)
        _c = _a & _b
        self.set_target(arg1, _c & self.register_mask)
      #----------------------------------------------------------------
      # OR
      case 0x7:
        _a = self.get_register(arg1)
        _b = self.get_arg_b(arg2)
        _c = _a | _b
        self.set_target(arg1, _c & self.register_mask)
      #----------------------------------------------------------------
      # XOR
      case 0x8:
        _a = self.get_register(arg1)
        _b = self.get_arg_b(arg2, 255)
        _c = _a ^ _b
        self.set_target(arg1, _c & self.register_mask)
      #----------------------------------------------------------------
      # ROT
      case 0x9:
        _a = self.get_register(arg1)
        _b = self.get_arg_b(arg2, 1)
        _c = (_a << _b) | (_a >> (self.register_size*8 - _b))
        self.set_target(arg1, _c & self.register_mask)
      #----------------------------------------------------------------
      # JMP
      case 0xA:
        _adrs = (self.y << 8) | self.x
        _offset = self.get_arg_b(arg2, 0)
        self.pc = (_adrs + _offset) & 0xffff
      #----------------------------------------------------------------
      # BRC
      case 0xB:
        cond = 0 
        cond += (self.carry_flag and arg1 == 0)
        cond += (self.overflow_flag and arg1 == 1)
        cond += (self.r0 == 0 and arg1 == 2)
        cond += (self.r0 == 255 and arg1 == 3)
        _offset = self.get_arg_b(arg2, 0)
        if(cond > 0):
          _offset =  _offset - 256 if _offset > 127 else _offset
          self.advence_pc(_offset)
      #----------------------------------------------------------------
      # PSH
      case 0xC:
        self.ROM[0xff00 | self.sp] = self.get_register(arg1) & 0xFF
        self.sp = (self.sp + 1) & 0xff
      #----------------------------------------------------------------
      # POP
      case 0xD:
        self.sp = (self.sp - 1) & 0xff
        self.set_target(arg1, self.ROM[0xff00 | self.sp])
      #----------------------------------------------------------------
      # IN
      case 0xE:
        self.set_target(arg1, self.get_port(arg2))
      #---------------------------------------------------------------- 
      # OUT
      case 0xF:
        self.set_port(arg1, self.get_arg_b(arg2, 0))
      #----------------------------------------------------------------
      # Invalid instruction
      case _:
        print(f"Error: Invalid instruction {instruction} at address {self.pc-1}")
        sys.exit(1)
    return 1

if( __name__ == "__main__"):
  mm4 = MINMAX4(sys.argv[1] if len(sys.argv) > 1 else None)
  while not mm4.halt_flag:
    mm4.tick()
    print(f"PC: {mm4.pc:04X}, R0: {mm4.r0:04X}, R1: {mm4.r1:04X}, R2: {mm4.x:04X}, R3: {mm4.y:04X}, CF: {mm4.carry_flag}, OF: {mm4.overflow_flag}")
    if(mm4.A_update):
      print(f"Port A: {mm4.A}, {chr(mm4.A)}")
    #input("Press Enter to continue...")
