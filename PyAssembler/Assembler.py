#! /usr/bin/env
import struct
import argparse
from enum import IntEnum, unique

# Constants
WORD_SIZE = 16
EMPTY_WORD = '0000000000000000'
OPCODES = {
    'mov': ("0000", 2),
    'cmp': ("0001", 2),
    'add': ("0010", 2),
    'sub': ("0011", 2),
    'not': ("0100", 1),
    'clr': ("0101", 1),
    'lea': ("0110", 2),
    'inc': ("0111", 1),
    'dec': ("1000", 1),
    'jmp': ("1001", 1),
    'jne': ("1010", 1),
    'jz' : ("1011", 1),
    'xor': ("1100", 2),
    'or' : ("1101", 2),
    'rol': ("1110", 2),
    'nop': ("1111", 0)
}

REGISTERS = {
    'r0': "000",
    'r1': "001",
    'r2': "010",
    'r3': "011",
    'r4': "100",
    'r5': "101",
    'r6': "110",
    'r7': "111"
    }

class Sections():
    STRING = '.string'
    DATA =   '.data'


class AddressingMode():
    REGISTER    = '00'
    IMMEDIATE   = '01'
    DIRECT      = '10'
    INDIRECT    = '11'



# Global Variables
current_address = 0
sym_tbl = {}
args = {}


# Helper Functions

def setup_argparse():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="Directs the input to a name of your choice")
    parser.add_argument("-o", "--output", help="Directs the output to a name of your choice")
    args = parser.parse_args()

def invokeError(message):
    print("ERROR:" + message)
    exit()

def convert_str_to_binary(data_string):
    global current_address
    current_address = current_address + len(data_string) + 1
    return ''.join(format(ord(i), '08b')+'\n' for i in data_string+'\0')[:-1]

def handle_addressing_mode(second_arg):
    addr_mode = AddressingMode.DIRECT
    clean_sec_arg = second_arg
    if REGISTERS.get(second_arg):
        addr_mode = AddressingMode.REGISTER
    elif second_arg.isnumeric():
        addr_mode = AddressingMode.IMMEDIATE
    elif second_arg.startswith('[') and second_arg.endswith(']'):
        addr_mode = AddressingMode.INDIRECT
        clean_sec_arg = second_arg[1:-1]
    return addr_mode, clean_sec_arg

def update_sym_tbl(label):
    global current_address, sym_tbl
    sym_tbl.update({label: current_address})

def handle_label(words):
    if words[0].endswith(':'):
        update_sym_tbl(words[0][:-1])
        words.pop(0)

def handle_by_type(words, opcode_type, translated_words):
    global current_address
    trans_word1, trans_word2 = translated_words
    current_address += 2

    if opcode_type == 0:        # nop
        return        
    
    addr_mode, clean_sec_arg = handle_addressing_mode(words[-1])
    trans_word1 = trans_word1[:7] + addr_mode + trans_word1[9:]       # update addr_mode bits
    
    if opcode_type == 1:                                # not clr inc dec jmp jne jz sections
        bin_reg = REGISTERS.get(clean_sec_arg)                                          # check the inner parameter
        if bin_reg:
            trans_word1 = trans_word1[:4] + bin_reg + trans_word1[7:]      # update first reg bits
        elif clean_sec_arg.isnumeric():
            trans_word2 = format(int(clean_sec_arg), '016b')                          # update numeric value bits
        else:
            trans_word2 = clean_sec_arg                                               # update placeholder bits
    
    elif opcode_type == 2:                              # mov cmp add sub lea xor or rol
        bin_reg1 = REGISTERS.get(words[1][:-1])                                        # remove ','
        if not bin_reg1: 
            invokeError("Invalid first register of 3-type line")
        else:
            trans_word1 = trans_word1[:4] + bin_reg1 + trans_word1[7:]  # update first reg bits
        bin_reg2 = REGISTERS.get(clean_sec_arg)
        if bin_reg2:
            return trans_word1[:9] + bin_reg2 + trans_word1[12:]                # update second reg bits
        elif clean_sec_arg.isnumeric():
            trans_word2 = format(int(clean_sec_arg), '016b')                          # update numeric value bits
        else:
            trans_word2 = clean_sec_arg                                               # update placeholder bits
    
    else:
        invokeError("It is not a valid assembly line (maybe comment or sections).")
    
    current_address+=2
    translated_words[0] = trans_word1
    translated_words[1] = '\n' + trans_word2 if trans_word2 != '' else trans_word2          # TODO it is terrible!


def translate_line(ass_line):
    global current_address, sym_tbl
    words = ass_line.split()
    handle_label(words)
    translated_words = [EMPTY_WORD, '']
    if section_handler(words, translated_words):
        return translated_words[0]
    bin_opcode, opcode_type = OPCODES.get(words[0])
    translated_words[0] = bin_opcode + EMPTY_WORD[4:]                   # update opcode bits
    handle_by_type(words, opcode_type, translated_words)
    return ''.join(translated_words)

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

def section_handler(words, translated_words):
    global current_address
    if words[0] == Sections.STRING:
        translated_words[0] = convert_str_to_binary(words[1][1:-1])
    elif words[0] == Sections.DATA:
        current_address+=2
        translated_words[0] = format(int(words[1]), '016b')
    else:
        return
    return True

def clean_comments(asm_lines):
    for index, line in enumerate(asm_lines):
        line = line.strip()
        if line == '' or line.startswith(';'):        # Blank lines or Comment lines
            asm_lines[index] = None
        else:
            code_then_comment = line.split(';')
            asm_lines[index] = code_then_comment[0].strip()
    return [line for line in asm_lines if line is not None]

# Public Functions
def first_step(assembly_file):
    with open(assembly_file,'r') as origin_file:
        all_lines = origin_file.readlines()
        cleaned_lines = clean_comments(all_lines)
        semi_trans_lines = [translate_line(line) for line in cleaned_lines]
    with open('PyAssembler/output/semi_output.txt', 'w') as outfile:
        for line in semi_trans_lines:
            outfile.write(line + '\n')


def second_step(outfile_name):
    with open('PyAssembler/output/semi_output.txt','r') as intermidiate_file:
        all_lines = intermidiate_file.readlines()
        all_lines = [fix_line(line.strip()) for line in all_lines]
    output_binary_string = ''.join(all_lines)
    with open(outfile_name, 'wb') as bin_out:
        bytes_string = [(output_binary_string[i:i+8]) for i in range(0, len(output_binary_string), 8)]
        for byte_str in bytes_string:
            bin_out.write(struct.pack('>B', int(byte_str, 2)))
    print("Assembling Done.")


def assemble_code(input_file, output_file):
    first_step(input_file)
    second_step(output_file)


# Execute
setup_argparse()
assemble_code(args.input, args.output)
