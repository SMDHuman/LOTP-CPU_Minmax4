# -----------------------------------------------------------------------------
# Minmax4 Arcade Emulator
# Using pygame for graphics and input
# -----------------------------------------------------------------------------
# Inputs:
#   PORT A Keyboard: 
#     first 4 bits: down, up, right, left
#     last 4 bits: space, c, x, z
# Outputs:
#  PORT B/C Display:
#   first 4 bits: Colors
#   next 6 bits: X position
#   next 6 bits: Y position
#   First incoming 16 byte of data from PORT B is the color palette
#   with the color format of BBGGGRRR
#  PORT D Speaker:
#   0 : no sound
#   1-127: MIDI Notes (A0 TO G9)
#   128-255: Special sounds
# ----------------------------------------------------------------------------- 
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from Emulators.Minmax4EMUpy import Minmax4EMU
from Assembler.Minmax4ASM import assembler
import pygame as pg
import datetime, time

class Minmax4Arc:
  #----------------------------------------------------------------------------
  # Initialize the emulator
  def __init__(self):
    pg.init()
    self.win = pg.display.set_mode((640, 640))
    self.clock = pg.time.Clock()
    self.running = True

    byte_code = assembler("Programs/Displat_Test.mm4")
    
    print("Size of byte code: ", len(byte_code))
    self.cpu = Minmax4EMU.MINMAX4(register_size = 2)
    self.cpu.load_bytes(byte_code)
    self.cpu.set_output_callback(self.handle_cpu_outputs)

    self.display = pg.Surface((64, 64))
    self.display_lower_input = 0
    self.display_pallet = []
  #----------------------------------------------------------------------------
  # Handle events
  def handle_events(self):
    for event in pg.event.get():
      if event.type == pg.QUIT:
        self.running = False

  #----------------------------------------------------------------------------
  def handle_cpu_outputs(self, port, value):
    # Log the output to the console
    timeinfo = datetime.datetime.now().strftime('%H:%M:%S')
    millis = int(round(time.time() * 1000)) % 1000
    print(f"{timeinfo}.{millis} - Port: {port}, Value: {value}")

    # Handle the output based on the port
    if(port == 1):
      if(len(self.display_pallet) < 16):
        r, g, b = value & 0x7, (value >> 3) & 0x7, (value >> 6) & 0x3
        r = int(r * 255 / 7)
        g = int(g * 255 / 7)
        b = int(b * 255 / 3)
        self.display_pallet.append((r, g, b))
      else:
        self.display_lower_input = value
    elif(port == 2):
      color = self.display_lower_input & 0x0F
      x = ((value & 0x3) << 4) | ((self.display_lower_input & 0xF0) >> 4)
      y = value >> 2
      print(f"X: {x}, Y: {y}, Color: {color}")
      self.display.set_at((x, y), self.display_pallet[color])
      self.win.blit(pg.transform.scale(self.display, self.win.get_size()), (0, 0))    
      pg.display.flip()

  #----------------------------------------------------------------------------
  # Main loop
  def run(self):
    while self.running:
      self.handle_events()
      if(not self.cpu.halt):
        self.cpu.tick()
        #print(self.cpu.reg_pc)
        if(self.cpu.halt):
          print("CPU halted")
      #self.win.fill((0, 0, 0))

        

      self.clock.tick(60)
    pg.quit()

if __name__ == "__main__":
  emulator = Minmax4Arc()
  emulator.run()