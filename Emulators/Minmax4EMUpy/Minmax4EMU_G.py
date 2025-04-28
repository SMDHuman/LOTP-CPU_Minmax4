from Minmax4EMU import MINMAX4
import customtkinter as tk
from tkinter.filedialog import askopenfilename
from CTkTable import *  
import os, sys
import keyboard

SQUARE = '█'
CIRCLE = '⚫'
CIRCLE_OUTLINE = '◯'
UP =    '▲'
RIGHT = '►'
DOWN =  '▼'
LEFT =  '◄'

class Register_Frame(tk.CTkFrame):
  #...
  def __init__(self, master, name:str, max_value = -1, **kwargs):
    super().__init__(master, **kwargs)
    self.max_value = max_value # -1 means no limit
    self.name = name
    self.master = master
    self.value_entered = None
    self.indicator_color = 0
    self.old_value = 0
    self.current_filename = None
    self.reg_label = tk.CTkLabel(self, text=self.name)
    self.reg_label.grid(row=0, column=0, padx=5, pady=5)
    self.reg_indicator = tk.CTkLabel(self, text=CIRCLE, text_color="black")
    self.reg_indicator.grid(row=0, column=1, padx=5, pady=5)
    self.reg_entry = tk.CTkEntry(self, width = 50)
    self.reg_entry.grid(row=1, column=0, padx=5, pady=5, columnspan = 2, sticky="ew")
    self.reg_entry.insert(0, "0")
    self.reg_entry.bind("<Return>", self.register_entry_handler)
  #...
  def register_entry_handler(self, event):
    # Check if the entry is empty or not a number
    if(self.reg_entry.get().isnumeric() == False):
      self.update_register(0)
    else:
      self.update_register(int(self.reg_entry.get()))
  #...
  def update_register(self, value:int):
    """
    This function is called to update the register value in the entry.
    It also updates the indicator to show if the register is being used or not.
    """
    if(self.max_value < value and self.max_value != -1):
      value = self.max_value
    if(value < 0):
      value = 0
    #...
    readonly = (self.reg_entry.cget("state") == "readonly")
    if(readonly):
      self.reg_entry.configure(state="normal")
    #...
    self.reg_entry.delete(0, tk.END)
    self.reg_entry.insert(0, str(value))
    #...
    if(value != self.old_value):
      self.update_indicator(100)
    self.old_value = value
    #...
    if(readonly):
      self.reg_entry.configure(state="readonly")
    #...
    if(self.value_entered != None):
      self.value_entered(self)

  #...
  def update_indicator(self, value:int = -1):
    """
    This function is called to update the indicator color.
    It also updates the register value in the entry.
    """
    if(value > 0):
      self.indicator_color = value
    else:
      self.indicator_color -= 5
      if(self.indicator_color < 0):
        self.indicator_color = 0

    if(self.indicator_color > 0):
      self.master.after(100, self.update_indicator)

    self.reg_indicator.configure(text=CIRCLE, text_color=f"gray{self.indicator_color}")
  

  
