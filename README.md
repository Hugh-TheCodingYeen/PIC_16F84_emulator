# PIC16F84 Microcontroller Emulator (Educational Pet-Project)

> ⚠️ **Important Disclaimer**
> **This is an experimental, educational pet-project.** 
> The code is written strictly for learning purposes, to understand the inner workings of the PIC16 architecture, instruction sets, and low-level programming. 
> 
> **Please DO NOT use this code in any serious, production, or commercial work.** It may contain bugs, incomplete features, and architectural simplifications. You have been warned!

## 📖 About
This repository is currently a work-in-progress. The ultimate goal is to build a functional software emulator for the **PIC16F84** microcontroller. 

At the current stage, the repository contains the `asm.py` module, which provides an Assembler and Disassembler for the PIC16 Instruction Set Architecture (14-bit instructions).

### Current Features (`asm.py`)
* **Assembler (`asm`):** Converts PIC16 assembly text into a list of 14-bit integer machine code words.
* **Disassembler (`disasm`):** Converts a list of 14-bit integers back into readable assembly code.
* **Table-Driven Design:** Instruction encoding and decoding are implemented using a table method with bitwise masks (`format_table`), rather than hardcoding conditional branches for every single instruction.

## 🚀 Roadmap
- [x] PIC16 Assembler/Disassembler
- [ ] Implementation of CPU registers (W, STATUS, PC, etc.)
- [ ] Memory management (Program memory, Data memory, EEPROM)
- [ ] Execution engine (Fetch-Decode-Execute cycle)
- [ ] I/O ports and peripherals emulation (Ports A & B, TMR0)

## 💻 Usage Example
You can easily test the assembler and disassembler in your Python environment:

```python
from asm import asm, disasm

# Assembly code
code = "movwf 0x05\naddwf 0x05, F"

# Assemble the code into memory
memory = asm(code, mem=[], offset=0)

# Disassemble the memory back to text
print(disasm(memory, offset=0, size=len(memory)))
```

## 📜 License
This project is distributed under the **BSD-3-Clause-No-Nuclear-Warranty** license.

## 👤 Author
* **Author:** Hugh The Coding Yeen
* **Project:** PIC16 ISA Assembler/Disassembler
* **Year:** 2026
* **Version:** 1.0.1
