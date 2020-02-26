
RISCV_ARCH ?= rv32

ifeq ($(RISCV_ARCH), rv32)
RISCV_GNU_TOOLCHAIN_INSTALL_PREFIX=/opt/software/riscv32i
TOOLCHAIN_PREFIX = $(RISCV_GNU_TOOLCHAIN_INSTALL_PREFIX)/bin/riscv32-unknown-elf-
else
ifeq ($(RISCV_ARCH), rv64)
RISCV_GNU_TOOLCHAIN_INSTALL_PREFIX=/opt/software/riscv64
TOOLCHAIN_PREFIX = $(RISCV_GNU_TOOLCHAIN_INSTALL_PREFIX)/bin/riscv64-unknown-elf-
endif
endif



TCU_TEST_PATH = ../../../test/
TC_SOURCE_PATH = src/
#TC_SOURCE_PATH = $(TCU_TEST_PATH)
BITFILES_PATH = ../../bitfiles/

SCRIPTS_PATH = ../../scripts/
VPATH        = ${TC_SOURCE_PATH} ${TCU_TEST_PATH}hw

CPPFLAGS     += -I$(TCU_TEST_PATH) -D__hw__ -D__riscv__
CFLAGS       += -I$(TCU_TEST_PATH) -D__hw__ -D__riscv__
CPPFLAGS     += -Wall -O2
CFLAGS       += -Wall -O2
LDFLAGS      ?= -O2 -march=rv32i -Wl,-Bstatic,-T,$(SCRIPTS_PATH)riscv.ld,-Map,mem.map,--strip-debug


CPP          := $(TOOLCHAIN_PREFIX)g++
CC           := $(TOOLCHAIN_PREFIX)gcc

CPPSOURCES   += $(notdir $(wildcard ${TC_SOURCE_PATH}*.cc) $(wildcard ${TCU_TEST_PATH}hw/*.cc))
CSOURCES     += $(notdir $(wildcard ${TC_SOURCE_PATH}*.c) $(wildcard ${TCU_TEST_PATH}hw/*.c))
CPPOBJECTS   := $(notdir $(CPPSOURCES:.cc=.lo))
COBJECTS     := $(notdir $(CSOURCES:.c=.o))


#--------------------------------------------


APPLICATION  ?= main

%.o: %.c
	${CC} ${CFLAGS} -c -o $@ $<

%.lo: %.cc
	${CPP} ${CPPFLAGS} -c -o $@ $<


.PHONY: compile
ifeq ($(RISCV_ARCH), $(filter $(RISCV_ARCH), rv32 rv64))
compile: ${APPLICATION}
else
compile:
	@echo "RISC-V arch not supported:" $(RISCV_ARCH)
endif


${APPLICATION}: ${CPPOBJECTS} ${COBJECTS}
	${CPP} ${LDFLAGS} ${CPPOBJECTS} ${COBJECTS} -o $@

	$(TOOLCHAIN_PREFIX)objdump -D $@ > $@.dump
	$(RISCV_GNU_TOOLCHAIN_INSTALL_PREFIX)/bin/elf2hex 8 65536 $@ > tmp_$@.hex
	python3 $(SCRIPTS_PATH)reducehex.py tmp_$@.hex $@.hex
	rm tmp_$@.hex



.PHONY: clean
clean:
	rm -f ${CPPOBJECTS} ${COBJECTS} ${APPLICATION} ${APPLICATION}.hex ${APPLICATION}.dump mem.map ovpsim.log




#--------------------------------------------
PYTHON := python3

.PHONY: run
run:
	$(PYTHON) testcase.py



#--------------------------------------------
OVPSIM_PATH := /opt/software/riscv-ovpsim/bin/Linux64/

ifeq ($(RISCV_ARCH), rv32)
OVPSIM_VARIANT := RV32I
else
OVPSIM_VARIANT := RV64I
endif

.PHONY: simulate
simulate:
	$(OVPSIM_PATH)riscvOVPsim.exe --program $(APPLICATION) --variant $(OVPSIM_VARIANT) --logfile ovpsim.log



#--------------------------------------------

BITFILE ?= $(BITFILES_PATH)fpga_top.bit

.PHONY: program-fpga
program-fpga:
	vivado -mode batch -source $(SCRIPTS_PATH)program_fpga.tcl -tclargs $(BITFILE)