class Minmax4EMU_G(tk.CTk):
  """
  Minmax4_G is a GUI application for Minmax4 CPU Emulator
  It allows you to see regsiters, memory, and other information in a more user-friendly way.
  And it also provides some input and output methods for the cpu.
  """
  def __init__(self, cpu: MINMAX4):
    super().__init__()
    self.title("Minmax4 Emulator GUI")
    self.geometry("1200x600")
    self.cpu = cpu
    self.cpu_running = False
    self.cpu_speed = 1
    self.last_selected = [0, 0]
    # -------------------------------------------------------------------------
    self.grid_rowconfigure(0, weight=1)
    self.grid_rowconfigure(1, weight=0)
    self.grid_columnconfigure(0, weight=0)
    self.grid_columnconfigure(1, weight=1)
    self.grid_columnconfigure(2, weight=0)
    # Create the main frames
    self.io_frame = tk.CTkFrame(self)
    self.control_frame = tk.CTkFrame(self)
    self.register_frame = tk.CTkFrame(self)
    self.memory_frame = tk.CTkScrollableFrame(self, width=250)

    self.control_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
    self.io_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
    self.memory_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
    self.register_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew", columnspan=3)
    
    # -------------------------------------------------------------------------
    # Setup Registers 
    self.pc_reg_frame = Register_Frame(self.register_frame, "Program Counter", self.cpu.byte_mask)
    self.r0_reg_frame = Register_Frame(self.register_frame, "R0", self.cpu.byte_mask)
    self.r1_reg_frame = Register_Frame(self.register_frame, "R1", self.cpu.byte_mask)
    self.r2_reg_frame = Register_Frame(self.register_frame, "R2", self.cpu.byte_mask)
    self.sc_reg_frame = Register_Frame(self.register_frame, "Stack Counter", self.cpu.byte_mask)
    self.sc_reg_frame.reg_entry.configure(state="readonly")

    self.pc_reg_frame.value_entered = self.handle_register_entry
    self.r0_reg_frame.value_entered = self.handle_register_entry
    self.r1_reg_frame.value_entered = self.handle_register_entry
    self.r2_reg_frame.value_entered = self.handle_register_entry
    self.sc_reg_frame.value_entered = self.handle_register_entry

    self.pc_reg_frame.pack(side=tk.LEFT, padx=5, pady=5)
    self.r0_reg_frame.pack(side=tk.LEFT, padx=5, pady=5)
    self.r1_reg_frame.pack(side=tk.LEFT, padx=5, pady=5)
    self.r2_reg_frame.pack(side=tk.LEFT, padx=5, pady=5)
    self.sc_reg_frame.pack(side=tk.LEFT, padx=5, pady=5)

    # -------------------------------------------------------------------------
    # Setup Control Buttons
    self.run_button = tk.CTkButton(self.control_frame, text="Run", width=50, command=self.run_button_handler)
    self.run_speed = tk.CTkComboBox(self.control_frame, width=100,
                                    values=["1Hz", "4Hz", "16Hz", "256Hz", "FULL"],
                                    command=self.handle_cpu_speed)
    self.step_button = tk.CTkButton(self.control_frame, text="Step", command=self.step_cpu)
    self.reset_button = tk.CTkButton(self.control_frame, text="Reset", command=self.handle_cpu_reset)
    self.load_button = tk.CTkButton(self.control_frame, text="Load Program", command=self.load_handler)
    self.reload_button = tk.CTkButton(self.control_frame, text="Reload Program", command=self.reload_handler)

    self.run_button.grid(row=0, column=0, padx=5, pady=5)
    self.run_speed.grid(row=0, column=1, padx=5, pady=5)
    self.step_button.grid(row=1, column=0, padx=5, pady=5, columnspan = 2, sticky="ew")
    self.reset_button.grid(row=2, column=0, padx=5, pady=5, columnspan = 2, sticky="ew")
    self.load_button.grid(row=3, column=0, padx=5, pady=5, columnspan = 2, sticky="ew")
    self.reload_button.grid(row=4, column=0, padx=5, pady=5, columnspan = 2, sticky="ew")
    # -------------------------------------------------------------------------
    # Setup memory frame
    self.memory_table_row = 32
    self.memory_table = CTkTable(self.memory_frame, row = self.memory_table_row+1, column = 5)
    self.memory_select = tk.CTkSegmentedButton(self.memory_frame,
                                                values=["Program", "Stack"],
                                                command=self.update_memory_table)
    self.memory_select.set("Program")
    for i in range(self.memory_table_row):
      self.memory_table.edit(i+1, 0, text = f"{i*4:02x}:", text_color = "gray", font=("Arial", 14, "bold"))
    

    self.memory_select.pack(pady=5, padx=5, fill=tk.X)
    self.memory_table.pack()
    #-------------------------------------------------------------------------
    # Setup IO frame
    self.io_frame.grid_rowconfigure(0, weight=0)
    self.io_frame.grid_rowconfigure(1, weight=0)
    self.io_frame.grid_rowconfigure(2, weight=1)
    self.io_frame.grid_columnconfigure(0, weight=0)
    self.io_frame.grid_columnconfigure(1, weight=1)
    self.io_frame.grid_columnconfigure(2, weight=1)

    # Port A, B, C, D
    self.port_frame = tk.CTkFrame(self.io_frame)

    self.port_A_frame = Register_Frame(self.port_frame, "Port A", self.cpu.byte_mask)
    self.port_B_frame = Register_Frame(self.port_frame, "Port B", self.cpu.byte_mask)
    self.port_C_frame = Register_Frame(self.port_frame, "Port C", self.cpu.byte_mask)
    self.port_D_frame = Register_Frame(self.port_frame, "Port D", self.cpu.byte_mask)

    self.port_frames = {"Port A": self.port_A_frame,
                        "Port B": self.port_B_frame,
                        "Port C": self.port_C_frame,
                        "Port D": self.port_D_frame}

    self.port_A_frame.value_entered = self.handle_register_entry
    self.port_B_frame.value_entered = self.handle_register_entry
    self.port_C_frame.value_entered = self.handle_register_entry
    self.port_D_frame.value_entered = self.handle_register_entry

    self.port_A_frame.pack(side=tk.LEFT, padx=5, pady=5)
    self.port_B_frame.pack(side=tk.LEFT, padx=5, pady=5)
    self.port_C_frame.pack(side=tk.LEFT, padx=5, pady=5)
    self.port_D_frame.pack(side=tk.LEFT, padx=5, pady=5)

    
    # Port Log
    self.port_log_textbox = tk.CTkTextbox(self.io_frame, width=150)
    self.port_log_textbox.insert(tk.END, "---- Console Log ----\n")

    # Matrix Output
    self.matrix_buffer = [0]*16*16
    self.matrix_frame = tk.CTkFrame(self.io_frame)
    self.matrix_label = tk.CTkLabel(self.matrix_frame, text="", text_color="black")
    self.matrix_label.pack(side=tk.LEFT, padx=5, pady=5)
    self.matrix_info_frame = tk.CTkFrame(self.matrix_frame)
    self.matrix_port_select = tk.CTkOptionMenu(self.matrix_info_frame,
                                                values=["Port A", "Port B", "Port C", "Port D"],
                                                command=self.update_matrix)
    self.matrix_port_select.set("Port A")
    self.matrix_X_label = tk.CTkLabel(self.matrix_info_frame, text="Cursor X: \n0")
    self.matrix_Y_label = tk.CTkLabel(self.matrix_info_frame, text="Cursor Y: \n0")

    self.matrix_clear_button = tk.CTkButton(self.matrix_info_frame, text="Clear", command= self.clear_matrix)

    self.matrix_port_select.pack(side=tk.TOP, padx=5, pady=5)
    self.matrix_X_label.pack(side= tk.TOP, padx=5)
    self.matrix_Y_label.pack(side= tk.TOP, padx=5)
    self.matrix_clear_button.pack(side=tk.TOP, padx=5, pady=5)
    self.matrix_info_frame.pack(side=tk.RIGHT, padx=5, pady=5, fill=tk.BOTH)

    self.update_matrix()

    # Controller input with arrow keys
    self.controller_frame = tk.CTkFrame(self.io_frame)
    for i in range(3):
      self.controller_frame.grid_rowconfigure(i, weight=1)
      self.controller_frame.grid_columnconfigure(i, weight=1)

    self.controller_keypad = CTkTable(self.controller_frame, row=3, column=3, width=30, height=30)
    self.controller_keypad.edit(0, 1, text=UP, text_color="gray", font=("Arial", 14, "bold"))
    self.controller_keypad.edit(1, 0, text=LEFT, text_color="gray", font=("Arial", 14, "bold"))
    self.controller_keypad.edit(1, 2, text=RIGHT, text_color="gray", font=("Arial", 14, "bold"))
    self.controller_keypad.edit(2, 1, text=DOWN, text_color="gray", font=("Arial", 14, "bold"))

    self.controller_keypad.grid(row=0, column=0, padx=5, pady=5, columnspan=3, rowspan=3)


    self.controller_port_select = tk.CTkOptionMenu(self.controller_frame,
                                                values=["Port A", "Port B", "Port C", "Port D"],
                                                width=50)
    self.controller_port_select.set("Port B")
    self.controller_uplow_select = tk.CTkSegmentedButton(self.controller_frame,
                                                values=["Higher", "Lower"])
    self.controller_uplow_select.set("Lower")
    self.controller_uplow_select.grid(row=2, column=3, padx=5, pady=5, sticky="ew")
    self.controller_port_select.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

    # Place the io frames in grid
    self.port_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew", columnspan=2)
    self.port_log_textbox.grid(row=0, column=2, padx=5, pady=5, sticky="nsew", rowspan=3)
    self.matrix_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew", columnspan=2)
    self.controller_frame.grid(row=2, column=0, padx=5, pady=5)

    # Update Things
    self.update_memory_table()
    self.update_memory_table_highlight()
    self.after(100, self.check_keyboard)

  #----------------------------------------------------------------------------
  def reload_handler(self):
    if(self.current_filename != None):
      self.cpu.load_file(self.current_filename)
      self.port_log_textbox.insert(tk.END, "Reloading...\n")
      self.port_log_textbox.see(tk.END)
      self.update_memory_table()
  #----------------------------------------------------------------------------
  def load_handler(self):
    # Open a file dialog to select a file
    self.current_filename = askopenfilename(initialdir=os.getcwd(), title="Select binary file")
    Error = self.cpu.load_file(self.current_filename)
    if(Error != None):
      self.port_log_textbox.insert(tk.END, f"{Error}\n")
      self.current_filename = None
    self.update_memory_table()
  #----------------------------------------------------------------------------
  def check_keyboard(self):
    # Check if the arrow keys are pressed
    up = keyboard.is_pressed("up")
    down = keyboard.is_pressed("down")
    left = keyboard.is_pressed("left")
    right = keyboard.is_pressed("right")
    # Update the table based on the arrow keys pressed
    if(up): self.controller_keypad.select(0, 1)
    else: self.controller_keypad.deselect(0, 1)
    if(down): self.controller_keypad.select(2, 1)
    else: self.controller_keypad.deselect(2, 1)
    if(left): self.controller_keypad.select(1, 0)
    else: self.controller_keypad.deselect(1, 0)
    if(right): self.controller_keypad.select(1, 2)
    else: self.controller_keypad.deselect(1, 2)
    #...
    value = self.port_frames[self.controller_port_select.get()].old_value
    if(self.controller_uplow_select.get() == "Higher"):
      value = value & 0x0F
      value = up<<4 | down<<5 | left<<6 | right<<7
    else:
      value = value & 0xF0
      value = up<<0 | down<<1 | left<<2 | right<<3
    self.port_frames[self.controller_port_select.get()].update_register(value)
    #...
    self.after(100, self.check_keyboard)
  #----------------------------------------------------------------------------
  def clear_matrix(self):
    # Clear the matrix buffer
    for i in range(16*16):
      self.matrix_buffer[i] = 0
    # Update the matrix display
    self.matrix_label.configure(text="")
    self.update_matrix()
  #----------------------------------------------------------------------------
  def update_matrix(self, event = None):
    # Get the selected port
    port = self.matrix_port_select.get()
    if(port == "Port A"):
      value = self.cpu.port_A
      value_update = self.cpu.port_A_update
    elif(port == "Port B"):
      value = self.cpu.port_B
      value_update = self.cpu.port_B_update
    elif(port == "Port C"):
      value = self.cpu.port_C
      value_update = self.cpu.port_C_update
    elif(port == "Port D"):
      value = self.cpu.port_D
      value_update = self.cpu.port_D_update
    # Update the matrix buffer
    x = value & 0x0F
    y = (value >> 4) & 0x0F
    if(value_update):
      self.matrix_buffer[y*16+x] = not self.matrix_buffer[y*16+x]
    
    # Update the matrix display
    self.matrix_X_label.configure(text=f"Cursor X: \n{x}")
    self.matrix_Y_label.configure(text=f"Cursor Y: \n{y}")
    matrix_text = ""
    for i in range(16*16):
      if(self.matrix_buffer[i]):
        matrix_text += CIRCLE
      else:
        matrix_text += CIRCLE_OUTLINE
      if((i+1) % 16 == 0):
        matrix_text += "\n"
    self.matrix_label.configure(text=matrix_text)

  #----------------------------------------------------------------------------
  def run_button_handler(self):
    self.cpu_running = not self.cpu_running
    if(self.cpu_running):
      self.run_button.configure(text="Pause")
      self.step_cpu()
    else:
      self.run_button.configure(text="Run")
  #----------------------------------------------------------------------------
  def step_cpu(self):
    for i in range([1, 50][self.cpu_speed <= 0]):
      self.cpu.tick()
      if(self.cpu.halt):
        self.cpu_running = False
        self.port_log_textbox.insert(tk.END, "CPU Halted\n")
        self.port_log_textbox.see(tk.END)
        self.run_button.configure(text="Run")
        break
      self.update_matrix()
      self.update_registers()
    #self.update_memory_table()
    if(self.cpu_running):
      if(self.cpu_speed > 0):
        delay = int(1000/self.cpu_speed)
      else:
        delay = 100
      self.after(delay, self.step_cpu)
  #----------------------------------------------------------------------------
  # Handle Memory Table Highlight
  def update_memory_table_highlight(self):
    self.memory_table.deselect(self.last_selected[0], self.last_selected[1])
    if(self.memory_select.get() == "Program"):
      size = self.memory_table.size()
      if(self.cpu.reg_pc >= 0 and self.cpu.reg_pc < (size[0]-1)*(size[1]-1)):
        row = self.cpu.reg_pc // (size[0]-1)
        col = self.cpu.reg_pc % (size[0]-1)
        self.memory_table.select(row+1, col+1)
        self.last_selected = [row+1, col+1]
      
  #----------------------------------------------------------------------------
  # Handle CPU Reset
  def handle_cpu_reset(self):
    self.cpu_running = False
    self.run_button.configure(text="Run")
    self.port_log_textbox.insert(tk.END, "----------------------\n")
    self.port_log_textbox.insert(tk.END, "CPU Reseting...\n")
    self.port_log_textbox.insert(tk.END, "----------------------\n")
    self.port_log_textbox.see(tk.END)
    self.port_A_frame.update_register(0)
    self.port_B_frame.update_register(0)
    self.port_C_frame.update_register(0)
    self.port_D_frame.update_register(0)
    self.after(1000, self.cpu.reset)
    self.after(1005, self.update_registers)

  #----------------------------------------------------------------------------
  def handle_cpu_speed(self, event = None):
    if(self.run_speed.get() == "FULL"):
      self.cpu_speed = 0
    elif("HZ" in self.run_speed.get().upper()):
      self.cpu_speed = int(self.run_speed.get().upper().replace("HZ", ""))
    else:
      self.cpu_speed = int(self.run_speed.get())
  #----------------------------------------------------------------------------
  def update_memory_table(self, event = None):
    """
    This function is called to update the memory table in the GUI.
    """
    #...
    table = self.memory_table.get()
    #...
    if(self.memory_select.get() == "Program"):
      for i in range(1, len(table)):
        for j in range(1, len(table[i])):
          self.memory_table.edit(i, j, text = hex(self.cpu.read_memory((i-1)*(len(table[i])-1)+(j-1)))[1:], font = ("Arial", 11))
    elif(self.memory_select.get() == "Stack"):
      for i in range(1, len(table)):
        for j in range(1, len(table[i])):
          indx = (i-1)*(len(table[i])-1)+(j-1)
          if(indx >= len(self.cpu.stack)):
            val = hex(0)[1:]
          else:
            val = hex(self.cpu.stack[indx])[1:]
          self.memory_table.edit(i, j, text = val)
  #----------------------------------------------------------------------------
  #...
  def handle_register_entry(self, frame: Register_Frame):
    if(frame == self.pc_reg_frame):
      self.cpu.reg_pc = frame.old_value
    elif(frame == self.r0_reg_frame):
      self.cpu.reg_r0 = frame.old_value
    elif(frame == self.r1_reg_frame):
      self.cpu.reg_r1 = frame.old_value
    elif(frame == self.r2_reg_frame):
      self.cpu.reg_r2 = frame.old_value
    elif(frame == self.sc_reg_frame):
      self.cpu.stack_counter = frame.old_value
    elif(frame == self.port_A_frame):
      self.cpu.port_A = frame.old_value
    elif(frame == self.port_B_frame):
      self.cpu.port_B = frame.old_value
    elif(frame == self.port_C_frame):
      self.cpu.port_C = frame.old_value
    elif(frame == self.port_D_frame):
      self.cpu.port_D = frame.old_value
  #----------------------------------------------------------------------------
  #...
  def update_registers(self):
    """
    This function is called to update the registers in the GUI.
    It also updates the memory and other information.
    """
    self.pc_reg_frame.update_register(self.cpu.reg_pc)
    self.update_memory_table_highlight()
    self.r0_reg_frame.update_register(self.cpu.reg_r0)
    self.r1_reg_frame.update_register(self.cpu.reg_r1)
    self.r2_reg_frame.update_register(self.cpu.reg_r2)
    self.sc_reg_frame.update_register(len(self.cpu.stack))

    if(self.cpu.port_A_update):
      self.port_A_frame.update_register(self.cpu.port_A)
      self.port_log_textbox.insert(tk.END, f"Port A: {self.cpu.port_A}, {hex(self.cpu.port_A)}, '{chr(self.cpu.port_A)}'\n")
    if(self.cpu.port_B_update):
      self.port_B_frame.update_register(self.cpu.port_B)
      self.port_log_textbox.insert(tk.END, f"Port B: {self.cpu.port_B}, {hex(self.cpu.port_B)}, '{chr(self.cpu.port_B)}'\n")
    if(self.cpu.port_C_update):
      self.port_C_frame.update_register(self.cpu.port_C)
      self.port_log_textbox.insert(tk.END, f"Port C: {self.cpu.port_C}, {hex(self.cpu.port_C)}, '{chr(self.cpu.port_C)}'\n")
    if(self.cpu.port_D_update):
      self.port_D_frame.update_register(self.cpu.port_D)
      self.port_log_textbox.insert(tk.END, f"Port D: {self.cpu.port_D}, {hex(self.cpu.port_D)}, '{chr(self.cpu.port_D)}'\n")
    self.port_log_textbox.see(tk.END)
  #----------------------------------------------------------------------------

if(__name__ == "__main__"):
  cpu = MINMAX4()
  app = Minmax4EMU_G(cpu)
  app.mainloop()