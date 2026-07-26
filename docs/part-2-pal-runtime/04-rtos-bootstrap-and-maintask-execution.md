## Main Function

Once C runtime initialization is complete, `Main()`, the C entry point of the firmware, is called. `Main()` configures the performance monitoring unit, initial hardware, and interrupt controller, prepares the internal RTOS state and system memory region, and creates `mainTask`, the first task.

```c
void Main(void)
{
  PMU_InitCounters();
  Pal_EarlyHardwareBringup();
  GIC_DistributorAndCpuInterfaceInit();
  thunk_FUN_4178de54(&DAT_04800c20);
  GetSysMemRegionBase();
  pal_CreateMainTask();

  do {
  } while (true);
}
```

First, `PMU_InitCounters()` checks the control registers of the ARM Performance Monitoring Unit (PMU) and enables the PMU and performance counters when necessary. It also configures the cycle counter and several event counters so that they can be used and initializes the counter values.

```c
undefined4 PMU_InitCounters(void)
{
  uint value;

  value = coprocessor_movefromRt(0xf, 0, 0, in_cr9, in_cr12);

  if ((value & 1) == 0) {
    coprocessor_moveto(0xf, 0, 0, value | 7, in_cr9, in_cr12);
  }

  value = coprocessor_movefromRt(0xf, 0, 1, in_cr9, in_cr12);

  if ((~value & 0x80000001) != 0) {
    coprocessor_moveto(
        0xf, 0, 1,
        value & 0xfffffff7 | 0x80000001,
        in_cr9, in_cr12
    );
  }

  coprocessor_moveto(0xf, 0, 0, 0, in_cr9, in_cr13);
  return 0;
}
```

`Pal_EarlyHardwareBringup()` configures the initial hardware state required before the PAL runtime begins operating. Afterward, `GIC_DistributorAndCpuInterfaceInit()` initializes the Distributor and CPU Interface of the ARM Generic Interrupt Controller, establishing the foundation for interrupt handling. Finally, `GetSysMemRegionBase()` returns the start address of the system memory region that will be used by the RTOS, and this value is passed through `r0` to the subsequently called `pal_CreateMainTask()`.

---

## pal_CreateMainTask

`pal_CreateMainTask()` constructs the system memory pools used by the RTOS, prepares the stack region of `mainTask`, and then calls the actual task creation function.

```c
void pal_CreateMainTask(int param_1)
{
  int ret;
  int extraout_r0;
  uint uVar1;

  uVar1 = param_1 + 0x1fU & 0xffffffe0;

  ret = GetSysMemRegionSize();
  MemClearZero(uVar1, ret - 0x20);

  ret = GetSysMemRegionSize();
  ret = MemoryPool_Init(
      &DAT_4356a8d0,
      "sysmem",
      uVar1,
      ret - 0x20,
      0x20,
      0xb
  );

  if (ret != 0) {
    do {
    } while (true);
  }

  DAT_41828ae8 = uVar1;

  MemClearZero(&SCATTERED_FROM_4246f168, 0x60);

  ret = MemoryPool_Init(
      &DAT_4356a8e8,
      "usysmem",
      &SCATTERED_FROM_4246f168,
      0x60,
      0x20,
      0xb
  );

  if (ret == 0) {
    memset_zero(&DAT_4356a980, 0x5000);

    OS_CreateTaskWrapper(
        (TCB *)&mainTask_TCB,
        "mainTask",
        (void *)0x4056cab5,
        0,
        0,
        &DAT_4356a984,
        0x4ff8,
        0x32,
        0,
        8,
        1
    );

    if (extraout_r0 == 0) {
      return;
    }

    do {
    } while (true);
  }

  do {
  } while (true);
}
```

First, the start address of the system memory region returned by `GetSysMemRegionBase()` in `Main()` is rounded up and aligned to a `0x20`-byte boundary.

```c
uVar1 = (param_1 + 0x1f) & 0xffffffe0;
```

