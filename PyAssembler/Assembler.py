#! /usr/bin/env
import struct
import argparse
from enum import IntEnum, unique



class Sections():
    
    STRING = '.string'
    DATA =   '.data'


class AddressingMode():
    REGISTER    = '00'
    IMMEDIATE   = '01'
    DIRECT      = '10'
    INDIRECT    = '11'

class Assembler():

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


    def __init__(self, in_file, out_file):
        self.input_file = in_file
        self.output_file = out_file
        self.sym_tbl = {}
        self.current_address = 0


    # Helper Functions

    def invokeError(self, message):
        print("ERROR:" + message)
        exit()

    def convert_str_to_binary(self, data_string):
        self.current_address += (len(data_string) + 1)
        return ''.join(format(ord(i), '08b')+'\n' for i in data_string+'\0')[:-1]

    def handle_addressing_mode(self, second_arg):
        addr_mode = AddressingMode.DIRECT
        clean_sec_arg = second_arg
        if Assembler.REGISTERS.get(second_arg):
            addr_mode = AddressingMode.REGISTER
        elif second_arg.isnumeric():
            addr_mode = AddressingMode.IMMEDIATE
        elif second_arg.startswith('[') and second_arg.endswith(']'):
            addr_mode = AddressingMode.INDIRECT
            clean_sec_arg = second_arg[1:-1]
        return addr_mode, clean_sec_arg

    def update_sym_tbl(self, label):
        self.sym_tbl.update({label: self.current_address})

    def handle_label(self, words):
        if words[0].endswith(':'):
            self.update_sym_tbl(words[0][:-1])
            words.pop(0)

    def handle_by_type(self, words, opcode_type, translated_words):
        trans_word1, trans_word2 = translated_words
        self.current_address += 2

        if opcode_type == 0:        # nop
            return        
        
        addr_mode, clean_sec_arg = self.handle_addressing_mode(words[-1])
        trans_word1 = trans_word1[:7] + addr_mode + trans_word1[9:]       # update addr_mode bits
        
        if opcode_type == 1:                                # not clr inc dec jmp jne jz sections
            bin_reg = Assembler.REGISTERS.get(clean_sec_arg)                                          # check the inner parameter
            if bin_reg:
                trans_word1 = trans_word1[:4] + bin_reg + trans_word1[7:]      # update first reg bits
            elif clean_sec_arg.isnumeric():
                trans_word2 = format(int(clean_sec_arg), '016b')                          # update numeric value bits
            else:
                trans_word2 = clean_sec_arg                                               # update placeholder bits
        
        elif opcode_type == 2:                              # mov cmp add sub lea xor or rol
            bin_reg1 = Assembler.REGISTERS.get(words[1][:-1])                                        # remove ','
            if not bin_reg1: 
                self.invokeError("Invalid first register of 3-type line")
            else:
                trans_word1 = trans_word1[:4] + bin_reg1 + trans_word1[7:]  # update first reg bits
            bin_reg2 = Assembler.REGISTERS.get(clean_sec_arg)
            if bin_reg2:
                return trans_word1[:9] + bin_reg2 + trans_word1[12:]                # update second reg bits
            elif clean_sec_arg.isnumeric():
                trans_word2 = format(int(clean_sec_arg), '016b')                          # update numeric value bits
            else:
                trans_word2 = clean_sec_arg                                               # update placeholder bits
        
        else:
            self.invokeError("It is not a valid assembly line (maybe comment or sections).")
        
        self.current_address += 2
        translated_words[0] = trans_word1
        translated_words[1] = '\n' + trans_word2 if trans_word2 != '' else trans_word2          # TODO it is terrible!


    def translate_line(self, asm_line):
        """ 
        Converts an assembly code line to it's binary representation.
        
        :param asm_line: A string represents the assembly code line
        :returns: The binary representation of the assembly line.
        :rtype: str
        """

        words = asm_line.split('[')
        if len(words) > 1:
            asm_line = words[0] + "[" + words[1].replace(" ", "")
        words = asm_line.split()
        self.handle_label(words)
        translated_words = [Assembler.EMPTY_WORD, '']
        if self.section_handler(words, translated_words):
            return translated_words[0]
        bin_opcode, opcode_type = Assembler.OPCODES.get(words[0])
        translated_words[0] = bin_opcode + Assembler.EMPTY_WORD[4:]                   # update opcode bits
        self.handle_by_type(words, opcode_type, translated_words)
        return ''.join(translated_words)

    def fix_line(self, damaged_line):
        try:
            int(damaged_line, 2)
            return damaged_line
        except Exception:
            for label_tuple in self.sym_tbl:
                damaged_line = damaged_line.replace(label_tuple, str(self.sym_tbl[label_tuple]))
            damaged_line = eval(damaged_line)
            return format(int(damaged_line) & 0xffff, '016b')

    def section_handler(self, words, translated_words):
        if words[0] == Sections.STRING:
            translated_words[0] = self.convert_str_to_binary(words[1][1:-1])
        elif words[0] == Sections.DATA:
            self.current_address += 2
            translated_words[0] = format(int(words[1]), '016b')
        else:
            return
        return True

    def clean_comments(self, asm_lines):
        for index, line in enumerate(asm_lines):
            line = line.strip()
            if line == '' or line.startswith(';'):        # Blank lines or Comment lines
                asm_lines[index] = None
            else:
                code_then_comment = line.split(';')
                asm_lines[index] = code_then_comment[0].strip()
        return [line for line in asm_lines if line is not None]

    # Public Functions
    def first_step(self, assembly_file):
        with open(assembly_file,'r') as origin_file:
            all_lines = origin_file.readlines()
            cleaned_lines = self.clean_comments(all_lines)
            semi_trans_lines = [self.translate_line(line) for line in cleaned_lines]
        with open('PyAssembler/output/semi_output.txt', 'w') as outfile:
            for line in semi_trans_lines:
                outfile.write(line + '\n')


    def second_step(self, outfile_name):
        with open('PyAssembler/output/semi_output.txt','r') as intermidiate_file:
            all_lines = intermidiate_file.readlines()
            all_lines = [self.fix_line(line.strip()) for line in all_lines]
        output_binary_string = ''.join(all_lines)
        with open(outfile_name, 'wb') as bin_out:
            bytes_string = [(output_binary_string[i:i+8]) for i in range(0, len(output_binary_string), 8)]
            for byte_str in bytes_string:
                bin_out.write(struct.pack('>B', int(byte_str, 2)))
        print("Assembling Done.")


    def assemble_code(self):
        self.first_step(self.input_file)
        self.second_step(self.output_file)

def setup_argparse():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="Directs the input to a name of your choice")
    parser.add_argument("-o", "--output", help="Directs the output to a name of your choice")
    return parser.parse_args()

if __name__ == '__main__':
    args = setup_argparse()
    asm = Assembler(args.input, args.output)
    asm.assemble_code()