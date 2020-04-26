#!/usr/bin/env python3.7

import sys
import struct
import argparse
import binascii
from enum import Enum


STR_R_FORMAT = 'r'
BYTES_W_FORMAT = 'wb'


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
        """
        Enumeration of the possible sections in the 
        assembly code """
        
        STRING = '.string'
        DATA =   '.data'


    class AddressingMode(Enum):
        """
        Enumeration of the possible Addressing modes
        which can be used in an assemblt code line """

        REGISTER    = 0b00
        IMMEDIATE   = 0b01
        DIRECT      = 0b10
        INDIRECT    = 0b11


    # Constants
    WORD_SIZE = 2
    ASCII_SIZE = 8
    EMPTY_WORD = 0b0
    
    OPCODE_OFFSET = 12
    REG1_OFFSET = 9
    ADDR_MODE_OFFSET = 7
    REG2_OFFSET = 4
    
    NUM_BYTES = 2
    TWO_BYTES_FORMAT = '>H'
    BIG_ENDIAN = 'big'
    NULL_TERMINATED = '\0'
    INDIRECT_PREFIX = '['
    INDIRECT_SUFFIX = ']'
    STRING_AFFIX = '"'
    LABEL_SUFFIX = ':'
    COMMENT_PREFIX = ';'
    REGISTER_SUFFIX = ','
    SPACE = " "
    
    FIRST_WORD = 0
    SECOND_WORD = 1
    ZERO_PARAMS_TYPE = 0
    ONE_PARAM_TYPE = 1
    TWO_PARAMS_TYPE = 2
    OPCODE = 0
    FIRST_PARAM = 1
    LAST_PARAM = -1
    
    OPCODES = {
        'mov': (0b0000, 2),
        'cmp': (0b0001, 2),
        'add': (0b0010, 2),
        'sub': (0b0011, 2),
        'not': (0b0100, 1),
        'clr': (0b0101, 1),
        'lea': (0b0110, 2),
        'inc': (0b0111, 1),
        'dec': (0b1000, 1),
        'jmp': (0b1001, 1),
        'jne': (0b1010, 1),
        'jz' : (0b1011, 1),
        'xor': (0b1100, 2),
        'or' : (0b1101, 2),
        'rol': (0b1110, 2),
        'nop': (0b1111, 0)
    }

    REGISTERS = {
        'r0': 0b000,
        'r1': 0b001,
        'r2': 0b010,
        'r3': 0b011,
        'r4': 0b100,
        'r5': 0b101,
        'r6': 0b110,
        'r7': 0b111
    }

    def __init__(self):
        self.sym_tbl = {}
        self.untranslated_exps = {}
        self.current_address = 0
        self.current_line_idx = -1

    def convert_str_to_binary(self, data_string):
        """ 
        Converts a string data in the .string section to it's binary
        representation bytes. A null byte is added at the end of the string.
        
        :param data_string: The data string.
        :returns: The corresponding binary bytes of the null-terminated string.
        :rtype: bytes
        """
        if not data_string.startswith(Assembler.STRING_AFFIX) and data_string.endswith(Assembler.STRING_AFFIX):
                raise TypeError("String excpected, with surrounding \" at .string line")
        
        data_string = data_string[len(Assembler.STRING_AFFIX):-len(Assembler.STRING_AFFIX)]
        if Assembler.STRING_AFFIX in data_string:
            raise ValueError("String must not include \" characters at .string line")
        
        data_string = data_string + Assembler.NULL_TERMINATED
        self.current_address += len(data_string)
        return binascii.a2b_qp(data_string)

    def handle_addressing_mode(self, last_arg):
        """ 
        Resolves the addressing mode of the line's last argument and
        cleans the addressing modes affixes from it.
        
        :param last_arg: The last argument of the assembly code line.
        :returns addr_mode: A 2-bits length binary represents the addresing mode.
        :returns clean_sec_arg: A string represents the cleaned version of the last argumet.
        :rtypes: integer, string
        """
        addr_mode = Assembler.AddressingMode.DIRECT.value
        clean_sec_arg = last_arg

        if Assembler.REGISTERS.get(last_arg):
            addr_mode = Assembler.AddressingMode.REGISTER.value
        elif last_arg.isnumeric():
            addr_mode = Assembler.AddressingMode.IMMEDIATE.value
        elif last_arg.startswith(Assembler.INDIRECT_PREFIX) and last_arg.endswith(Assembler.INDIRECT_SUFFIX):
            addr_mode = Assembler.AddressingMode.INDIRECT.value
            clean_sec_arg = last_arg[len(Assembler.INDIRECT_PREFIX):-len(Assembler.INDIRECT_SUFFIX)]
        return addr_mode, clean_sec_arg

    def handle_label(self, asm_line):
        """ 
        Checks if a label is attached to the assembly line and stores the
        address of the line. Afterwards, removes the label from the line.
        
        :param asm_line: The assembly code line.
        :returns: The unlabeled assembly code lide
        :rtype: string
        """
        # Extract label
        label, *rest_line = asm_line.split(Assembler.LABEL_SUFFIX, maxsplit=1)
        
        if rest_line:
            self.sym_tbl[label] = self.current_address
            return rest_line.pop().lstrip()
        return asm_line

    def section_handler(self, asm_line, translated_words):
        """ 
        Checks if the line consist of a section, and handles the conversion
        of it's data. Update the (potentially) 2 translated words with the new data.
        
        :param asm_line: The assembly code line.
        :param translated_words: The (potentially) 2 words translated so far.
        :returns: Whether the line is a section line (and handled) or not.
        :rtype: boolean
        """
        section, *rest_line = asm_line.split(maxsplit=1)
        
        if section == Assembler.Sections.STRING.value:
            translated_words[Assembler.FIRST_WORD] = self.convert_str_to_binary(rest_line.pop())      # remove quotes
        elif section == Assembler.Sections.DATA.value:
            argument = rest_line.pop().lstrip()
            if argument.isnumeric():
                self.current_address += Assembler.WORD_SIZE
                translated_words[Assembler.FIRST_WORD] = struct.pack(Assembler.TWO_BYTES_FORMAT, int(argument))
            else:
                raise ValueError("The input was not a number at line: " + asm_line)
        else:
            return False
        return True

    def handle_1_param_type(self, translated_words, arg):
        """ 
        Handles the 1-type line's parameter and update the cumulative translated words.
        
        :param translated_words: The (potentially) 2 words translated so far.
        :param arg: The parameter of the line.
        """
        trans_word1, trans_word2 = translated_words
        
        # Find 1st argument and then update relevant bits
        bin_reg = Assembler.REGISTERS.get(arg)
        if bin_reg:
            trans_word1 = trans_word1 | bin_reg << Assembler.REG1_OFFSET
        else:
            if arg.isnumeric():
                trans_word2 = int(arg)
            else:
                self.untranslated_exps[self.current_line_idx] = arg
                trans_word2 = None
            self.current_address += self.WORD_SIZE
        
        translated_words[self.FIRST_WORD] = trans_word1
        translated_words[self.SECOND_WORD] = trans_word2

    def handle_2_param_type(self, translated_words, arg1, arg2):
        """ 
        Handles the 2-type line's parameters and update the cumulative translated words.
        
        :param translated_words: The (potentially) 2 words translated so far.
        :param arg1: The first argument (must be register)
        :param arg2: The second argument
        """
        trans_word1, trans_word2 = translated_words
        # Find 1st register and then update reg1 bits
        bin_reg1 = Assembler.REGISTERS.get(arg1)
        
        if bin_reg1 is None: 
            raise Assembler.NotRegisterArgumentException(None, arg1)
        
        trans_word1 = trans_word1 | bin_reg1 << Assembler.REG1_OFFSET  

        # Find 2nd argument and then update relevant bits
        bin_reg2 = Assembler.REGISTERS.get(arg2)
        if bin_reg2 is not None:
            translated_words[Assembler.FIRST_WORD] = trans_word1 | bin_reg2 << Assembler.REG2_OFFSET
            return
        if arg2.isnumeric():
            trans_word2 = int(arg2)                          
        else:
            self.untranslated_exps[self.current_line_idx] = arg2
            trans_word2 = None
        
        self.current_address += Assembler.WORD_SIZE
        translated_words[Assembler.FIRST_WORD] = trans_word1
        translated_words[Assembler.SECOND_WORD] = trans_word2

    def handle_by_opcode_type(self, words, opcode_type, translated_words):
        """ 
        Handles the line's parameters according to the opcode and
        updates the cumulative translated words
        
        :param words: List of separated parts of a line.
        :param opcode_type: The number of parameters expected - indicator for the right handle
        :param translated_words: The (potentially) 2 words translated so far.
        """
        trans_word1 = translated_words[self.FIRST_WORD]
        self.current_address += Assembler.WORD_SIZE

        # nop
        if opcode_type == Assembler.ZERO_PARAMS_TYPE:
            return
        
        addr_mode, clean_sec_arg = self.handle_addressing_mode(words[Assembler.LAST_PARAM])
        
        # update addr_mode bits
        translated_words[self.FIRST_WORD] = trans_word1 | addr_mode << Assembler.ADDR_MODE_OFFSET       
        
        # not clr inc dec jmp jne jz
        if opcode_type == Assembler.ONE_PARAM_TYPE:                                
            self.handle_1_param_type(translated_words, clean_sec_arg)
        
        # mov cmp add sub lea xor or rol
        elif opcode_type == Assembler.TWO_PARAMS_TYPE:                              
            self.handle_2_param_type(translated_words, words[Assembler.FIRST_PARAM].rstrip(Assembler.REGISTER_SUFFIX), clean_sec_arg)
        
    def translate_line(self, asm_line):
        """ 
        Converts an assembly code line to it's binary representation.
        
        :param asm_line: A string represents the assembly code line
        :returns: The binary representation of the assembly line.
        :rtype: str
        """
        self.current_line_idx += 1
        unlabeled_asm_line = self.handle_label(asm_line)

        translated_words = [Assembler.EMPTY_WORD, None]
        # Section line check and translation
        if self.section_handler(unlabeled_asm_line, translated_words):
            return bytearray(translated_words[self.FIRST_WORD])

        # Remove spaces from indirect expression, if any.
        code, *indirect = unlabeled_asm_line.split(Assembler.INDIRECT_PREFIX)
        if indirect:
            unlabeled_asm_line = code + Assembler.INDIRECT_PREFIX + indirect.pop().replace(Assembler.SPACE, "")

        words = unlabeled_asm_line.split()
        
        # update opcode bits
        bin_opcode, opcode_type = Assembler.OPCODES.get(words[Assembler.OPCODE])
        translated_words[Assembler.FIRST_WORD] = Assembler.EMPTY_WORD | bin_opcode << Assembler.OPCODE_OFFSET                   
        
        if len(words[Assembler.FIRST_PARAM:]) > opcode_type:
            raise Assembler.TooManyParamsException(asm_line)
        try:
            self.handle_by_opcode_type(words, opcode_type, translated_words) 
        except Assembler.NotRegisterArgumentException as e:
            e.code_line = asm_line
            raise

        if translated_words[Assembler.SECOND_WORD] is not None:
            return bytearray().join([tran_word.to_bytes(Assembler.NUM_BYTES, byteorder=Assembler.BIG_ENDIAN) for tran_word in translated_words])
        return bytearray(translated_words[Assembler.FIRST_WORD].to_bytes(Assembler.NUM_BYTES, byteorder=Assembler.BIG_ENDIAN))

    def clean_comments(self, asm_lines):
        """ 
        Removes the comments (if exists) in each assembly code line.
        
        :param asm_lines: A list of extracted assembly lines.
        :returns: A comments-cleaned version of the assembly lines
        :rtype: List of strings
        """
        for index, line in enumerate(asm_lines):
            line = line.strip()
            
            # Blank lines or Comment lines
            if line == '' or line.startswith(Assembler.COMMENT_PREFIX):
                asm_lines[index] = None
            else:
                # Inline comments
                code, *comment = line.split(Assembler.COMMENT_PREFIX, maxsplit=1)
                asm_lines[index] = code.strip()
        
        return [line for line in asm_lines if line is not None]

    def first_step(self, assembly_lines):
        """ 
        Performs the first step in the assembling process. It consist of translation
        of the code lines (except for the usages of labels), and storage of labels and their addresses.
        
        :param assembly_lines: A list of assembly code lines strings.
        :returns: The partially-translated lines.
        :rtype: list of bytearrays
        """
        cleaned_lines = self.clean_comments(assembly_lines)
        semi_trans_lines = [self.translate_line(line) for line in cleaned_lines]
        return semi_trans_lines

    def second_step(self, semi_trans_lines):
        """ 
        Performs the second step in the assembling process. It resolves the correct
        address value of a label and evaluates expressions of which it contained in them.
        
        :param semi_trans_lines: A list of partially-translated lines.
        :returns: The completely translated lines
        :rtype: list of bytearrays
        """
        for line_num in self.untranslated_exps:
            eval_expr = eval(self.untranslated_exps[line_num], self.sym_tbl)
            semi_trans_lines[line_num].extend(eval_expr.to_bytes(Assembler.NUM_BYTES, byteorder=Assembler.BIG_ENDIAN))
        return semi_trans_lines

    def assemble_code(self, assembly_lines):
         """ 
        Performes the whole assembling process.
        
        :param assembly_lines: A list of the extracted assembly lines, as strings.
        :returns: The completely translated lines to binary bytes.
        :rtype: list of bytearrays
        """
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

    # Extract lines
    with open(args.input, STR_R_FORMAT) as origin_file:
        all_lines = origin_file.readlines()

    assembled_code_string = asm.assemble_code(all_lines)
    
    # Extract to binary file
    with open(args.output, BYTES_W_FORMAT) as bin_out:
        for line_bytes in assembled_code_string:
            bin_out.write(line_bytes)

    print("Assembling Done.")