The system memory region is then initialized to zero based on the aligned start address. The initialization size is calculated by subtracting `0x20` from the value returned by `GetSysMemRegionSize()`.

```c
ret = GetSysMemRegionSize();
MemClearZero(uVar1, ret - 0x20);
```

Afterward, the same memory region is used to create a memory pool named `sysmem`.

```c
ret = MemoryPool_Init(
    &DAT_4356a8d0,
    "sysmem",
    uVar1,
    ret - 0x20,
    0x20,
    0xb
);
```

`MemoryPool_Init()` records the start address, end address, and total size in the supplied memory pool management structure and constructs the management information for the first block at the beginning of the pool.

```c
undefined4 MemoryPool_Init(
    int *pool,
    undefined4 name,
    int base,
    int size)
{
  pool[1] = base;
  pool[0] = base;
  pool[2] = base + size;

  *(undefined4 *)(base + 0xc) = 0;
  *(undefined4 *)(base + 0x10) = 0;
  *(int *)(base + 0x0) = size - 0x14;
  *(undefined4 *)(base + 0x8) = 1;
  *(undefined4 *)(base + 0x4) = 0;

  pool[3] = size;
  pool[4] = 0;
  pool[5] = size;

  return 0;
}
```

The pool management structure stores the start and end of the memory region, its total size, and initial state values. A block header of `0x14` bytes is also placed at the start address of the pool, and the size of the first block is set to the total pool size minus the header size.

Therefore, in the initial state, most of the system memory region appears to be constructed as a single large block. If `MemoryPool_Init()` fails, execution enters an infinite loop and stops the subsequent initialization process.

Afterward, a separate static memory region is initialized, and a second memory pool named `usysmem` is created.

```c
MemClearZero(&SCATTERED_FROM_4246f168, 0x60);

ret = MemoryPool_Init(
    &DAT_4356a8e8,
    "usysmem",
    &SCATTERED_FROM_4246f168,
    0x60,
    0x20,
    0xb
);
```

Unlike the previously created `sysmem`, `usysmem` does not use a dynamically calculated system memory region. Instead, it uses a statically allocated `0x60`-byte region inside the firmware. Its exact purpose has not yet been confirmed, but it appears to be a pool for small RTOS management objects separated from the general system memory.

If `usysmem` initialization fails, the function enters an infinite loop. If it succeeds, the memory region used by `mainTask` is initialized to zero.

```c
memset_zero(&DAT_4356a980, 0x5000);
```

`OS_CreateTaskWrapper()` is then called to create `mainTask`, the first task.

```c
OS_CreateTaskWrapper(
    (TCB *)&mainTask_TCB,
    "mainTask",
    (void *)0x4056cab5,
    0,
    0,
    &DAT_4356a984,
    0x4ff8,
    0x32,
    0,
    8,
    1
);
```

The major arguments passed to the function are as follows.

```text
TCB             mainTask_TCB
Task name       "mainTask"
Entry point     0x4056cab5
Stack base      DAT_4356a984
Stack size      0x4ff8 bytes
Priority        0x32
Autostart       1
```

After initializing the entire `0x5000`-byte region, `DAT_4356a984`, which is located four bytes after the start address, is used as the stack base. Since the stack size is passed as `0x4ff8` bytes, some space at the beginning and end of the initialized region appears to be used for stack management information or boundary regions.

In addition, because the least significant bit of the entry point `0x4056cab5` is set to 1, `mainTask` executes in Thumb state. The actual address at which the instructions are located is `0x4056cab4`, with the least significant bit removed.

Because the final argument, `autostart`, is set to 1, `mainTask` is registered in the scheduler's ready state after task creation is complete and can be selected as an execution target.

---

## OS_CreateTask

`OS_CreateTaskWrapper()` converts the task creation arguments passed from the PAL layer into the format required by the internal RTOS function `OS_CreateTask()`.

