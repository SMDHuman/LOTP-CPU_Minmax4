import sys, os
import argparse
import struct
import re
from typing import override

#------------------------------------------------------------------------------
def parse_cmd_arguments() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description='Minmax4ASM - Minmax4 Assembler')
  parser.add_argument('input', type=str, help='Input file path')
  parser.add_argument('output', type=str, help='Output file path', default="-", nargs='?')
  parser.add_argument('-b', "--bytes", type=int, help='Length of the data bus in bytes')
  parser.add_argument('-d', "--debug", action='store_true', help='Enable debug mode')
  
  return(parser.parse_args())
#------------------------------------------------------------------------------
def get_input_code(input_file: str) -> str:
  if not os.path.isfile(input_file):
    print(f"Error: File '{input_file}' not found.")
    sys.exit(1)
  
  with open(input_file, 'r') as f:
    return(f.read())
#------------------------------------------------------------------------------
def output_rom(rom: bytearray, output_file: str) -> None:
  MAGIC = "MNMX"
  VERSION = 0x04
  #...
  if output_file == "-":
    output_file = ".".join(args.input.split(".")[:-1])
  #...
  with open(output_file, 'wb') as f:
    # Write the magic number and version
    f.write(MAGIC.encode())
    f.write(struct.pack('B', VERSION))
    f.write(BYTE_LENGHT.to_bytes(1, byteorder='little'))
    f.write(rom)
  #...
  print(f"Output file '{output_file}' created successfully.")

#------------------------------------------------------------------------------
class Token:
  def __init__(self, line: int, _type: str, word: str):
    self.line: int = line
    self.file: str = ""
    self.type: str = _type
    self.word: str = word

  @override
  def __repr__(self) -> str:
    return(f"{self.file} {self.line} - {self.type}: {str([self.word])[1:-1]}")

#------------------------------------------------------------------------------
def tokenize_code(input_code: str, file_name: str = "main") -> list[Token]:
  input_code += "\n\n"
  tokens: list[Token] = []
  current_token_type: str = "BLANK"
  current_token_char: str = ""
  current_line: int = 1
  in_list: bool = False
  i = 0
  while(i < len(input_code)):
    char: str = input_code[i]
    match current_token_type:
      #-------------------------------
      case "BLANK": # BLANK
        if(char == ";"):
          current_token_type = "COMMENT"
        if(char == "<"):
          tokens.append(Token(current_line, "MACRO_START", "<"))
        if(char == ">"):
          tokens.append(Token(current_line, "MACRO_END", ">"))
        if(char == "#"):
          tokens.append(Token(current_line, "INDEX", "#"))
        if(char == "'"):
          current_token_type = "STRING_SINGLE"
        if(char == '"'):
          current_token_type = "STRING_DOUBLE"
        if(char == "["):
          in_list = True
          tokens.append(Token(current_line, "LIST_START", "["))
        if(char == "]"):
          in_list = False
          tokens.append(Token(current_line, "LIST_END", "]"))
        if(char == "," and not in_list):
          tokens.append(Token(current_line, "SEPARATOR", ","))
        if(char == "="):
          tokens.append(Token(current_line, "ASSIGN", "="))
        if(re.match("[A-Za-z_]", char)):
          current_token_char += char
          current_token_type = "WORD"
        if(re.match("[0-9]", char)):
          current_token_type = "VALUE"
          current_token_char += char
      #-------------------------------
      case "COMMENT":
        if(char == "\n"):
          current_token_type = "BLANK"
      #-------------------------------
      case "WORD":
        if(re.match("[A-Za-z0-9_]", char)):
          current_token_char += char
        elif(char == ":"):
          tokens.append(Token(current_line, "BRANCH", current_token_char))
          current_token_char = ""
          current_token_type = "BLANK"
        else:
          tokens.append(Token(current_line, current_token_type, current_token_char))
          current_token_char = ""
          current_token_type = "BLANK"
          if(char != "\n"):
            i-=1
      #-------------------------------
      case "STRING_SINGLE":
        if(char == "'"):
          tokens.append(Token(current_line, "STRING", current_token_char))
          current_token_char = ""
          current_token_type = "BLANK"
        else:
          current_token_char += char
      #-------------------------------
      case "STRING_DOUBLE":
        if(char == '"'):
          tokens.append(Token(current_line, "STRING", current_token_char))
          current_token_char = ""
          current_token_type = "BLANK"
        else:
          current_token_char += char
      #-------------------------------
      case "VALUE":
        if(re.match("[0-9a-fA-F_bx]", char)):
          current_token_char += char
        else:
          tokens.append(Token(current_line, current_token_type, current_token_char))
          current_token_char = ""
          current_token_type = "BLANK"
          if(char != "\n"):
            i-=1
    #...
    if(char == "\n"):
      current_line += 1
      if(tokens[-1].type != "SEPARATOR"):
        tokens.append(Token(current_line, "SEPARATOR", ","))
    #...
    i += 1
  for token in tokens:
    token.file = file_name
  return(tokens)
#------------------------------------------------------------------------------
def parse_macros(tokens: list[Token]) -> tuple[list[list[Token]], list[Token]]:
  macros = []
  current_macro = []
  new_tokens = []
  macro_start = False
  macro_arg = False
  # Loop through the tokens and find macros
  for i, token in enumerate(tokens):
    if macro_arg:
      if token.type == "MACRO_END":
        macro_arg = False
      else:
        token.type = "MACRO_ARG"
        current_macro.append(token)
    elif macro_start:
      if token.type == "MACRO_START":
        macro_arg = True
      # Include another file in here and tokenize it
      elif(token.type == "STRING"):
        current_path = "\\".join(args.input.split("\\")[:-1]) + "\\"
        code = get_input_code(current_path+token.word)
        include_tokens = tokenize_code(code, token.word)
        include_macros, include_tokens = parse_macros(include_tokens)
        macros += include_macros
        # Add the tokens to the new tokens list
        for i_token in include_tokens:
          new_tokens.append(i_token)
      elif token.type == "MACRO_END":
        macro_start = False
        macros.append(current_macro)
        current_macro = []
      else:
        current_macro.append(token)
    else:
      if token.type == "MACRO_START":
        macro_start = True
      else:
        new_tokens.append(token)
  #---------------------------------------
  # Print the macros for debugging
  if(DEBUG_MODE):
    print("Macros:")
    for macro in macros:
      print(macro)
  #...
  return( macros, new_tokens)

