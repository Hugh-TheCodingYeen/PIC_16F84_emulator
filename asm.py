# ============================================================================
# Author: Hugh-TheCodingYeen
# Project: PIC16 ISA Assembler/Disassembler
# Year: 2026
# Version: 1.0.1
# License: BSD-3-Clause-No-Nuclear-Warranty
# ============================================================================

# ============================================================================
# Глобальный комментарий
# ============================================================================
"""
Модуль предоставляет интерфейсы для ассемблирования и дизассемблирования 
машинного кода архитектуры PIC16 (14-битные инструкции).

Основные функции:
- asm():  Преобразует текст ассемблера в список 14-битных целых чисел (память).
- disasm(): Преобразует список целых чисел обратно в читаемый ассемблерный код.

Использование:
    code = "movwf 0x05\naddwf 0x05, F"
    memory = asm(code, mem=[], offset=0)
    print(disasm(memory, offset=0, size=len(memory)))

Примечание к алгоритму:
    Кодирование и декодирование инструкций реализовано через табличный метод 
    с использованием побитовых масок (format_table), а не через жестко 
    зашитые условные ветвления для каждой инструкции.
"""

# ============================================================================
# Константы настройки
# ============================================================================
# Параметры по умолчанию, вынесенные из аргументов функций для удобства 
# глобальной настройки и изменения без поиска по коду.

DEFAULT_MEM_SIZE = 25         # Размер памяти/кол-во инструкций по умолчанию
DEFAULT_FILL_ASM = 0x3FFF     # Значение-заглушка для пустой памяти (NOP в PIC16)
DEFAULT_FILL_DISASM = 'nop'   # Строковая заглушка для дизассемблера

# ============================================================================
# Зависимости
# ============================================================================
# В данном модуле внешние зависимости отсутствуют.
# Если в будущем потребуются регулярные выражения или работа с файлами, 
# импорты следует размещать здесь:
# import re
# import os

# ============================================================================
# БЛОК 1: АТОМАРНЫЕ ФУНКЦИИ ПРЕОБРАЗОВАНИЯ ТИПОВ (*_d)
# ============================================================================
# Эти функции не зависят от других функций файла и описывают 
# базовое преобразование бита направления (d) для архитектуры.

# ФУНКЦИЯ ДЕКОДИРОВАНИЯ НАПРАВЛЕНИЯ

def decode_d(d):
  return 'f' if d else 'W'

# ФУНКЦИЯ КОДИРОВАНИЯ НАПРАВЛЕНИЯ

def encode_d(d):
  if d in ('f', 'F', '1', 1, True) : return 1
  if d in ('W', 'w', '0', 0, False): return 0
  raise Exception("Wrong direction")

# ============================================================================
# БЛОК 2: СТРУКТУРЫ ДАННЫХ (ОПИСАНИЕ ЯЗЫКА АССЕМБЛЕРА)
# ============================================================================
# Определение мнемоник, опкодов и форматов инструкций.
# Эти структуры зависят от функций *_d (используют их как постпроцессоры).

# СЛОВАРЬ МНЕМОНИКИ

