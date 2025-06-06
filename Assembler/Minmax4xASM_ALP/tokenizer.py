import re
from typing import override

#...
#BLANK, WORD, VALUE, COMMENT, NL
class Token:
	def __init__(self, line: int, type: str, word: str):
		self.line: int = line
		self.type: str = type
		self.word: str = word

	@override
	def __repr__(self) -> str:
		return(f"{self.line} - {self.type}: {str([self.word])[1:-1]}")

def Tokenizer(input_code: str) -> list[Token]:
	input_code += "\n\n"
	tokens: list[Token] = []
	current_token_type: str = "BLANK"
	current_token_char: str = ""
	current_line: int = 1
	i = 0
	while(i < len(input_code)):
		char: str = input_code[i]
		match current_token_type:
			#-------------------------------
			case "BLANK": # BLANK
				if(char == ";"):
					current_token_type = "COMMENT"
				if(re.match("[A-Z]|[a-z]|_", char)):
					current_token_char += char
					current_token_type = "WORD"
				if(re.match("[0-9]|-", char)):
					current_token_type = "VALUE"
					current_token_char += char
			#-------------------------------
			case "COMMENT":
				if(char == "\n"):
					current_token_type = "BLANK"
			#-------------------------------
			case "WORD":
				if(re.match("[A-Z]|[a-z]|[0-9]|_", char)):
					current_token_char += char
				elif(char == ":"):
					tokens.append(Token(current_line, "BRANCH", current_token_char))
					current_token_char = ""
					current_token_type = "BLANK"
				else:
					tokens.append(Token(current_line, current_token_type, current_token_char))
					current_token_char = ""
					current_token_type = "BLANK"
			#-------------------------------
			case "VALUE":
				if(re.match("[0-9]|_|b|x|-", char)):
					current_token_char += char
				else:
					tokens.append(Token(current_line, current_token_type, current_token_char))
					current_token_char = ""
					current_token_type = "BLANK"
					if(char == ">"):
						tokens.append(Token(current_line, "MACRO_END", ">"))
		#...
		if(char == "\n"):
			current_line += 1
			tokens.append(Token(current_line, "NL", "\n"))
		#...
		i += 1
	
	return(tokens)