import sys, os, re

from enum import Enum
from pprint import pprint

class ParsingError(Exception):
    def __init__(self, msg):
        self.msg = msg

class Instruction(object):

    D_BITS = {
        'null': '000',
        'M': '001',
        'D': '010',
        'MD': '011',
        'A': '100',
        'AM': '101',
        'AD': '110',
        'AMD': '111'
    }

    C_BITS = {
        'null': '101010',
        '0': '101010',

        '1': '111111',

        '-1': '111010',

        'D': '001100',

        'A': '110000',
        'M': '110000a',

        '!D': '001101',

        '!A': '110001',
        '!M': '110001a',

        '-D': '001111',

        '-A': '110011',
        '-M': '110011a',

        'D+1': '011111',

        'A+1': '110111',
        'M+1': '110111a',

        'D-1': '001110',

        'A-1': '110010',
        'M-1': '110010a',

        'D+A': '000010',
        'D+M': '000010a',

        'D-A': '010011',
        'D-M': '010011a',

        'A-D': '000111',
        'M-D': '000111a',

        'D&M': '000000a',
        'D&A': '000000',

        'D|A': '010101',
        'D|M': '010101a'
    }

    J_BITS = {
        'null': '000',
        'JGT': '001',
        'JEQ': '010',
        'JGE': '011',
        'JLE': '100',
        'JNE': '101',
        'JLT': '110',
        'JMP': '111'
    }

    def __init__(self, parser, line):
        self.parser = parser

        self.index = self.parser.nextAvailableIndex
        self.line = re.sub(r"\s+", '', line.split('//')[0])
        self.originalLine = line

        self.valid = False
        self.bin = ''

    def parse(self):

        #print('Original: {}\nCleaned: {}'.format(self.originalLine, self.line))

        if len(self.line) == 0:
            return

        if self.line[0] == '@':
            tokenVal = None

            token = self.line[1:]

            if token.isdigit():
                tokenVal = int(token)
                if tokenVal < 0: tokenVal = None
            elif token.isalpha():
                tokenVal = self.parser.parse_symbol(token)
            
            if tokenVal is None:
                raise ParsingError('Attempted to set A-register to something other than a symbol or positive integer: {}'.format(token))
            else:
                self.valid = True

            self.bin = '0{:015b}'.format(tokenVal)
        elif self.line[0] == '(' and self.line[-1:] == ')':
            token = self.line[1:-1]

            if token.isalpha():
                self.parser.symbols[token] = self.parser.nextAvailableIndex
        else:
            #dest = comp ; jump
            eqIndex = self.line.find('=')
            semiIndex = self.line.find(';')

            destToken = None
            compToken = None
            jumpToken = None

            eqSplits = self.line.split('=')
            if len(eqSplits) > 1:
                destToken = eqSplits[0]
                semiSplits = eqSplits[-1].split(';')
                if len(semiSplits) > 1:
                    compToken = semiSplits[0]
                    jumpToken = semiSplits[-1]
                else:
                    compToken = eqSplits[-1]
                    jumpToken = None
            else:
                destToken = None
                semiSplits = self.line.split(';')
                if len(semiSplits) > 1:
                    compToken = semiSplits[0]
                    jumpToken = semiSplits[-1]
                else:
                    compToken = eqSplits[-1]
                    jumpToken = None

            if destToken is None and compToken is None and jumpToken is None: return
            self.valid = True

            #print('Original: {}\nCleaned: {}'.format(self.originalLine, self.line))
            #print('Dest: {}, Comp: {}, Jump: {}'.format(destToken, compToken, jumpToken))

            if destToken is None: destToken = 'null'
            if compToken is None: compToken = 'null'
            if jumpToken is None: jumpToken = 'null'

            destBits = Instruction.D_BITS[destToken]
            compBits = Instruction.C_BITS[compToken]
            jumpBits = Instruction.J_BITS[jumpToken]

            aBit = str(-6+len(compBits))

            #print('Dest= {}, {} - Comp= {}, {}, - Jump= {}, {}'.format(destToken, destBits, compToken, compBits, jumpToken, jumpBits))

            self.bin = '111{}{}{}{}'.format(aBit, compBits[0:6], destBits, jumpBits)


class Parser(object):

    @staticmethod
    def default_symbols():
        return {
            'R0'        : 0,
            'R1'        : 1,
            'R2'        : 2,
            'R3'        : 3,
            'R4'        : 4,
            'R5'        : 5,
            'R6'        : 6,
            'R7'        : 7,
            'R8'        : 8,
            'R9'        : 9,
            'R10'       : 10,
            'R11'       : 11,
            'R12'       : 12,
            'R13'       : 13,
            'R14'       : 14,
            'R15'       : 15,

            'SCREEN'    : 16384,
            'KBD'       : 24576,

            'SP'        : 0,
            'LCL'       : 1,
            'ARG'       : 2,
            'THIS'      : 3,
            'THAT'      : 4
        }

    @property
    def nextAvailableIndex(self):
        return len(self.instructions)

    def __init__(self):
        self.symbols = Parser.default_symbols()
        self.nextVarAddress = 16
        self.instructions = []

    def parse_file(self, path):
        self.symbols = Parser.default_symbols()
        self.nextVarAddress = 16
        self.instructions = []

        with open(path) as f:

            for line in f.readlines():
                ins = Instruction(self, line)

                try:
                    ins.parse()
                except ParsingError as ex:
                    print('Error parsing \'{}\': {}'.format(line, ex.msg))
                else:
                    if ins.valid:
                        self.instructions.append(ins)
                        #print('Instruction {}: 0x{}\n\tLine #{}: {}\n'.format(ins.index, ins.bin, lineNum,
                        #                                                    line[:64] + ('..' if len(line) > 60 else '')))


    def parse_symbol(self, token):
        val = None

        try:
            val = self.symbols[token]
        except KeyError:
            val = self.nextVarAddress
            self.symbols[token] = val
            self.nextVarAddress += 1
        finally:
            return val

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Invalid number of command-line arguments: Accepts a single path to the file that needs to be assembled')
        sys.exit(-1)

    path = sys.argv[1]
    asmFileName = os.path.basename(path)
    genericFileName = os.path.splitext(asmFileName)[0]
    hackFilePath = str(path).replace('.asm', '.hack')

    print('Beginning assembly of file \'{}\', will create \'{}.hack\' if successful\n'.format(asmFileName, genericFileName))

    p = Parser()
    p.parse_file(path)

    print('User-Defined Symbols and Labels\n')
    customSymbols = {}
    for s in p.symbols.keys():
        if s in Parser.default_symbols(): continue
        print('\'{0}\': {1}\t\t\t->\t{1:016b}'.format(s, p.symbols[s]))
    print('\nAssembled Machine Code\n')

    with open(hackFilePath, mode='w') as f:
        for ins in p.instructions:
            print('Instruction {}:\t{}\t\t->\t{}'.format(ins.index, ins.line[:48] + ('..' if len(ins.line) > 45 else ''), ins.bin))
            f.write(ins.bin)