opcode_list = (
  #	 MNEMONIC    OPCODE               OPMASK             FORMAT_ID
    ('nop'     , 0b00_0000_0000_0000, 0b11_1111_1001_1111, 5),
    ('return'  , 0b00_0000_0000_1000, 0b11_1111_1111_1111, 5),
    ('retfie'  , 0b00_0000_0000_1001, 0b11_1111_1111_1111, 5),
    ('sleep'   , 0b00_0000_0110_0011, 0b11_1111_1111_1111, 5),
    ('clrwdt'  , 0b00_0000_0110_0100, 0b11_1111_1111_1111, 5),
    ('movwf'   , 0b00_0000_1000_0000, 0b11_1111_1000_0000, 4),
    ('clrw'    , 0b00_0001_0000_0000, 0b11_1111_1000_0000, 5),
    ('clrf'    , 0b00_0001_1000_0000, 0b11_1111_1000_0000, 4),
    ('subwf'   , 0b00_0010_0000_0000, 0b11_1111_0000_0000, 0),
    ('decf'    , 0b00_0011_0000_0000, 0b11_1111_0000_0000, 0),
    ('iorwf'   , 0b00_0100_0000_0000, 0b11_1111_0000_0000, 0),
    ('andwf'   , 0b00_0101_0000_0000, 0b11_1111_0000_0000, 0),
    ('xorwf'   , 0b00_0110_0000_0000, 0b11_1111_0000_0000, 0),
    ('addwf'   , 0b00_0111_0000_0000, 0b11_1111_0000_0000, 0),
    ('movf'    , 0b00_1000_0000_0000, 0b11_1111_0000_0000, 0),
    ('comf'    , 0b00_1001_0000_0000, 0b11_1111_0000_0000, 0),
    ('incf'    , 0b00_1010_0000_0000, 0b11_1111_0000_0000, 0),
    ('decfsz'  , 0b00_1011_0000_0000, 0b11_1111_0000_0000, 0),
    ('rrf'     , 0b00_1100_0000_0000, 0b11_1111_0000_0000, 0),
    ('rlf'     , 0b00_1101_0000_0000, 0b11_1111_0000_0000, 0),
    ('swapf'   , 0b00_1110_0000_0000, 0b11_1111_0000_0000, 0),
    ('incfsz'  , 0b00_1111_0000_0000, 0b11_1111_0000_0000, 0),
    ('bcf'     , 0b01_0000_0000_0000, 0b11_1100_0000_0000, 1),
    ('bsf'     , 0b01_0100_0000_0000, 0b11_1100_0000_0000, 1),
    ('btfsc'   , 0b01_1000_0000_0000, 0b11_1100_0000_0000, 1),
    ('btfss'   , 0b01_1100_0000_0000, 0b11_1100_0000_0000, 1),
    ('call'    , 0b10_0000_0000_0000, 0b11_1000_0000_0000, 2),
    ('goto'    , 0b10_1000_0000_0000, 0b11_1000_0000_0000, 2),
    ('movlw'   , 0b11_0000_0000_0000, 0b11_1100_0000_0000, 3),
    ('retlw'   , 0b11_0100_0000_0000, 0b11_1100_0000_0000, 3),
    ('iorlw'   , 0b11_1000_0000_0000, 0b11_1111_0000_0000, 3),
    ('andlw'   , 0b11_1001_0000_0000, 0b11_1111_0000_0000, 3),
    ('xorlw'   , 0b11_1010_0000_0000, 0b11_1111_0000_0000, 3),
    ('sublw'   , 0b11_1100_0000_0000, 0b11_1110_0000_0000, 3),
    ('addlw'   , 0b11_1110_0000_0000, 0b11_1110_0000_0000, 3),

)

# СПИСОК ФОРМАТОВ
# Описание кортежей: (argmask, argshift, postproc_decode, postproc_encode)
# Форматы используют функции encode_d/decode_d как постпроцессоры

format_table = (
    ( (0b00_0000_0111_1111, 0, None, None), (0b00_0000_1000_0000, 7, decode_d, encode_d), ),    #file_dir
    ( (0b00_0000_0111_1111, 0, None, None), (0b00_0011_1000_0000, 7, None, None), ),            #file_bit
    ( (0b00_0111_1111_1111, 0, None, None), ),                                                  #liter_11
    ( (0b00_0000_1111_1111, 0, None, None), ),                                                  #liter_08
    ( (0b00_0000_0111_1111, 0, None, None), ),                                                  #file_d_1
    ( ),                                                                                        #w_o_args
)

# Словарь для быстрого поиска опкода по имени мнемоники

mnemonics = {}

for mnemonic, opcode, opmask, format_id in opcode_list:
  mnemonics[mnemonic] = (opcode,opmask,format_id)

# ============================================================================
# БЛОК 3: ФУНКЦИИ КОДИРОВАНИЯ/ДЕКОДИРОВАНИЯ ИНСТРУКЦИЙ
# ============================================================================
# Эти функции работают с одной инструкцией. Они зависят от структур 
# (opcode_list, format_table, mnemonics) и атомарных функций (*_d).

# ФУНЦИЯ АССЕМБЛИРОВАНИЯ ОДНОЙ ИНСТРУКЦИИ