```c
void OS_CreateTaskWrapper(
    TCB *task,
    char *name,
    void *task_entry,
    undefined4 param_4,
    undefined4 param_5,
    uint *param_6,
    uint param_7,
    undefined4 param_8,
    undefined4 param_9,
    undefined4 param_10,
    int autostart)
{
  OS_CreateTask(
      task,
      name,
      (undefined2)param_8,
      param_6,
      param_7 >> 2,
      0,
      task_entry,
      0,
      param_5,
      autostart
  );

  return;
}
```

`OS_CreateTaskWrapper()` shifts the stack size supplied in bytes to the right by two bits, converting it into units of 4-byte words.

```text
stack_words = stack_size >> 2;
```

The major values passed to `OS_CreateTask()` when creating `mainTask` are as follows.

```text
TCB             mainTask_TCB
Task name       "mainTask"
Priority        0x32
Stack base      DAT_4356a984
Stack words     0x4ff8 >> 2
Create hook     NULL
Entry point     0x4056cab5
User context    NULL
Autostart       1
```

`param_4`, `param_9`, and `param_10` exist as arguments of the wrapper, but they are not passed to the currently identified call to `OS_CreateTask()`.

The complete code of `OS_CreateTask()`, which is called internally when `mainTask` is created, is as follows.

```c
undefined4 OS_CreateTask(
    TCB *task,
    char *name,
    ushort priority,
    uint *stack_base,
    int stack_words,
    void *create_hook,
    void *entry,
    uint hook_arg_or_ext,
    void *user_context,
    int autostart)
{
  ushort uVar1;
  undefined4 interrupt_state;
  uint *stack_ptr;
  int current_task_id;
  int should_preempt;
  ushort signal_task_id;
  uint selected;
  uint task_id;

  selected = DAT_4178e5b8;
  stack_ptr = stack_base + 2;

  *stack_base = DAT_4178e5b8;
  stack_base[1] = selected;

  interrupt_state = FUN_417c36e0();

  MemCopy(task->name, name);

  signal_task_id = *DAT_4178e5bc + 1;
  selected = signal_task_id + 1;
  task_id = selected & 0xffff;
  uVar1 = (ushort)selected;

  *DAT_4178e5bc = uVar1;

  task->signal_task_id = signal_task_id;
  task->task_id = uVar1;
  task->priority = priority;

  task->saved_signal_task_id = signal_task_id;
  task->saved_task_id = uVar1;
  task->saved_priority = priority;

  task->ready_group_mask =
      1 << (0x1f - (task_id >> 5) & 0xff);

  task->ready_bit_mask =
      1 << (0x1f - (selected & 0x1f) & 0xff);

  task->ready_word_ptr =
      (uint *)(DAT_4178e5c0 + (selected & 0x1f) * 4);

  task->entry = entry;
  task->create_hook = create_hook;

  task->stack_high = stack_ptr + stack_words - 9;
  task->hook_arg_or_ext = hook_arg_or_ext;
  task->saved_sp = stack_ptr + stack_words - 9;

  task->reserved38 = 0;
  task->stack_low = stack_ptr;

  task->pending_event_bits = 0;
  task->event_callback = (void *)0x0;
  task->event_callback_active = 0;
  task->reserved50 = 0;
  task->user_context = user_context;

  List_AppendTail(g_tcbListHead, task);

  current_task_id = g_taskTable;
  *(TCB **)(g_taskTable + task_id * 4) = task;
  *(TCB **)(current_task_id + (uint)signal_task_id * 4) = task;

  if (create_hook != (void *)0x0) {
    (*task->create_hook)();
  }

  task->magic_or_state = DAT_4178e5cc;

  stack_ptr = task->saved_sp;

  task->saved_sp = stack_ptr - 1;
  stack_ptr[-1] = (uint)entry;

  task->saved_sp = task->saved_sp - 1;

  selected = CPU_GetCPSR();
  *task->saved_sp = selected | 0x20;

  task->context_state = 2;

  if (autostart == 1) {
    current_task_id = Scheduler_GetCurrentTaskId();

    Scheduler_SetReady(task_id);

    if (current_task_id == 0x420) {
      SwitchToSchedulerStack();
      Scheduler_SelectHighestReadyTaskId();
      Scheduler_SetCurrentTaskId();
      Scheduler_SelectHighestReadyTaskId();
      Scheduler_Dispatch();
    }

    should_preempt = Scheduler_ShouldPreempt(task_id);

    if (should_preempt == 1) {
      Scheduler_PreemptToTask(current_task_id, 1, task_id);
    }
    else {
      RestoreInterrupts(interrupt_state);
    }
  }

  return 0;
}
```

