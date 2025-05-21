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
#  PORT D Speaker:
#   0 : no sound
#   1-127: MIDI Notes (A0 TO G9)
#   128-255: Special sounds
# ----------------------------------------------------------------------------- 
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Minmax4EMUpy import Minmax4EMU

import pygame as pg

class Minmax4Arc:
  #----------------------------------------------------------------------------
  # Initialize the emulator
  def __init__(self):
    pg.init()
    self.win = pg.display.set_mode((640, 480))
    self.clock = pg.time.Clock()
    self.running = True

    self.cpu = Minmax4EMU.MINMAX4()
    self.cpu.set_output_callback(self.handle_cpu_outputs)
  #----------------------------------------------------------------------------
  # Handle events
  def handle_events(self):
    for event in pg.event.get():
      if event.type == pg.QUIT:
        self.running = False

  #----------------------------------------------------------------------------
  def handle_cpu_outputs(self, port, value):
    pass

  #----------------------------------------------------------------------------
  # Main loop
  def run(self):
    while self.running:
      self.handle_events()
      self.cpu.tick()
      #self.win.fill((0, 0, 0))

      #pg.display.flip()
      #self.clock.tick(60)
    pg.quit()

if __name__ == "__main__":
  emulator = Minmax4Arc()
  emulator.run()