#pragma once

typedef unsigned int size_t;
typedef unsigned int uintptr_t;


#define read_csr(reg) ({ unsigned long __tmp; \
  asm volatile ("csrr %0, " #reg : "=r"(__tmp)); \
  __tmp; })


inline void memory_barrier() {
    asm volatile ("fence");
}


#if (__riscv_xlen == 32)

inline uint64_t read8b(uintptr_t addr) {
    uintptr_t addr_lower = addr;
    uintptr_t addr_upper = addr + 4;
    uint64_t res_lower;
    uint64_t res_upper;
    asm volatile (
        "lw %0, (%1)"
        : "=r"(res_upper)
        : "r"(addr_upper)
    );
    asm volatile (
        "lw %0, (%1)"
        : "=r"(res_lower)
        : "r"(addr_lower)
    );
    return ((res_upper<<32) | res_lower);
}

inline void write8b(uintptr_t addr, uint64_t val) {
    uint32_t val_lower = val & 0xFFFFFFFF;
    uint32_t val_upper = val >> 32;
    uintptr_t addr_lower = addr;
    uintptr_t addr_upper = addr + 4;
    asm volatile (
        "sw %0, (%1)"
        : : "r"(val_upper), "r"(addr_upper)
    );
    asm volatile (
        "sw %0, (%1)"
        : : "r"(val_lower), "r"(addr_lower)
    );
}

inline uint32_t rdcycle() {
    uint32_t res;
    asm volatile (
        "rdcycle %0"
        : "=r"(res)
    );
    return res;
}

#elif (__riscv_xlen == 64)

inline uint64_t read8b(uintptr_t addr) {
    uint64_t res;
    asm volatile (
        "ld %0, (%1)"
        : "=r"(res)
        : "r"(addr)
    );
    return res;
}

inline void write8b(uintptr_t addr, uint64_t val) {
    asm volatile (
        "sd %0, (%1)"
        : : "r"(val), "r"(addr)
    );
}

#ifndef rdcycle
    #define rdcycle() read_csr(mcycle)
#endif

#endif
