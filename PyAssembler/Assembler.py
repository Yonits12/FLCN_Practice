#!/usr/bin/env python3.7

import sys
import struct
import argparse
from enum import Enum



class Assembler:

    class TooManyParamsException(TypeError):
        """
        Raised when the input line consist of 
        more than 2 parameters """

        def __init__(self, code_line):
            self.code_line = code_line

        def __str__(self):
            return 'Invalid assembly code line: Too many arguments at line: {0} '.format(self.code_line)


    class NotRegisterArgumentException(ValueError):
        """
        Raised when there is not a register in the 
        first argument of a type-2 input line """

        def __init__(self, code_line, arg):
                self.code_line = code_line
                self.arg = arg

        def __str__(self):
            return 'Invalid assembly code line: first parameter {0} must be a register at line:  {1} '.format(self.arg, self.code_line)



    class Sections(Enum):
        STRING = '.string'
        DATA =   '.data'


    class AddressingMode(Enum):
        REGISTER    = '00'
        IMMEDIATE   = '01'
        DIRECT      = '10'
        INDIRECT    = '11'


    # Constants
    WORD_SIZE = 16
    ASCII_SIZE = 8
    EMPTY_WORD = '0' * WORD_SIZE
    
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


    def __init__(self):
        self.sym_tbl = {}
        self.untranslated_exps = {}
        self.current_address = 0


    def convert_str_to_binary(self, data_string):
        if not data_string.startswith('"') and data_string.endswith('"'):
                raise TypeError("String excpected, with surrounding \" at .string line")
        data_string = data_string[1:-1]
        if '"' in data_string:
            raise ValueError("String must not include \" characters at .string line")
        self.current_address += (len(data_string) + 1)
        return ''.join(format(ord(i), '08b')+'\n' for i in data_string+'\0').strip('\n')


    def handle_addressing_mode(self, second_arg):
        addr_mode = Assembler.AddressingMode.DIRECT.value
        clean_sec_arg = second_arg

        if Assembler.REGISTERS.get(second_arg):
            addr_mode = Assembler.AddressingMode.REGISTER.value
        
        elif second_arg.isnumeric():
            addr_mode = Assembler.AddressingMode.IMMEDIATE.value
        
        elif second_arg.startswith('[') and second_arg.endswith(']'):
            addr_mode = Assembler.AddressingMode.INDIRECT.value
            clean_sec_arg = second_arg[1:-1]
        
        return addr_mode, clean_sec_arg


    def handle_label(self, asm_line):
        # Extract label
        label, *rest_line = asm_line.split(':', maxsplit=1)
        
        # Save label to symbol table, and remove from line words
        if len(rest_line) > 0:
            self.sym_tbl[label] =  self.current_address
            return rest_line[0].lstrip()
        return asm_line


    def handle_1_param_type(self, translated_words, arg):
        trans_word1, trans_word2 = translated_words
        
        # Find 1st argument and then update relevant bits
        bin_reg = Assembler.REGISTERS.get(arg)
        
        if bin_reg:
            trans_word1 = trans_word1[:4] + bin_reg + trans_word1[7:]
        
        elif arg.isnumeric():
            trans_word2 = format(int(arg), '016b')
        
        else:
            trans_word2 = arg
        
        translated_words[0] = trans_word1
        translated_words[1] = '\n' + trans_word2 if trans_word2 != '' else trans_word2          # TODO it is terrible!


    def handle_2_param_type(self, translated_words, arg1, arg2):
        trans_word1, trans_word2 = translated_words
        
        # Find 1st register and then update reg1 bits
        bin_reg1 = Assembler.REGISTERS.get(arg1)
        
        if not bin_reg1: 
            raise Assembler.NotRegisterArgumentException(None, arg1)
        
        trans_word1 = trans_word1[:4] + bin_reg1 + trans_word1[7:]  

        # Find 2nd argument and then update relevant bits
        bin_reg2 = Assembler.REGISTERS.get(arg2)
        
        if bin_reg2:
            return trans_word1[:9] + bin_reg2 + trans_word1[12:]                
       
        if arg2.isnumeric():
            trans_word2 = format(int(arg2), '016b')                          
       
        else:
            trans_word2 = arg2
        
        translated_words[0] = trans_word1
        translated_words[1] = '\n' + trans_word2 if trans_word2 != '' else trans_word2          # TODO it is terrible!


    def handle_by_opcode_type(self, words, opcode_type, translated_words):
        trans_word1 = translated_words[0]
        self.current_address += 2

        # nop
        if opcode_type == 0:
            return        
        
        addr_mode, clean_sec_arg = self.handle_addressing_mode(words[-1])
        
        # update addr_mode bits
        translated_words[0] = trans_word1[:7] + addr_mode + trans_word1[9:]       
        
        # not clr inc dec jmp jne jz
        if opcode_type == 1:                                
            self.handle_1_param_type(translated_words, clean_sec_arg)
        
        # mov cmp add sub lea xor or rol
        elif opcode_type == 2:                              
           self.handle_2_param_type(translated_words, words[1].rstrip(','), clean_sec_arg)
        
        self.current_address += 2


    def translate_line(self, asm_line):
        """ 
        Converts an assembly code line to it's binary representation.
        
        :param asm_line: A string represents the assembly code line
        :returns: The binary representation of the assembly line.
        :rtype: str
        """
        unlabeled_asm_line = self.handle_label(asm_line)

        translated_words = [Assembler.EMPTY_WORD, '']
        # Section line check and translation
        if self.section_handler(unlabeled_asm_line, translated_words):
            return translated_words[0]

        # Remove spaces from indirect expression, if any.
        words = unlabeled_asm_line.split('[')
        if len(words) > 1:
            unlabeled_asm_line = words[0] + "[" + words[1].replace(" ", "")

        words = unlabeled_asm_line.split()
        
        # update opcode bits
        bin_opcode, opcode_type = Assembler.OPCODES.get(words[0])
        translated_words[0] = bin_opcode + Assembler.EMPTY_WORD[4:]                   
        
        if len(words[1:]) > opcode_type:
            raise Assembler.TooManyParamsException(asm_line)
        try:
            self.handle_by_opcode_type(words, opcode_type, translated_words)
        
        except Assembler.NotRegisterArgumentException as e:
            e.code_line = asm_line
            raise
        
        return ''.join(translated_words)


    def fix_line(self, damaged_line):
        
        # Check if the line is not damaged
        if damaged_line.strip('01') == '':
            return damaged_line

        # Re-write the expression as an arithmetic expression using symbol table
        for label_tuple in self.sym_tbl:
            damaged_line = damaged_line.replace(label_tuple, str(self.sym_tbl[label_tuple]))
        
        damaged_line = eval(damaged_line)
        return format(int(damaged_line) & 0xffff, '016b')


    def section_handler(self, asm_line, translated_words):
        section, *rest_line = asm_line.split(maxsplit=1)
        
        if section == Assembler.Sections.STRING.value:
            translated_words[0] = self.convert_str_to_binary(rest_line[0])       # remove quotes
        elif section == Assembler.Sections.DATA.value:
            argument = rest_line[0].lstrip()
            if argument.isnumeric():
                self.current_address += 2
                translated_words[0] = format(int(argument), '016b') 
            else:
                raise ValueError("The input was not a number at line: " + asm_line)
        else:
            return False
        return True


    def clean_comments(self, asm_lines):

        for index, line in enumerate(asm_lines):
            line = line.strip()
            
            # Blank lines or Comment lines
            if line == '' or line.startswith(';'):
                asm_lines[index] = None
            
            else:
                # Inline comments
                code, *comment = line.split(';', maxsplit=1)
                asm_lines[index] = code.strip()
        
        return [line for line in asm_lines if line is not None]


    def first_step(self, assembly_lines):
        cleaned_lines = self.clean_comments(assembly_lines)
        semi_trans_lines = [self.translate_line(line) for line in cleaned_lines]
        
        # Separate adjacent lines
        semi_trans_lines = [line.split('\n') for line in semi_trans_lines]
        semi_trans_lines = [element for sublist in semi_trans_lines for element in sublist]
        return semi_trans_lines


    def second_step(self, semi_trans_lines):
        # Fix lines using symbol table & place-holders
        fixed_lines = [self.fix_line(line.strip()) for line in semi_trans_lines]
        
        # Prepare binary writing
        output_binary_string = ''.join(fixed_lines)
        bytes_string = [(output_binary_string[i:i+8]) for i in range(0, len(output_binary_string), 8)]
        return bytes_string

    def assemble_code(self, assembly_lines):
        half_translated_lines = self.first_step(assembly_lines)
        return self.second_step(half_translated_lines)



def setup_argparse():
    parser = argparse.ArgumentParser()
    
    parser.add_argument("-i", "--input", help="Directs the input to a name of your choice", required=True)
    parser.add_argument("-o", "--output", help="Directs the output to a name of your choice", required=True)
    
    return parser.parse_args()

if __name__ == '__main__':
    args = setup_argparse()
    asm = Assembler()
    all_lines = []

    with open(args.input,'r') as origin_file:
        all_lines = origin_file.readlines()

    assembled_code_string = asm.assemble_code(all_lines)
    
    with open(args.output, 'wb') as bin_out:
        for byte_str in assembled_code_string:
            bin_out.write(struct.pack('>B', int(byte_str, 2)))

    print("Assembling Done.")

    
    