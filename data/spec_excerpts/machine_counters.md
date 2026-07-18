## §3.1.10 Hardware Performance Monitor

<!-- anchor: norm:m_mode_perf_monitoring -->
M-mode includes a basic hardware performance-monitoring facility.

<!-- anchor: norm:mcycle_op -->
The csr:mcycle[] CSR counts the number of clock cycles executed by the processor core on which the hart is running.

<!-- anchor: norm:minstret_op -->
The csr:minstret[] CSR counts the number of instructions the hart has retired.

<!-- anchor: norm:mcycle_minstret_sz -->
The csr:mcycle[] and csr:minstret[] registers have 64-bit precision on all RV32 and RV64 harts.

<!-- anchor: norm:mcycle_minstret_rst -->
The counter registers have an arbitrary value after the hart is reset, and can be written with a given value.

<!-- anchor: norm:mcycle_minstret_wr -->
Any CSR write takes effect after the writing instruction has otherwise completed.

<!-- anchor: norm:mcycle_shared -->
The csr:mcycle[] CSR may be shared between harts on the same core, in which case writes to csr:mcycle[] will be visible to those harts. The platform should provide a mechanism to indicate which harts share an csr:mcycle[] CSR.

<!-- anchor: norm:mhpmcounter_num -->
The hardware performance monitor includes 29 additional 64-bit event counters, csr:mhpmcounter3[]–csr:mhpmcounter31[].

<!-- anchor: norm:mhpmevent_sz_warl_op -->
The event selector CSRs, csr:mhpmevent3[]–csr:mhpmevent31[], are 64-bit *WARL* registers that control which event causes the corresponding counter to increment.

<!-- anchor: norm:mhpmevent_enc -->
The meaning of these events is defined by the platform, but event 0 is defined to mean "no event."

<!-- anchor: norm:mhpmcounter_mandatory -->
All counters should be implemented, but
<!-- anchor: norm:mhpmcounter_mhpmevent_rdonly0 -->
a legal implementation is to make both the counter and its corresponding event selector be read-only 0.

*Hardware performance monitor counters*
<!-- AsciiDoc include: include::images/bytefield/hpmevents.edn[] -->

<!-- anchor: norm:mhpmcounter_warl -->
The ``mhpmcounter``s are *WARL* registers that
<!-- anchor: norm:mhpmcounter_sz -->
support up to 64 bits of precision on RV32 and RV64.

When XLEN=32, reads of the csr:mcycle[], csr:minstret[], `mhpmcounter__n__`, and `mhpmevent__n__` CSRs return bits 31-0 of the corresponding register, and writes change only bits 31-0;

<!-- anchor: norm:mcycleh_minstreth_mhpmh_op -->
reads of the csr:mcycleh[], csr:minstreth[], `mhpmcounter__n__h`, and `mhpmevent__n__h` CSRs return bits 63-32 of the corresponding register, and writes change only bits 63-32.

<!-- anchor: norm:mhpmeventh_presence -->
The `mhpmevent__n__h` CSRs are provided only if the ext:sscofpmf[] extension is implemented.

---

## §3.1.11 Machine Counter-Enable (csr:mcounteren[]) Register

<!-- anchor: norm:mcounteren_sz -->
The counter-enable csr:mcounteren[] register is a 32-bit register that
<!-- anchor: norm:mcounteren_op -->
controls the availability of the hardware performance-monitoring counters to the next-lowest privileged mode.

*Counter-enable (csr:mcounteren[]) register*
<!-- AsciiDoc include: include::images/bytefield/counteren.edn[] -->

<!-- anchor: norm:mcounteren_inc_inaccessible -->
The settings in this register only control accessibility. The act of reading or writing this register does not affect the underlying counters, which continue to increment even when not accessible.

<!-- anchor: norm:mcounteren_clr_ill_inst_exc -->
When the csr::[cy], csr::[tm], csr::[ir], or HPM__n__ bit in the csr:mcounteren[] register is clear, attempts to read the csr:cycle[], csr:time[], csr:instret[], or `hpmcounter__n__` register while executing in S-mode or U-mode will cause an illegal-instruction exception.

<!-- anchor: norm:mcounteren_set_nxt_priv -->
When one of these bits is set, access to the corresponding register is permitted in the next implemented privilege mode (S-mode if implemented, otherwise U-mode).