`OS_CreateTask()` records the task identification information, priority, stack range, entry point, and initial processor context in the supplied TCB. It then registers the TCB in global data structures and, if `autostart` is set, immediately transitions the task into the scheduler's ready state.

The reconstructed TCB structure, based on the fields accessed by `OS_CreateTask()` and references from subsequent scheduler and context-switching functions, is as follows.

```c
typedef struct TCB {
    struct TCB *list_next;           // 0x00
    struct TCB *list_prev;           // 0x04

    uint32_t magic_or_state;         // 0x08

    uint16_t task_id;                // 0x0C
    uint16_t signal_task_id;         // 0x0E
    uint16_t priority;               // 0x10
    uint16_t saved_task_id;          // 0x12
    uint16_t saved_signal_task_id;   // 0x14
    uint16_t saved_priority;         // 0x16

    uint32_t ready_group_mask;       // 0x18
    uint32_t ready_bit_mask;         // 0x1C
    uint32_t *ready_word_ptr;        // 0x20

    void *entry;                     // 0x24

    uint32_t *stack_high;            // 0x28
    uint32_t *stack_low;             // 0x2C
    uint32_t *saved_sp;              // 0x30

    uint32_t context_state;          // 0x34
    uint32_t reserved38;             // 0x38

    uint32_t pending_event_bits;     // 0x3C
    void *event_callback;            // 0x40
    uint32_t event_callback_active;  // 0x44

    uint32_t context_state_shadow;   // 0x48
    uint32_t *saved_sp_shadow;       // 0x4C

    uint32_t reserved50;             // 0x50

    void *create_hook;               // 0x54
    uint32_t hook_arg_or_ext;        // 0x58

    char name[8];                    // 0x5C

    uint32_t dispatch_count;         // 0x64
    void *user_context;              // 0x68

    uint8_t reserved6c[12];          // 0x6C
} TCB;                               // size: 0x78
```

The TCB contains the task ID and priority, ready bitmap information, stack range, saved stack pointer, and task entry point. Through `list_next` and `list_prev` at the beginning of the structure, each TCB is directly linked into the global task list without requiring a separate list node.

The function first writes the same global value twice at the beginning of the stack and sets the actual stack start position to `stack_base + 2`.

```c
selected = DAT_4178e5b8;
stack_ptr = stack_base + 2;

*stack_base = DAT_4178e5b8;
stack_base[1] = selected;
```

Because the first two words are excluded from the actual stack region, they are presumed to be values used for stack boundary checks or corruption detection. The function then calls `FUN_417c36e0()` to modify the interrupt state during task creation and save the previous state.

```c
interrupt_state = FUN_417c36e0();
```

Next, the task name is copied into the TCB, and the global task ID counter is incremented to consecutively allocate a `signal_task_id` and a regular `task_id`.

```c
MemCopy(task->name, name);

signal_task_id = *DAT_4178e5bc + 1;
task_id = signal_task_id + 1;

*DAT_4178e5bc = task_id;
```

The allocated IDs and priority are recorded in both the current-value fields and the saved-value fields.

