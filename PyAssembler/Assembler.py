#! /usr/bin/env

import sys
import struct
import argparse
from enum import IntEnum, unique


class TooManyParamsException(Exception):
   """
   Raised when the input line consist of 
   more than 2 parameters
   """
   pass

class NotRegisterArgumentException(Exception):
   """
   Raised when there is not a register in the 
   first argument of a type-2 input line
   """
   pass


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


    def convert_str_to_binary(self, data_string):
        self.current_address += (len(data_string) + 1)
        return ''.join(format(ord(i), '08b')+'\n' for i in data_string+'\0').strip('\n')


    def handle_addressing_mode(self, second_arg):
        addr_mode = AddressingMode.DIRECT
        clean_sec_arg = second_arg

        if Assembler.REGISTERS.get(second_arg):
            addr_mode = AddressingMode.REGISTER
        
        elif second_arg.isnumeric():
            addr_mode = AddressingMode.IMMEDIATE
        
        elif second_arg.startswith('[') and second_arg.endswith(']'):
            addr_mode = AddressingMode.INDIRECT
            clean_sec_arg = second_arg.strip('[]')
        
        return addr_mode, clean_sec_arg


    def handle_label(self, words):

        # Extract label
        label_then_code = words[0].split(':')
        
        # Save label to symbol table, and remove from line words
        if len(label_then_code) > 1:
            self.sym_tbl.update({label_then_code[0].rstrip(':'): self.current_address})
            words.pop(0)
            
            # Repair words of line
            if label_then_code[1] != '':
                words.insert(0, label_then_code[1])


    def handle_type_1(self, translated_words, arg):
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


    def handle_type_2(self, translated_words, arg1, arg2):
        trans_word1, trans_word2 = translated_words
        
        # Find 1st register and then update reg1 bits
        bin_reg1 = Assembler.REGISTERS.get(arg1)
        
        if not bin_reg1: 
            raise Exception("Invalid first register of 3-type line: " + arg1)
        
        else:
            trans_word1 = trans_word1[:4] + bin_reg1 + trans_word1[7:]  

        # Find 2nd argument and then update relevant bits
        bin_reg2 = Assembler.REGISTERS.get(arg2)
        
        if bin_reg2:
            return trans_word1[:9] + bin_reg2 + trans_word1[12:]                
       
        elif arg2.isnumeric():
            trans_word2 = format(int(arg2), '016b')                          
       
        else:
            trans_word2 = arg2
        
        translated_words[0] = trans_word1
        translated_words[1] = '\n' + trans_word2 if trans_word2 != '' else trans_word2          # TODO it is terrible!


    def handle_by_type(self, words, opcode_type, translated_words):
        trans_word1 = translated_words[0]
        self.current_address += 2

        # nop
        if opcode_type == 0:
            return        
        
        addr_mode, clean_sec_arg = self.handle_addressing_mode(words[-1])
        
        # update addr_mode bits
        translated_words[0] = trans_word1[:7] + addr_mode + trans_word1[9:]       
        
        # not clr inc dec jmp jne jz sections
        if opcode_type == 1:                                
            self.handle_type_1(translated_words, clean_sec_arg)
        
        # mov cmp add sub lea xor or rol
        elif opcode_type == 2:                              
           self.handle_type_2(translated_words, words[1].rstrip(','), clean_sec_arg)
        
        else:
            raise TooManyParamsException
        
        self.current_address += 2


    def translate_line(self, asm_line):
        """ 
        Converts an assembly code line to it's binary representation.
        
        :param asm_line: A string represents the assembly code line
        :returns: The binary representation of the assembly line.
        :rtype: str
        """

        # Remove spaces from indirect expression, if any.
        words = asm_line.split('[')
        if len(words) > 1:
            asm_line = words[0] + "[" + words[1].replace(" ", "")
        
        words = asm_line.split()
        self.handle_label(words)
        
        translated_words = [Assembler.EMPTY_WORD, '']
        
        # Section line check. None returns if it is.
        if self.section_handler(words, translated_words) is None:
            return translated_words[0]
        
        # update opcode bits
        bin_opcode, opcode_type = Assembler.OPCODES.get(words[0])
        translated_words[0] = bin_opcode + Assembler.EMPTY_WORD[4:]                   
        
        try:
            self.handle_by_type(words, opcode_type, translated_words)
        
        except TooManyParamsException:
            raise Exception("At line: " + asm_line + " : Invalid assembly code line: Too many paramenters")
        
        except NotRegisterArgumentException:
            raise Exception("At line: " + asm_line + " : First parameter of type-2 line must be a register.")
        
        return ''.join(translated_words)


    def fix_line(self, damaged_line):
        
        # Check if the line is damaged (== not binary)
        if damaged_line.strip('01') == '':
            return damaged_line

        else:
            # Re-write the expression as an arithmetic expression using symbol table
            for label_tuple in self.sym_tbl:
                damaged_line = damaged_line.replace(label_tuple, str(self.sym_tbl[label_tuple]))
            
            damaged_line = eval(damaged_line)
            return format(int(damaged_line) & 0xffff, '016b')


    def section_handler(self, words, translated_words):
        
        if words[0] == Sections.STRING:
            translated_words[0] = self.convert_str_to_binary(words[1].strip('"'))       # remove " "
        
        elif words[0] == Sections.DATA:
            self.current_address += 2
            translated_words[0] = format(int(words[1]), '016b')
        
        else:
            return True


    def clean_comments(self, asm_lines):

        for index, line in enumerate(asm_lines):
            line = line.strip()
            
            # Blank lines or Comment lines
            if line == '' or line.startswith(';'):
                asm_lines[index] = None
            
            else:
                # Inline comments
                code_then_comment = line.split(';')
                asm_lines[index] = code_then_comment[0].strip()
        
        return [line for line in asm_lines if line is not None]


    def first_step(self, assembly_file):
        
        with open(assembly_file,'r') as origin_file:
            all_lines = origin_file.readlines()
        
        cleaned_lines = self.clean_comments(all_lines)
        
        # Translates the assembly lines with place-holders for the yet unconvertable expressions
        semi_trans_lines = [self.translate_line(line) for line in cleaned_lines]
        
        # Separate adjacent lines
        semi_trans_lines = [line.split('\n') for line in semi_trans_lines]
        semi_trans_lines = [element for sublist in semi_trans_lines for element in sublist]
        
        return semi_trans_lines


    def second_step(self, outfile_name, semi_trans_lines):

        # Fix lines using symbol table & place-holders
        all_lines = [self.fix_line(line.strip()) for line in semi_trans_lines]
        
        # Prepare binary writing
        output_binary_string = ''.join(all_lines)
        bytes_string = [(output_binary_string[i:i+8]) for i in range(0, len(output_binary_string), 8)]
        
        with open(outfile_name, 'wb') as bin_out:
            for byte_str in bytes_string:
                bin_out.write(struct.pack('>B', int(byte_str, 2)))


    def assemble_code(self):

        half_translated_lines = self.first_step(self.input_file)
        
        self.second_step(self.output_file, half_translated_lines)
        
        print("Assembling Done.")



def setup_argparse():
    parser = argparse.ArgumentParser()
    
    parser.add_argument("-i", "--input", help="Directs the input to a name of your choice")
    parser.add_argument("-o", "--output", help="Directs the output to a name of your choice")
    
    return parser.parse_args()

if __name__ == '__main__':
    args = setup_argparse()
    asm = Assembler(args.input, args.output)
    asm.assemble_code()