def encode_instruction(line):

  mnem, *args = line.replace(","," ").split()
  mnem = mnem.strip().lower()

  if not mnem in mnemonics: raise Exception("Wrong mnemonic")

  opcode, opmask, format_id = mnemonics[mnem]
  field_buffer = format_table[format_id]

  if opcode in (0b_00_0000_1000_0000, 0b_00_0001_1000_0000) and len(args) == 2:
    if encode_d(args.pop().strip()) != 1: raise Exception(f"{mnem} direction must be 'f'")

  if len(args) != len(field_buffer): raise Exception(f"Wrong number of arguments for {mnem}")

  for i in range(len(field_buffer)):
    arg = args[i]
    argfield, argshift, _, postproc = field_buffer[i]
    val = arg
    if postproc:
      val = postproc(val)
    val = argfield & (int(val) << argshift)
    opcode |= val

  return opcode

# ФУНКЦИЯ ДИЗАССЕМБЛИРОВАНИЯ ОДНОЙ ИНСТРУКЦИИ

def decode_instruction(code):
  if not isinstance(code, int): raise Exception("Instruction must be an integer")
  if code >> 14 : raise Exception("Instruction must be 14 bit long")

  mnem = None
  op_buffer = []
  operands = []

  for mnemonic, opcode, opmask, format_id in opcode_list:
    if code & opmask == opcode:
      mnem = mnemonic
      op_buffer = format_table[format_id]
      break
  else: raise Exception("Wrong instruction")

  for argmask, argshift, postproc, _ in op_buffer:
    val = (code & argmask) >> argshift
    if postproc:
      val = postproc(val)
    operands.append(val)

  return mnem, operands

# ============================================================================
# БЛОК 4: ВЫСОКОУРОВНЕВЫЕ ИНТЕРФЕЙСЫ (АСМ/ДИЗАСМ)
# ============================================================================
# Самые общие функции, зависящие от всех предыдущих блоков. 
# Они обрабатывают массивы данных, вызывая функции кодирования/
# декодирования отдельных инструкций.

# ИНТЕРФЕЙС АССЕМБЛЕРА

def asm(text, mem=None, offset=0, size=DEFAULT_MEM_SIZE, fill=DEFAULT_FILL_ASM):

  e_asm = {
      'text_err':"Wrong input data, expected string",
      'mem_err':"Wrong memory data, expected None or list",
      'offset_err':"Wrong offset data, expected integer",
      'size_err':"Wrong size data, expected None or integer"
  }

  if not isinstance(text, str):
    raise Exception (e_asm.get('text_err'))
  if mem == None:
    mem = []
  elif not isinstance(mem, list):
    raise Exception (e_asm.get('mem_err'))
  if not isinstance (offset, int):
    raise Exception (e_asm.get('offset_err'))
  if not size == None and not isinstance(size, int):
    raise Exception (e_asm.get('size_err'))

  text_asm = [string.strip() for string in text.splitlines() if string.strip()]

  cursor = offset
  end_point = offset + (min(size, len(text_asm)) if size else len(text_asm))

  if offset >= len(mem):
    mem_fill = [fill for _ in range(offset - len(mem))]
    mem.extend(mem_fill)

  for instr in text_asm:
    if cursor >= len(mem) and not cursor == end_point:
      mem.append(encode_instruction(instr))
      cursor = cursor + 1
    elif cursor < len(mem) and not cursor == end_point:
      mem[cursor] = encode_instruction(instr)
      cursor = cursor + 1
    elif cursor == end_point:
      break
  return mem

# ИНТЕРФЕЙС ДИЗАССЕМБЛЕРА

def disasm(mem, offset=0, size=DEFAULT_MEM_SIZE, fill=DEFAULT_FILL_DISASM):
  e_disasm = {
      'mem_empty':"Memory is empty!",
      'mem_err':"Wrong memory type, expected list",
      'offset_err':"Wrong offset type, expected integer",
      'size_err':"Wrong size type, expected None or integer"
  }

  if mem == None:
    raise Exception(e_disasm.get('mem_empty'))
  elif not isinstance(mem, list):
    raise Exception(e_disasm.get('mem_err'))
  if not isinstance(offset, int):
    raise Exception(e_disasm.get('offset_err'))
  if not size == None and not isinstance(size, int):
    raise Exception(e_disasm.get('size_err'))

  mem_slice = mem[offset:None if size is None else offset + size]
  str_list = []

  for i, instr in enumerate(mem_slice):
    mnem, operands = decode_instruction(instr)
    instr_str = f"{mnem}\t{', '.join(str(arg) for arg in operands)}".strip()
    address = offset + i
    str_list.append(f"{address:02X}:{instr:04X}\t{instr_str}")

  text = "\n".join(str_list)
  return text