```c
task->signal_task_id = signal_task_id;
task->task_id = task_id;
task->priority = priority;

task->saved_signal_task_id = signal_task_id;
task->saved_task_id = task_id;
task->saved_priority = priority;
```

The function then calculates the mask and pointer used to manage the task in the scheduler's ready bitmap.

```c
task->ready_group_mask =
    1 << (0x1f - (task_id >> 5));

task->ready_bit_mask =
    1 << (0x1f - (task_id & 0x1f));

task->ready_word_ptr =
    (uint *)(DAT_4178e5c0 + (task_id & 0x1f) * 4);
```

This appears to be a structure in which the ready state is managed as a bitmap by dividing the task ID into groups of 32 tasks and a bit position within each group.

The entry point, stack range, callback, and user-context information are then stored in the TCB.

```c
task->entry = entry;
task->create_hook = create_hook;

task->stack_low = stack_ptr;
task->stack_high = stack_ptr + stack_words - 9;
task->saved_sp = stack_ptr + stack_words - 9;

task->hook_arg_or_ext = hook_arg_or_ext;
task->user_context = user_context;
```

Fields related to event processing are initialized to 0 or `NULL`.

```c
task->reserved38 = 0;
task->pending_event_bits = 0;
task->event_callback = NULL;
task->event_callback_active = 0;
task->reserved50 = 0;
```

Once TCB initialization is complete, the task is added to the global TCB linked list, and both task IDs are registered in the global task table so that they point to the same TCB.

```c
List_AppendTail(g_tcbListHead, task);

g_taskTable[task_id] = task;
g_taskTable[signal_task_id] = task;
```

The linked list appears to be used to iterate over all tasks, while the task table is used to quickly retrieve a TCB by its ID.

If `create_hook` exists, it is called after the task is registered. However, `NULL` is passed for `mainTask`, so it is not executed.

```c
if (create_hook != NULL) {
  (*task->create_hook)();
}
```

Finally, the initial context that will be used when the task is executed for the first time is constructed on the stack.

```c
task->magic_or_state = DAT_4178e5cc;

stack_ptr = task->saved_sp;

task->saved_sp = stack_ptr - 1;
stack_ptr[-1] = (uint)entry;

task->saved_sp--;

selected = CPU_GetCPSR();
*task->saved_sp = selected | 0x20;

task->context_state = 2;
```

The initial stack stores the task entry point and the CPSR with Thumb state enabled. When the scheduler later restores this context, control is transferred to the entry point of `mainTask`.

If `autostart` is 1, the newly created task is registered in the scheduler's ready state.

```c
if (autostart == 1) {
  current_task_id = Scheduler_GetCurrentTaskId();
  Scheduler_SetReady(task_id);
```

If the current task ID is `0x420`, it is considered to be the initial scheduler state in which no regular task is yet executing. The function switches to the scheduler stack, selects a ready task, and dispatches it.

```c
  if (current_task_id == 0x420) {
    SwitchToSchedulerStack();
    Scheduler_SelectHighestReadyTaskId();
    Scheduler_SetCurrentTaskId();
    Scheduler_SelectHighestReadyTaskId();
    Scheduler_Dispatch();
  }
```

If a task is already running, the function checks whether the new task should preempt the current task. If preemption is required, context switching is performed. Otherwise, the interrupt state saved before task creation is restored.

```c
  if (Scheduler_ShouldPreempt(task_id) == 1) {
    Scheduler_PreemptToTask(current_task_id, 1, task_id);
  }
  else {
    RestoreInterrupts(interrupt_state);
  }
}
```

Therefore, `OS_CreateTask()` constructs the TCB and initial stack context, registers the task in the global management structures, and, depending on the `autostart` setting, immediately delivers it to the scheduler in an executable state.

---

## mainTask Autostart

When `mainTask` is registered in the ready state and selected as the first execution target, `Scheduler_Dispatch()` is called. The following is the complete assembly of `Scheduler_Dispatch()` and the context-restoration routine that follows it.

