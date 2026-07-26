# Samsung Shannon Baseband RTOS Analysis

Reverse-engineering notes and research tools documenting the RTOS architecture of Samsung Shannon baseband firmware.
This project focuses on reconstructing the firmware startup process, task management, scheduling, interrupt handling, and message-based inter-task communication through static firmware analysis.

> The English documentation in this repository was translated from the original Korean version with the assistance of AI. For the original Korean articles and additional context, visit haehet.tistory.com.
---


## Target Firmware

| Field                | Value               |
| -------------------- | ------------------- |
| Device               | Samsung Galaxy S10  |
| Model                | SM-G973N            |
| SoC                  | Samsung Exynos 9820 |
| Baseband             | Samsung Shannon     |
| AP firmware          | G973NKSU7HWA1       |
| CP firmware          | G973NKOU7HVL3       |
| Android version      | Android 12          |
| Security patch level | January 2023        |
| Region               | South Korea         |

No proprietary firmware binaries are included in this repository.

---

## Research Scope

The following components were reconstructed:

* Firmware image layout
* BOOT-to-MAIN execution flow
* MAIN early initialization
* MainTask creation
* PAL runtime initialization
* Static task creation
* Task scheduling and context switching
* IRQ context saving and restoration
* Static task descriptor table
* PAL message subsystem initialization
* Queue-based task IPC
* Blocking message reception
* Receiver task wake-up
* Priority-based preemption
* Static message entity descriptor table

---

## Documentation

### Part I. Firmware Startup

1. Firmware Layout
2. Boot Process
3. MAIN Early Initialization

### Part II. PAL Runtime Architecture

4. RTOS Bootstrap and MainTask Execution
5. Task Scheduling and Context Switching
6. IRQ Handling and Context Restoration
7. Task Descriptor Table
8. PAL Message System and Task IPC

---

## Reconstructed Runtime Flow

```text
Firmware BOOT
    ↓
MAIN image entry
    ↓
Early hardware and runtime initialization
    ↓
MainTask creation
    ↓
PAL subsystem initialization
    ↓
Static task creation
    ↓
Task scheduling
    ↓
Context switching
    ↓
IRQ dispatch
    ↓
Context restoration
    ↓
Message entity initialization
    ↓
Queue-based task IPC
```

---

## Tools

The repository includes scripts used to extract reconstructed firmware structures.

* Static task descriptor extractor
* Static message entity extractor

Firmware images, Ghidra projects, and proprietary Samsung files are not distributed.

---

## Repository Structure

```text
shannon-baseband-analysis/
├── README.md
├── docs/
│   ├── part-1-firmware-startup/
│   └── part-2-pal-runtime/
├── scripts/
├── data/
└── assets/
```

---

## Project Status

The analysis currently covers the Shannon firmware execution flow from early startup through task creation, scheduling, interrupt handling, and task-level message delivery.

This repository is limited to documenting the baseband RTOS architecture and its internal task communication mechanisms.

---

## Disclaimer

This repository is intended solely for security research, education, and technical documentation.

It does not include proprietary firmware binaries or instructions for interfering with public cellular networks. Any experiments should be conducted only with legally obtained devices and isolated test environments.
