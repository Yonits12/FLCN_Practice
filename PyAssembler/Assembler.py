#! /usr/bin/python3.7
import struct
import argparse

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
    return translated_word1 + '\n' + translated_word2

def translate_line(ass_line):
    global current_address, sym_tbl
    words = ass_line.split()
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