```nasm
                  ************************************
                  *              FUNCTION            *
                  ************************************
                  undefined Scheduler_Dispatch()

  4178e1a8 f0 41 2d e9    stmdb  sp!, {r4, r5, r6, r7, r8, lr}

LAB_4178e1ac:
  4178e1ac 00 40 a0 e1    cpy    r4, r0
  4178e1b0 38 4f d2 eb    bl     FUN_40c21e98
  4178e1b4 dc 60 9f e5    ldr    r6, [DAT_4178e298]        ; 0x418C7B74
  4178e1b8 42 0e 54 e3    cmp    r4, #0x420
  4178e1bc 2f 00 00 0a    beq    LAB_4178e280

  4178e1c0 01 00 14 e3    tst    r4, #1
  4178e1c4 d0 00 9f e5    ldr    r0, [DAT_4178e29c]        ; g_taskTable
  4178e1c8 04 01 90 e7    ldr    r0, [r0, r4, lsl #2]
  4178e1cc 29 00 00 0a    beq    LAB_4178e278

  4178e1d0 00 40 a0 e1    cpy    r4, r0
  4178e1d4 44 00 90 e5    ldr    r0, [r0, #0x44]
  4178e1d8 00 00 50 e3    cmp    r0, #0
  4178e1dc 04 00 a0 e1    cpy    r0, r4
  4178e1e0 01 00 00 0a    beq    LAB_4178e1ec

  4178e1e4 f0 41 bd e8    ldmia  sp!, {r4, r5, r6, r7, r8, lr}
  4178e1e8 e4 4e d2 ea    b      LAB_40c21d80

LAB_4178e1ec:
  4178e1ec 12 4f d2 eb    bl     FUN_40c21e3c
  4178e1f0 d0 03 c4 e1    ldrd   r0, r1, [r4, #0x30]
  4178e1f4 01 20 a0 e3    mov    r2, #1
  4178e1f8 4c 00 84 e5    str    r0, [r4, #0x4c]
  4178e1fc 00 70 a0 e3    mov    r7, #0
  4178e200 48 10 84 e5    str    r1, [r4, #0x48]
  4178e204 44 20 84 e5    str    r2, [r4, #0x44]

LAB_4178e208:
  4178e208 3c 50 94 e5    ldr    r5, [r4, #0x3c]
  4178e20c 3c 70 84 e5    str    r7, [r4, #0x3c]
  4178e210 00 00 96 e5    ldr    r0, [r6]
  4178e214 35 d5 00 eb    bl     RestoreInterrupts
  4178e218 40 10 94 e5    ldr    r1, [r4, #0x40]
  4178e21c 05 00 a0 e1    cpy    r0, r5
  4178e220 31 ff 2f e1    blx    r1
  4178e224 50 07 00 eb    bl     FUN_4178ff6c
  4178e228 3c 00 94 e5    ldr    r0, [r4, #0x3c]
  4178e22c 00 00 50 e3    cmp    r0, #0
  4178e230 f4 ff ff 1a    bne    LAB_4178e208

  4178e234 48 00 94 e5    ldr    r0, [r4, #0x48]
  4178e238 34 00 84 e5    str    r0, [r4, #0x34]
  4178e23c 4c 00 94 e5    ldr    r0, [r4, #0x4c]
  4178e240 30 00 84 e5    str    r0, [r4, #0x30]
  4178e244 44 70 84 e5    str    r7, [r4, #0x44]

  4178e248 be 00 d4 e1    ldrh   r0, [r4, #0x0e]
  4178e24c 81 06 00 eb    bl     FUN_4178fc58
  4178e250 f6 4e d2 eb    bl     SwitchToSchedulerStack

  4178e254 44 10 9f e5    ldr    r1, [DAT_4178e2a0]        ; scheduler state
  4178e258 44 20 9f e5    ldr    r2, [DAT_4178e2a4]        ; ready_words
  4178e25c 08 00 91 e5    ldr    r0, [r1, #8]
  4178e260 10 0f 6f e1    clz    r0, r0
  4178e264 00 21 92 e7    ldr    r2, [r2, r0, lsl #2]
  4178e268 12 2f 6f e1    clz    r2, r2
  4178e26c 80 02 82 e0    add    r0, r2, r0, lsl #5
  4178e270 04 00 81 e5    str    r0, [r1, #4]
  4178e274 cc ff ff ea    b      LAB_4178e1ac

LAB_4178e278:
  4178e278 f0 41 bd e8    ldmia  sp!, {r4, r5, r6, r7, r8, lr}
  4178e27c bf 4e d2 ea    b      LAB_40c21d80

LAB_4178e280:
  4178e280 ea 4e d2 eb    bl     SwitchToSchedulerStack
  4178e284 00 00 96 e5    ldr    r0, [r6]
  4178e288 18 d5 00 eb    bl     RestoreInterrupts
  4178e28c 00 00 a0 e3    mov    r0, #0
  4178e290 f4 84 b7 fb    blx    app_hooks__Interrupts

LAB_4178e294:
  4178e294 fe ff ff ea    b      LAB_4178e294
```

