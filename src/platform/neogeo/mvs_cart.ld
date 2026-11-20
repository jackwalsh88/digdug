/*
 * Super Dig Dug — Neo Geo MVS 68000 Linker Script
 * P-ROM: $000000 .. $07FFFF (512 KiB)
 * User Work RAM: $100000 .. $10EFFF (60 KiB below BIOS reserved area $10F300)
 */
OUTPUT_ARCH(m68k)
ENTRY(_start)

MEMORY
{
    ROM (rx)  : ORIGIN = 0x00000000, LENGTH = 512K
    RAM (rwx) : ORIGIN = 0x00100000, LENGTH = 56K
}

SECTIONS
{
    .text 0x00000000 :
    {
        KEEP(*(.vectors))
        *(.text .text.*)
        *(.rodata .rodata.*)
        . = ALIGN(4);
        _etext = .;
    } > ROM

    .data : AT(_etext)
    {
        _sdata = .;
        *(.data .data.*)
        . = ALIGN(4);
        _edata = .;
    } > RAM

    .bss (NOLOAD) :
    {
        _sbss = .;
        *(.bss .bss.*)
        *(COMMON)
        . = ALIGN(4);
        _ebss = .;
    } > RAM
}
