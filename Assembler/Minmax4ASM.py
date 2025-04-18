import sys, os
import argparse
import struct
from tokenizer import Tokenizer

def main():
  parser = argparse.ArgumentParser(description='Minmax4ASM - Minmax4 Assembler')
  parser.add_argument('input', type=str, help='Input file path')
  parser.add_argument('output', type=str, help='Output file path')
  parser.add_argument('-b', "--bytes", type=int, help='Length of the data bus in bytes')
  parser.add_argument('-d', "--debug", action='store_true', help='Enable debug mode')
  
  args = parser.parse_args()

  byte_length = args.bytes if args.bytes else 1
  byte_mask = (1 << (byte_length * 8)) - 1

  input_file = args.input
  if not os.path.isfile(input_file):
    print(f"Error: File '{input_file}' not found.")
    sys.exit(1)
  
  # Read the input file
  with open(input_file, 'r') as f:
    input_code = f.read()
    tokens = Tokenizer(input_code)
    if args.debug:
      print("Tokens:")
      for token in tokens:
        print(token)

  magic = "MNMX"
  version = 0x04
  ROM: bytearray = b''
  #-----------------------------------------------------------------------------
  # Assemble the tokens into binary data
  instructions = ["NOP", "MOV", "LOD", "STR", "ADD", "SUB", "AND", "OR", "XOR", "INV", "ROT", "BRC", "PSH", "POP", "IN", "OUT"]
  targets = ["PC", "R0", "R1", "R2"]
  registers = [0, "R0", "R1", "R2"]
  conditions = ["CF", "EZ", "NCF", "NEZ"]
  ports = ["A", "B", "A_DIR", "B_DIR"]

  # Find all branch labels
  branch_later = []
  branch_labels = {}
  for token in tokens:
    if token.type == "BRANCH":
      label = token.word.upper()
      branch_labels[label] = None


  byte_slice = ""
  for token in tokens:
    bits = ""
    if token.type == "BRANCH":
      label = token.word.upper()
      branch_labels[label] = len(ROM)

    if token.type == "WORD":
      word = token.word.upper()
      if word in instructions:
        bits = f"{instructions.index(word):04b}"
      elif word in targets:
        bits = f"{targets.index(word):02b}"
      elif word in registers:
        bits = f"{registers.index(word):02b}"
      elif word in conditions:
        bits = f"{conditions.index(word):02b}"
      elif word in ports:
        bits = f"{ports.index(word):02b}"
      elif word in branch_labels:
        bits = f"{0:08b}"
        branch_later.append((len(ROM), word))

    if token.type == "VALUE":
      value = token.word
      sign_bit = 0
      if(value.startswith("-")):
        sign_bit = 1
      if value.startswith("0x"):
        value = int(value, 16)
      elif value.startswith("0b"):
        value = int(value, 2)
      else:
        value = int(value)
      if sign_bit == 1:
        value = 256 + value
      bits = f"{value:08b}"

    if(len(byte_slice) + len(bits) > 8 or (token.type == "NL" and byte_slice != "")):
      ROM += bytearray([int(byte_slice, 2)])
      byte_slice = bits
    else:
      byte_slice = bits + byte_slice
  
  #-----------------------------------------------------------------------------
  # Replace branch labels with addresses
  for branch in branch_later:
    print(f"Branch: {branch[0]}, Label: {branch[1]}, Address: {branch_labels[branch[1]]}")
    ROM = ROM[:branch[0]+1] + bytearray([branch_labels[branch[1]]]) + ROM[branch[0]+2:]

  if(args.debug):
    print("ROM:")
    for i in range(0, len(ROM), 16):
      print(" ".join(f"{byte:02X}" for byte in ROM[i:i+16]))
  #-----------------------------------------------------------------------------
  # Output file creation
  output_file = args.output
  with open(output_file, 'wb') as f:
    # Write the magic number and version
    f.write(magic.encode())
    f.write(struct.pack('B', version))
    f.write(byte_length.to_bytes(1, byteorder='little'))

    # Write the ROM data
    f.write(ROM)
  
  print(f"Output file '{output_file}' created successfully.")
  

if __name__ == "__main__":
  main()