The routine that actually restores the context of the task selected by `Scheduler_Dispatch()` is located at `LAB_40c21d80`.

```nasm
LAB_40c21d70:
  40c21d70 cb b0 2d eb    bl     FUN_4178e0a4
  40c21d74 5c 01 9f e5    ldr    r0, [LAB_40c21ed8]
  40c21d78 00 00 90 e5    ldr    r0, [r0]
  40c21d7c 09 b1 2d eb    bl     Scheduler_Dispatch

LAB_40c21d80:
  40c21d80 30 d0 90 e5    ldr    sp, [r0, #0x30]
  40c21d84 34 10 90 e5    ldr    r1, [r0, #0x34]
  40c21d88 04 20 9d e4    ldr    r2, [sp], #4
  40c21d8c c0 20 82 e3    orr    r2, r2, #0xc0

  40c21d90 4c 31 9f e5    ldr    r3, [DAT_40c21ee4]
  40c21d94 00 30 93 e5    ldr    r3, [r3]
  40c21d98 00 00 53 e3    cmp    r3, #0
  40c21d9c 00 00 00 1a    bne    LAB_40c21da4
  40c21da0 c0 20 c2 e3    bic    r2, r2, #0xc0

LAB_40c21da4:
  40c21da4 02 f0 6f e1    msr    spsr_cxsf, r2
  40c21da8 01 00 51 e3    cmp    r1, #1
  40c21dac 03 00 00 0a    beq    LAB_40c21dc0
  40c21db0 02 00 51 e3    cmp    r1, #2
  40c21db4 03 00 00 0a    beq    LAB_40c21dc8

  40c21db8 1c 36 e5 fa    blx    FUN_4056f630
  40c21dbc f0 9f fd e8    ldmia  sp!, {r4-r12, sp, lr, pc}^

LAB_40c21dc0:
  40c21dc0 1a 36 e5 fa    blx    FUN_4056f630
  40c21dc4 ff ff dd e8    ldmia  sp, {r0-r12, sp, lr, pc}^

LAB_40c21dc8:
  40c21dc8 00 80 fd e8    ldmia  sp!, {pc}^
```

`Scheduler_Dispatch()` checks whether the supplied task ID is even or odd. For an even regular task ID, it retrieves the TCB from the global task table and immediately moves to the context-restoration path at `LAB_40c21d80`. For an odd signal task ID, it processes the pending event and callback stored in the TCB and then searches the ready bitmap again.

Because `mainTask` is selected using an even regular execution task ID, it does not pass through the event-callback path. Instead, it moves to the path that restores the TCB's `saved_sp` and `context_state`.