def apply_macros(macros: list[list[Token]], tokens: list[Token]) -> list[Token]:
  #---------------------------------------
  # Add the macros to the new tokens list
  for macro in macros:
    if(len(macro) == 0):
      continue
    if(macro[0].type == "WORD"):
      #...
      if(macro[1].type == "MACRO_ARG"):
        macro_args = {}
        macro_start = -1
        origin_line = 0
        # Find the start of the function macro in the new tokens list
        for i, token in enumerate(tokens):
          if(token.word == macro[0].word):
            macro_start = i
            origin_line = token.line
            for j in range(1, len(macro)):
              if(macro[j].type == "MACRO_ARG"):
                macro_args[macro[j].word] = tokens[i+j]
              else:
                break
        if(macro_start == -1):
          continue
        # Remove the current line before replacement 
        for i in range(len(macro_args) + 1):
          tokens.pop(macro_start)
        # Replace the function macro arguments with the corresponding tokens
        for j in range(len(macro_args) + 1, len(macro)):
          i = j - len(macro_args) - 1
          tokens.insert(macro_start + i, macro[j])
          tokens[macro_start + i].line = origin_line
          if(macro[j].word in macro_args):
            tokens[macro_start + i].type = macro_args[macro[j].word].type
            tokens[macro_start + i].word = macro_args[macro[j].word].word
        
        print(macro_args, macro_start)
      #...
      else:
        for i, token in enumerate(tokens):
          if(token.word == macro[0].word):
            tokens[i].type = macro[1].type
            tokens[i].word = macro[1].word
            for j in range(2, len(macro)):
              tokens.insert(i+j-1, macro[j])
              tokens[i+j-1].line = token.line
  #---------------------------------------
  #...
  return(tokens)

def expect_token_type(token: Token, expected_type) -> bool:
  if(type(expected_type) == str):
    expected_type = [expected_type]
  if(token.type not in expected_type):
    print(f"Error: Expected token type '{expected_type}' but got '{token.type}' at line {token.line}.")
    if(DEBUG_MODE):
      print(f"Token: {token}")
    sys.exit(1)
    return(False)
  return(True)

#------------------------------------------------------------------------------
def generate_bytes(tokens: list[Token]) -> bytearray:
  # Constants
  instructions = {"NOP":0 ,"MOV":1 ,"LOD":2 ,"STR":3 ,"ADD":4 ,"SUB":5 ,"AND":6 ,"OR":7 ,"XOR":8 ,"INV":9 ,"ROT":10 ,"BRC":11 ,"PSH":12 ,"POP":13 ,"IN":14 ,"OUT":15}
  targets = {"PC": 0, "R0": 1, "R1": 2, "R2": 3}
  regs = {"R0": 1, "R1": 2, "R2": 3}
  conds = {"CF": 0, "EZ": 1, "NCF": 2, "NEZ": 3}
  ports = {"A": 0, "B": 1, "C": 2, "D": 3}
  constants = {}
  #...
  def eval(token: Token) -> int:
    if(token.type == "VALUE"):
      return(int(token.word, 0) & BYTE_MASK)
    elif(token.type == "WORD"):
      if(token.word in constants):
        return(constants[token.word])
      elif(token.word in targets):
        return(targets[token.word])
      elif(token.word in regs):
        return(regs[token.word])
      elif(token.word in ports):
        return(ports[token.word])
      elif(token.word in conds):
        return(conds[token.word])
      else:
        print(f"Error: Unknown token '{token.word}' at line {token.line}.")
        sys.exit(1)
    elif(token.type == "STRING"):
      if(len(token.word) == 1):
        return(ord(token.word[0]))
      else:
        print(f"Error: Invalid string token '{token.word}' at line {token.line}.")
        sys.exit(1)
    else:
      print(f"Error: Invalid token type '{token.type}' at line {token.line}.")
      sys.exit(1)

  #...
  ROM = bytearray()


  return(ROM)

#------------------------------------------------------------------------------
if __name__ == "__main__":
  args = parse_cmd_arguments()
  #...
  BYTE_LENGHT = args.bytes if args.bytes else 1
  BYTE_MASK = (1 << (BYTE_LENGHT * 8)) - 1
  DEBUG_MODE = args.debug
  #...
  input_code = get_input_code(args.input)
  tokens = tokenize_code(input_code)
  macros, tokens = parse_macros(tokens)
  tokens = apply_macros(macros, tokens)
  # remove repeation seperators
  i = 0
  while(i < len(tokens)-1):
    if(tokens[i].type == "SEPARATOR" and tokens[i+1].type == "SEPARATOR"):
      tokens.pop(i)
    else:
      i += 1
  print("-"*20)
  print("Generating bytes...")
  ROM = generate_bytes(tokens)
  #...
  if(DEBUG_MODE):
    print("Tokens:")
    for token in tokens:
      print(token)
    #...
    for token in tokens:
      if(token.type == "SEPARATOR"):
        print()
      else:
        print(token.word, end=" ")


  output_rom(ROM, args.output)