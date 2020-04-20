# Global Variables
current_address = 0
sym_tbl = {}


# Helper Functions

def invokeError(message):
   print("ERROR:" + message)
   exit()

def convert_str_to_binary(data_string):
   global current_address
   current_address = current_address + len(data_string) + 1
   return ''.join(format(ord(i), '08b')+'\n' for i in data_string+'\0')[:-1]

def switch_opcode(opcode):
   switcher = {
      'mov': "0000",
      'cmp': "0001",
      'add': "0010",
      'sub': "0011",
      'not': "0100",
      'clr': "0101",
      'lea': "0110",
      'inc': "0111",
      'dec': "1000",
      'jmp': "1001",
      'jne': "1010",
      'jz': "1011",
      'xor': "1100",
      'or': "1101",
      'rol': "1110",
      'nop': "1111"
   }
   return switcher.get(opcode, False)

def switch_register(reg_idx):
   switcher = {
      'r0': "000",
      'r1': "001",
      'r2': "010",
      'r3': "011",
      'r4': "100",
      'r5': "101",
      'r6': "110",
      'r7': "111"
   }
   return switcher.get(reg_idx, False)

def switch_addressing_mode(second_arg):
   ans = ['10', second_arg]
   if switch_register(second_arg):
      ans[0] = '00'
   elif second_arg.isnumeric():
       ans[0] = '01'
   elif second_arg[0] == '[' and second_arg[-1] == ']':
       ans[0] = '11'
       ans[1] = second_arg[1:-1]
   return ans

def update_sym_tbl(label):
   global current_address, sym_tbl
   sym_tbl.update({label: current_address})

def check_label(words):
   if words[0][-1] == ':':
      update_sym_tbl(words[0][:-1])
      return words[1:]
   return words

def handle_opcode(words):
   translated_word1 = '0000000000000000'
   bin_opcode = switch_opcode(words[0])
   if not bin_opcode:
      return True, section_handler(words)
   return False, bin_opcode + translated_word1[4:]        # update opcode bits

def handle_by_type(words, translated_word1):
   global current_address
   translated_word2 = '0000000000000000'
   current_address+=2
   line_type = len(words)
   if(line_type == 1): return translated_word1        # nop
   addr_mode = switch_addressing_mode(words[-1])
   translated_word1 = translated_word1[:7] + addr_mode[0] + translated_word1[9:]       # update addr_mode bits
   if(line_type == 2):                                # not clr inc dec jmp jne jz sections
      bin_reg = switch_register(addr_mode[1])                                          # check the inner parameter
      if bin_reg: return translated_word1[:4] + bin_reg + translated_word1[7:]      # update first reg bits
      elif addr_mode[1].isnumeric():
         translated_word2 = format(int(addr_mode[1]), '016b')                          # update numeric value bits
      else:
         translated_word2 = addr_mode[1]                                               # update placeholder bits
   elif(line_type == 3):                              # mov cmp add sub lea xor or rol
      bin_reg1 = switch_register(words[1][:-1])                                        # remove ','
      if not bin_reg1: invokeError("Invalid first register of 3-type line")
      else: translated_word1 = translated_word1[:4] + bin_reg1 + translated_word1[7:]  # update first reg bits
      bin_reg2 = switch_register(addr_mode[1])
      if bin_reg2: return translated_word1[:9] + bin_reg2 + translated_word1[12:]                # update second reg bits
      elif addr_mode[1].isnumeric():
         translated_word2 = format(int(addr_mode[1]), '016b')                          # update numeric value bits
      else:
         translated_word2 = addr_mode[1]                                               # update placeholder bits
   else:
      invokeError("It is not a valid assembly line (maybe comment or sections).")
   current_address+=2
   return '' + translated_word1 + '\n' + translated_word2

def translate_line(ass_line):
   global current_address, sym_tbl
   words = ass_line.split(' ')
   words = check_label(words)
   label_flag, translated_word1 = handle_opcode(words)
   if label_flag: return translated_word1
   return handle_by_type(words, translated_word1)

def fix_line(damaged_line):
   global sym_tbl
   try:
      int(damaged_line, 2)
      return damaged_line
   except Exception:
      for label_tuple in sym_tbl:
         damaged_line = damaged_line.replace(label_tuple, str(sym_tbl[label_tuple]))
      damaged_line = eval(damaged_line)
      return format(int(damaged_line) & 0xffff, '016b')

def section_handler(words):
   global current_address
   if(words[0] == '.string'):
      return convert_str_to_binary(words[1][1:-1])
   elif(words[0] == '.data'):
      current_address+=2
      return format(int(words[1]), '016b')
   else: invokeError("An invalid opcode was detected.")


# Public Functions
def first_step(assembly_file):
   with open(assembly_file,'r') as origin_file:
      all_lines = origin_file.readlines()
      for index, line in enumerate(all_lines):
         if line == '\n' or line[0] == ';': continue                                      # Blank lines, Comment lines
         all_lines[index] = translate_line(line[:-1] if line[-1] is '\n' else line)       # remove \n
   with open('semi_output.txt', 'w') as outfile:
      for line in all_lines:
         outfile.write(line + '\n')


def second_step(outfile_name):
   with open('semi_output.txt','r') as intermidiate_file:
      all_lines = intermidiate_file.readlines()
      for index, line in enumerate(all_lines):
         all_lines[index] = fix_line(line[:-1] if line[-1] is '\n' else line)          # remove \n
   with open('cool_' + outfile_name, 'w') as outfile:                                  # Output with line breaks
      for line in all_lines:
         outfile.write(line + '\n')
   with open(outfile_name, 'w') as outfile:
      for line in all_lines:
         outfile.write(line)
   print("Assembling Done.")


def assemble_code(input_file, output_file):
   first_step(input_file)
   second_step(output_file)


""" # For Extreme Case
assemble_code('lightAssmbly.txt', 'lightOutput.txt') """

# For Example Case
assemble_code('Example.txt', 'Output.txt')