NOTE:
The counter-enable bits support two common use cases with minimal hardware. For harts that do not need high-performance timers and counters, machine-mode software can trap accesses and implement all features in software. For harts that need high-performance timers and counters but are not concerned with obfuscating the underlying hardware counters, the counters can be directly exposed to lower privilege modes.

<!-- anchor: norm:mcounteren_tm_clr -->
In addition, when the csr:[tm] bit in the csr:mcounteren[] register is clear, attempts to access the csr:stimecmp[] or csr:vstimecmp[] register while executing in a mode less privileged than M will cause an illegal-instruction exception.

<!-- anchor: norm:mcounteren_tm_set -->
When this bit is set, access to the csr:stimecmp[] or csr:vstimecmp[] register is permitted in S-mode if implemented, and access to the csr:vstimecmp[] register (via csr:stimecmp[]) is permitted in VS-mode if implemented and not otherwise prevented by the csr::[tm] bit in csr:hcounteren[].

<!-- anchor: norm:cycle_instret_hpmcounter_op_rdonly -->
The csr:cycle[], csr:instret[], and `hpmcounter__n__` CSRs are read-only shadows of csr:mcycle[], csr:minstret[], and `mhpmcounter__n__`, respectively.

<!-- anchor: norm:time_op_rdonly -->
The csr:time[] CSR is a read-only shadow of the memory-mapped csr:mtime[] register.

Analogously,
<!-- anchor: norm:cycleh_instreth_hpmcounternh_op_rdonly -->
when XLEN=32, the csr:cycleh[], csr:instreth[] and `hpmcounter__n__h` CSRs are read-only shadows of csr:mcycleh[], csr:minstreth[] and `mhpmcounter__n__h`, respectively.

<!-- anchor: norm:timeh_op_rdonly -->
When XLEN=32, the csr:timeh[] CSR is a read-only shadow of the upper 32 bits of the memory-mapped csr:mtime[] register, while csr:time[] shadows only the lower 32 bits of csr:mtime[].

NOTE:
<!-- anchor: norm:time_csr_architectural_availability -->
Implementations can convert reads of the csr:time[] and csr:timeh[] CSRs into loads to the memory-mapped csr:mtime[] register, or emulate this functionality on behalf of less-privileged modes in M-mode software.

<!-- anchor: norm:mcounteren_flds_mandatory_warl -->
In harts with U-mode, the csr:mcounteren[] must be implemented, but all fields are *WARL* and
<!-- anchor: norm:mcounteren_flds_rdonly0 -->
may be read-only zero, indicating reads to the corresponding counter will cause an illegal-instruction exception when executing in a less-privileged mode.

<!-- anchor: norm:mcounteren_presence -->
In harts without U-mode, the csr:mcounteren[] register should not exist.

---

## §3.1.12 Machine Counter-Inhibit (csr:mcountinhibit[]) Register

*Counter-inhibit csr:mcountinhibit[] register*
<!-- AsciiDoc include: include::images/bytefield/counterinh.edn[] -->

<!-- anchor: norm:mcountinhibit_sz_warl_op1 -->
The counter-inhibit register csr:mcountinhibit[] is a 32-bit *WARL* register that controls which of the hardware performance-monitoring counters increment.

<!-- anchor: norm:mcountinhibit_only_inc -->
The settings in this register only control whether the counters increment; their accessibility is not affected by the setting of this register.

<!-- anchor: norm:mcountinhibit_op2 -->
When the csr::[cy], csr::[ir], or HPM__n__ bit in the csr:mcountinhibit[] register is clear, the csr:mcycle[], csr:minstret[], or `mhpmcounter__n__` register increments as usual. When the csr::[cy], csr::[ir], or HPM__n__ bit is set, the corresponding counter does not increment.

<!-- anchor: norm:mcountinhibit_cy_shared -->
The csr:mcycle[] CSR may be shared between harts on the same core, in which case the csr:mcountinhibit[cy] field is also shared between those harts, and so writes to csr:mcountinhibit[cy] will be visible to those harts.

<!-- anchor: norm:mcountinhibit_not_impl -->
If the csr:mcountinhibit[] register is not implemented, the implementation behaves as though the register were set to zero.

NOTE:
When the csr:mcycle[] and csr:minstret[] counters are not needed, it is desirable to conditionally inhibit them to reduce energy consumption. Providing a single CSR to inhibit all counters also allows the counters to be atomically sampled.

Because the csr:mtime[] counter can be shared between multiple cores, it cannot be inhibited with the csr:mcountinhibit[] mechanism.
