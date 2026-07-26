## MainTask_entry

Previously, the process in which `OS_CreateTask()` constructs the TCB and initial processor context of `mainTask`, and the scheduler restores that context to execute the first task, was analyzed.

The address registered as the entry point of `mainTask` is `0x4056CAB5`, and its least significant bit indicates Thumb state. Therefore, the actual address at which the instructions are located is `0x4056CAB4`. When the scheduler restores the CPSR and PC from the initial stack of `mainTask`, control is transferred to `MainTask_entry()` at this address.

```text
mainTask entry pointer   0x4056CAB5
Actual code address      0x4056CAB4
Execution state          Thumb
```

`MainTask_entry()` initializes the PAL runtime and then iterates through the task descriptors statically defined in the firmware to create each PAL task. It then synchronizes until the created tasks reach their initial startup point and enters `pal_TaskReaperLoop()`, which handles task termination and cleanup.

```c
void MainTask_entry(void)

{
  byte bVar1;
  int iVar2;
  undefined4 extraout_r3;
  undefined4 unaff_r4;
  undefined4 *puVar3;
  int iVar4;
  
  dummy_function(&DAT_4356a8d0);
  dummy_function_1(&DAT_4356a8d0);
  FUN_4056f728();
  pal_TaskManager__HISR0();
  pal_Init1();
  DAT_417fc720 = (code *)0x4056cc53;
  pal_ExceptionDump_RegisterCallback(0x40570091);
  if (g_palStaticTaskCount != 0) {
    create_semaphore(&g_palStartupSyncSem,"PALTskSs",0,extraout_r3,unaff_r4);
    pal_BuildStaticTaskStartupList();
    if ((undefined4 **)g_palStaticTaskStartupList == &g_palStaticTaskStartupList) {
      pal_FatalAssert(0xfffff405,"../../../VARIANT/PALVar/Platform_EV/PAL/inc/pal_list.h",0x12a);
    }
    puVar3 = g_palStaticTaskStartupList;
    DAT_418c7b74 = 0;
    enable_interrupts(0);
    iVar4 = 0;
    if (g_palStaticTaskCount != 0) {
      do {
        iVar2 = puVar3[2];
        if (*(undefined4 **)*puVar3 == puVar3) {
          pal_FatalAssert(0xfffff406,"../../../VARIANT/PALVar/Platform_EV/PAL/inc/pal_list.h",0x156)
          ;
        }
        puVar3 = (undefined4 *)*puVar3;
        if (*(uint *)(&DAT_41827b4c + g_palPreRegisterTaskCursor * 8) <
            (uint)(&g_palTaskDescTable)[iVar2].priority) {
          do {
            OS_PreRegisterTaskIds
                      (*(int *)(&DAT_41827b48 + g_palPreRegisterTaskCursor * 8) * 0x108 + 0x41807830
                       ,*(undefined2 *)(&DAT_41827b4c + g_palPreRegisterTaskCursor * 8));
            g_palPreRegisterTaskCursor = g_palPreRegisterTaskCursor + 1;
          } while (*(uint *)(&DAT_41827b4c + g_palPreRegisterTaskCursor * 8) <
                   (uint)(&g_palTaskDescTable)[iVar2].priority);
        }
        bVar1 = (&g_palTaskDescTable)[iVar2].flags;
        (&g_palTaskDescTable)[iVar2].flags = bVar1 | 2;
        if ((bVar1 & 4) == 0) {
          pal_CreateTaskFromDescriptor(&g_palTaskDescTable + iVar2,1);
        }
        else {
          g_palDeferredStartupTaskCount = g_palDeferredStartupTaskCount + 1;
          pal_CreateTaskFromDescriptor(&g_palTaskDescTable + iVar2,0);
        }
        iVar4 = iVar4 + 1;
      } while (iVar4 != g_palStaticTaskCount);
    }
    pal_SmObtain(g_palStartupSyncSem);
    (*DAT_417fc720)();
    g_palStartupBarrierActive = 0;
    pal_SmRelease(g_palStartupGateSem);
    pal_SmObtain(g_palStartupSyncSem);
    pal_SmDelete(g_palStartupSyncSem);
    pal_TaskReaperLoop();
  }
  (*DAT_417fc720)();
  g_palStartupBarrierActive = 0;
  return;
}
```

Before calling `pal_Init1()`, `MainTask_entry()` first executes several preparation routines.

```c
dummy_function(&DAT_4356a8d0);
dummy_function_1(&DAT_4356a8d0);
FUN_4056f728();
pal_TaskManager__HISR0();
```

The first functions called, `dummy_function()` and `dummy_function_1()`, are no-op stubs in the current binary whose bodies immediately return using `bx lr`. They also do not use the supplied argument `DAT_4356A8D0`.

`FUN_4056F728()` then initializes three internal PAL list heads placed around a reference address. Because the pointers in each region are configured to point either to themselves or to a common sentinel, this function appears to be a bootstrap helper that constructs the initial state of circular linked lists. It does not appear to be directly related to the task structure.

Finally, `pal_TaskManager__HISR0()` creates the `HISR0`, `HISR1`, and `HISR2` tasks, which handle additional processing after an interrupt occurs. Each task waits for work in its own queue and executes a registered callback when a request arrives. In other words, this function **prepares the HISR tasks responsible for high-level ISR processing before general PAL tasks are created**.

```c
void pal_TaskManager__HISR0(void)

{
  short sVar1;
  undefined4 uVar2;
  
  FUN_4178e394(&DAT_432275b4,"VoidSem",0);
  uVar2 = OS_CreateTask((TCB *)&DAT_4322b544,"HISR0",1,(uint *)&DAT_4322b5c4,0x4000,0,0x40cc8b6b,0,0
                        ,1);
  if ((short)uVar2 != 0) {
    pal_FatalAssert((int)(short)uVar2,
                    "../../../VARIANT/PALVar/Platform_EV/PAL/TaskManager/src/pal_TaskManager.c",
                    0x890);
  }
  uVar2 = OS_CreateTask((TCB *)&DAT_4323b5c0,"HISR1",2,(uint *)&DAT_4323b63c,0x4000,0,0x40cc8bd3,0,0
                        ,1);
  if ((short)uVar2 != 0) {
    pal_FatalAssert((int)(short)uVar2,
                    "../../../VARIANT/PALVar/Platform_EV/PAL/TaskManager/src/pal_TaskManager.c",
                    0x89c);
  }
  uVar2 = OS_CreateTask((TCB *)&DAT_4324b638,"HISR2",3,(uint *)&DAT_4324b6b4,0x4000,0,0x40cc8c3b,0,0
                        ,1);
  if ((short)uVar2 != 0) {
    pal_FatalAssert((int)(short)uVar2,
                    "../../../VARIANT/PALVar/Platform_EV/PAL/TaskManager/src/pal_TaskManager.c",
                    0x8a8);
  }
  sVar1 = FUN_4178e150();
  if (sVar1 != 0) {
    pal_FatalAssert((int)sVar1,
                    "../../../VARIANT/PALVar/Platform_EV/PAL/TaskManager/src/pal_TaskManager.c",
                    0x8ab);
    return;
  }
  return;
}
```

---

## pal_Init1

After preparing the HISR tasks through `pal_TaskManager__HISR0()`, `MainTask_entry()` calls `pal_Init1()`.

```c
pal_TaskManager__HISR0();
pal_Init1();
```

`pal_Init1()` does not directly create or execute static tasks. Instead, it is an initialization function that constructs the foundation of the entire PAL runtime so that `MainTask_entry()` can later create and execute the statically defined `TaskDescriptor` objects.

```c
void pal_Init1(void)

{
  int iVar1;
  undefined4 uVar2;
  undefined4 local_170;
  undefined4 local_16c;
  undefined4 local_168;
  undefined4 local_164;
  undefined4 local_160;
  undefined4 local_15c;
  undefined4 local_158;
  undefined4 local_154;
  undefined1 auStack_f0 [128];
  undefined1 auStack_70 [76];
  int local_24;
  TraceEntry *local_20;
  undefined4 local_1c;
  undefined1 local_18 [4];
  undefined1 local_14 [8];
  
  local_14[0] = 0;
  local_18[0] = 0;
  memset_zero(&local_170,0x80);
  memset_zero(auStack_f0,0x80);
  local_24 = 0;
  memset_zero(auStack_70,0x4c);
  thunk_FUN_4178de90(0xc1762b);
  iVar1 = FUN_4056ff90();
  uVar2 = 0;
  if (iVar1 != 0) {
    uVar2 = 2;
  }
  FUN_4056da18(uVar2);
  pal_BusMon_Init();
  FUN_40b53abc();
  FUN_40cc953a();
  FUN_4056f4aa();
  FUN_4056f5e4();
  pal_MemDriverPmd();
  pal_MemDriverRtk();
  pal_SemaphorePool_Init();
  pal_TaskManager_InitStaticDescriptors();
  DAT_43ddd81c._0_2_ = FUN_41310bd6();
  FUN_405706d8();
  pal_RegInit();
  S5000AP_S_20200113_055234();
  FUN_40c94da4(&DAT_418720e0,&DAT_40187d0c,0,"RegInit completed");
  thunk_FUN_417903e4(&local_170,0x80);
  iVar1 = thunk_FUN_04005a70(&local_170,auStack_f0,0x10);
  if (iVar1 == 0) {
    software_interrupt(1);
    DataMemoryBarrier(0x1f);
    DAT_41828b04 = "Wrong key";
    FUN_4056fa8e(&DAT_41828afc);
  }
  local_170 = 0;
  local_16c = 0;
  local_168 = 0;
  local_164 = 0;
  local_160 = 0;
  local_15c = 0;
  local_158 = 0;
  local_154 = 0;
  UTIL_Math();
  uVar2 = FUN_40c454e8("S5000AP_BEYOND1");
  FUN_411f830c("S5000AP_BEYOND1",uVar2);
  DAT_417fd4d0 = 1;
  local_24 = thunk_FUN_0401622e(4,&DAT_00004400,
                                "../../../VARIANT/PALVar/Platform_EV/CHIPSET/S5000AP/device/User/src /pal_main.c"
                                ,0x216);
  if (local_24 == 0) {
    local_20 = &TraceEntry::pal_main::pal_Init1_pSecurity_memory_array_MemAl;
    local_1c = 0x1585;
    FUN_4056b3de(&local_20);
    software_interrupt(1);
    DataMemoryBarrier(0x1f);
    DAT_41828b10 = "NV default : pSecurity_memory_array Memalloc fail";
    FUN_4056fa8e(&DAT_41828b08);
  }
  FUN_40c9401a(&DAT_00002c1b,local_24);
  DAT_417fd4c8 = 1;
  iVar1 = thunk_FUN_04005a70(local_24,auStack_70,0x4c);
  if (iVar1 == 0) {
    pal_Security_memory();
    local_20 = &TraceEntry::pal_main::Protected_pal_RegInit_Secure_Block_Def;
    local_1c = 0x1582;
    FUN_4056b3de(&local_20,&DAT_fecdba98);
  }
  else {
    local_20 = &TraceEntry::pal_main::Protected_pal_RegInit_Secure_Block_Ini;
    local_1c = 0x1582;
    FUN_4056b3de(&local_20,&DAT_fecdba98);
  }
  if (local_24 != 0) {
    FUN_40cc91d4(&local_24,
                 "../../../VARIANT/PALVar/Platform_EV/CHIPSET/S5000AP/device/User/src/pal_main.c",
                 0x22a);
  }
  FUN_405bb404();
  TCS_UnifiedSpCfg__defined();
  TestConfigurationService__Feature_8();
  TestConfigurationService__TCS_Init_NVtype_Features();
  RF_LTE_NV_Init_Load_Default_Cal_Values();
  FUN_40c9401a(0x37,local_14);
  FUN_40c9401a(0x55,local_18);
  FUN_40cc950c(local_18[0]);
  FUN_4056c81e();
  uart_main_1(2,&DAT_4356f980,0x400);
  dbg_Core__Hello();
  memInitNonSecureMemoryPoolRx();
  FUN_41184d08();
  DmTraceMsg__Default();
  FUN_40ff1f9c();
  FUN_4056f7f8("UpTimer Init: ");
  FUN_40cf8500();
  FUN_4056f7f8("Complete.\r\n");
  thunk_FUN_04001f5c();
  pal_TmMain__hTimer();
  FUN_4056d7f6();
  do {
    iVar1 = thunk_FUN_040193ce();
  } while (iVar1 == 0);
  hal_modem__InitModem();
  ps_Controller__thal_client_ids();
  pal_msg__Background();
  pal_WatchdogKick();
  FUN_4057321e();
  FUN_4056d710();
  thunk_FUN_040020ec();
  tcs_rfCfg();
  Tcs_LteBandConfiguration();
  local_20 = &TraceEntry::pal_main::BandSet_Done;
  local_1c = 0x1582;
  FUN_4056b3de(&local_20,&DAT_fecdba98);
  FUN_405b1f84();
  FUN_4056cbf0();
  hw_Device();
  hw_Acpm__pal_SmCreateEventGroup();
  FUN_41274c34();
  FUN_405bb498();
  iVar1 = hw_ClkFindSysClkCofigInfoIndex_1();
  if (iVar1 == 0) {
    local_20 = &TraceEntry::pal_main::DFS_is_not_ENABLED;
    local_1c = 0x1582;
    FUN_4056b3de(&local_20,&DAT_fecdba98);
  }
  RFIC_TYPE();
  PHYP_Subsys_PreStartup__pal_TmCreateMsgTimer();
  FUN_4123bf0a();
  FUN_40776594();
  FUN_4123c2a8();
  DAT_41828aec = thunk_FUN_04018ae8(99);
  thunk_FUN_0400465e();
  thunk_FUN_040046d2(DAT_41828aec,0x4056cc7d);
  thunk_FUN_04004668(DAT_41828aec);
  hw_Power__Information();
  FUN_4056f280();
  FUN_40c9401a(0x11,&DAT_4180711c);
  FUN_40c94da4(&DAT_418720e0,&DAT_40187d1c,0,"pal_init1 completed");
  return;
}
```

Inside the function, the low-level hardware and memory backends are initialized first, and the semaphore pool and task descriptor manager used by PAL are prepared. It then loads the Registry and NV configurations, initializes the timer, message, and debug subsystems, and performs the pre-startup processes related to the modem, RF, and PHY subsystems.

The overall flow can be summarized as follows.

```text
Low-level PAL/HW initialization
 → Memory backend and driver registration
 → Semaphore pool initialization
 → TaskDescriptor manager initialization
 → Registry/NV/security configuration loading
 → Timer/message/debug subsystem initialization
 → Modem/RF/PHY pre-startup
 → Exception handler registration
```

At the beginning of the function, the basic hardware and memory-related environments used by PAL are prepared.

```c
pal_BusMon_Init();
FUN_40b53abc();
FUN_40cc953a();
FUN_4056f4aa();
FUN_4056f5e4();
pal_MemDriverPmd();
pal_MemDriverRtk();
```

This region appears to include initialization of the bus monitor, SIM GPIO and interrupt-related components, the memory backend dispatcher, and memory driver registration. Although the exact roles of every function have not been identified, this can be considered a stage that prepares the low-level execution foundation used by the subsequent PAL object manager.

The PAL semaphore pool and task descriptor manager are then initialized.

```c
pal_SemaphorePool_Init();
pal_TaskManager_InitStaticDescriptors();
```

`pal_SemaphorePool_Init()` initializes `0x400` PAL semaphore objects and connects the unused objects into a free list. Each semaphore object has a size of `0x3C` bytes, and PAL semaphore APIs such as `pal_SmCreate()`, `pal_SmObtain()`, and `pal_SmRelease()` later use this pool.

```text
Semaphore object count   0x400
Semaphore object size    0x3C
```

`pal_TaskManager_InitStaticDescriptors()` initializes the `TaskDescriptor` management structure used during static task startup. This function calculates the number of static descriptors and constructs a free list from the remaining unused descriptors.

```c
void pal_TaskManager_InitStaticDescriptors(void)

{
  TaskDescriptor *pTVar1;
  uint uVar2;
  uint uVar3;
  TaskDescriptor *pTVar4;
  
  g_palStartupBarrierActive = 1;
  create_semaphore(&g_palTaskManagerMutexSem,"PALTskTm",1);
  g_palActiveTaskList = &g_palActiveTaskList;
  DAT_417fc73c = &g_palActiveTaskList;
  uVar2 = 0;
  DAT_417fc740 = &DAT_417fc740;
  DAT_417fc744 = (TaskDescriptor *)&DAT_417fc740;
  do {
    if ((&g_palTaskDescTable)[uVar2].name == (char *)0x0) break;
    (&g_palTaskDescTable)[uVar2].task_index = uVar2;
    uVar2 = uVar2 + 1;
  } while (uVar2 != 500);
  g_palStaticTaskCount = uVar2;
  if (uVar2 < 500) {
    do {
      pTVar4 = &g_palTaskDescTable + uVar2;
      (&g_palTaskDescTable)[uVar2].state = 0;
      (&g_palTaskDescTable)[uVar2].task_index = uVar2;
      pTVar1 = DAT_417fc744;
      if (DAT_417fc740 == (undefined4 *)0x0) {
        pal_FatalAssert(0xfffff409,"../../../VARIANT/PALVar/Platform_EV/PAL/inc/pal_list.h",0x1e6);
      }
      uVar3 = uVar2 + 1;
      DAT_417fc744 = pTVar4;
      pTVar4->list_next = (TaskDescriptor *)&DAT_417fc740;
      (&g_palTaskDescTable)[uVar2].list_prev = pTVar1;
      pTVar1->list_next = pTVar4;
      uVar2 = uVar3;
    } while (uVar3 != 500);
  }
  create_semaphore(&g_palTaskCleanupSem,"PALTskCs",0);
  return;
}
```

The function first sets `g_palStartupBarrierActive` to 1, indicating that static task startup is in progress. It then creates the `"PALTskTm"` semaphore with an initial count of 1 to protect the internal data structures of the task manager.

```c
g_palStartupBarrierActive = 1;
create_semaphore(&g_palTaskManagerMutexSem,"PALTskTm",1);
```

Because the initial count is 1, `PALTskTm` is considered to operate as a mutex that prevents multiple tasks from modifying the descriptor table or the active and free lists at the same time.

Next, it initializes the head of the active list used to manage currently created task descriptors and the head of the free list used to store unused descriptors.

```c
g_palActiveTaskList = &g_palActiveTaskList;
DAT_417fc73c = &g_palActiveTaskList;
uVar2 = 0;
DAT_417fc740 = &DAT_417fc740;
DAT_417fc744 = (TaskDescriptor *)&DAT_417fc740;
```

Because the next and previous pointers of each list are configured to point to their own head, both lists enter the initial state of an empty circular doubly linked list.

It then iterates through `g_palTaskDescTable` from the beginning and calculates the number of static descriptors.

```c
uVar2 = 0;

do {
  if (g_palTaskDescTable[uVar2].name == NULL) {
    break;
  }

  g_palTaskDescTable[uVar2].task_index = uVar2;
  uVar2++;

} while (uVar2 != 500);
```

`g_palTaskDescTable` is located at `0x418077A8`, and each `TaskDescriptor` has a size of `0x108` bytes. Statically defined task descriptors are placed consecutively at the beginning of the table.

```text
TaskDescriptor table base   0x418077A8
Descriptor size             0x108
Maximum descriptor count    500
```

The function checks the `name` field of each descriptor and stops searching when the first descriptor containing `NULL` is found. Therefore, descriptors with a configured `name` are treated as static tasks, and the table index is recorded in each descriptor.

```c
g_palTaskDescTable[uVar2].task_index = uVar2;
```

Once the search is complete, the identified number of static descriptors is stored in `g_palStaticTaskCount`.

```c
g_palStaticTaskCount = uVar2;
```

This value is later used by `MainTask_entry()` when iterating through the static task startup list and creating tasks.

The descriptors remaining after the static descriptors are added to the free list so that they can be used to dynamically create tasks at runtime.

```c
g_palTaskDescTable[uVar2].state = 0;
g_palTaskDescTable[uVar2].task_index = uVar2;
```

The state of each free descriptor is initialized to 0, and its table index is stored in the same manner as for static descriptors.

The descriptor is then connected to the final position of the free list.

```c
pTVar1 = DAT_417fc744;

DAT_417fc744 = pTVar4;

pTVar4->list_next =
    (TaskDescriptor *)&DAT_417fc740;

pTVar4->list_prev = pTVar1;

pTVar1->list_next = pTVar4;
```

The new descriptor's `list_prev` points to the previous final descriptor, while its `list_next` points to the head of the free list. The `list_next` of the previous final descriptor is also changed to the new descriptor. As a result, all remaining descriptors are sequentially connected to a circular doubly linked free list.

Finally, the `"PALTskCs"` semaphore is created with an initial count of 0.

```c
create_semaphore(
    &g_palTaskCleanupSem,
    "PALTskCs",
    0
);
```

This function does not actually create or execute static tasks. Instead, it prepares the initial state of the task manager so that `MainTask_entry()` can later iterate `g_palStaticTaskCount` times through the descriptors and call `pal_CreateTaskFromDescriptor()`.

Afterward, `pal_Init1()` initializes the Registry and NV subsystems.

```c
pal_RegInit();
S5000AP_S_20200113_055234();
FUN_40c94da4(
    &DAT_418720e0,
    &DAT_40187d0c,
    0,
    "RegInit completed"
);
```

After Registry initialization, it checks the key and security memory and verifies the NV default data and secure block. If verification or memory allocation fails, execution enters the software interrupt and fatal-processing path.

```c
if (iVar1 == 0) {
    software_interrupt(1);
    DataMemoryBarrier(0x1f);
    DAT_41828b04 = "Wrong key";
    FUN_4056fa8e(&DAT_41828afc);
}
```

It then loads the TCS configuration and LTE RF NV default values and initializes UART, the debug core, and the non-secure memory pool.

```c
TCS_UnifiedSpCfg__defined();
TestConfigurationService__Feature_8();
TestConfigurationService__TCS_Init_NVtype_Features();
RF_LTE_NV_Init_Load_Default_Cal_Values();

uart_main_1(2, &DAT_4356f980, 0x400);
dbg_Core__Hello();
memInitNonSecureMemoryPoolRx();
```

Next, the timer subsystem is initialized.

```c
FUN_4056f7f8("UpTimer Init: ");
FUN_40cf8500();
FUN_4056f7f8("Complete.\r\n");

thunk_FUN_04001f5c();
pal_TmMain__hTimer();
FUN_4056d7f6();
```

Inside `pal_TmMain__hTimer()`, the following function is called.

```c
pal_TaskManager_18(
    out,
    "hTimer",
    0x4004c6d,
    2,
    0,
    0
);
```

However, `pal_TaskManager_18()` does not call `OS_CreateTaskWrapper()`. Instead, it obtains one free descriptor and records a name, priority, and callback address in an internal control block.

Therefore, rather than being a general OS task, `hTimer` is likely a deferred callback descriptor or HISR control object used to deliver timer-expiration processing to an HISR worker.

To determine the exact execution path, the timer interrupt and HISR queue registration functions must be analyzed further.

After timer initialization, the function repeats until the following function returns a nonzero value.

```c
do {
    iVar1 = thunk_FUN_040193ce();
} while (iVar1 == 0);
```

`FUN_040193CE()` reads a timestamp and calls a global callback. Therefore, this appears to be a process that waits until the timer or clock subsystem becomes available, although the exact condition requires further analysis.

The modem and message subsystems are then initialized.

```c
hal_modem__InitModem();
ps_Controller__thal_client_ids();
pal_msg__Background();
pal_WatchdogKick();
```

`pal_msg__Background()` initializes the descriptor table and queue-related structures used by the PAL message subsystem. During this process, up to 500 message or queue descriptors are prepared, forming the foundation that later allows each PAL task to wait for and receive messages.

In the latter part of the function, LTE band configuration, the ACPM event group, clock configuration, and the RFIC and PHY subsystems are initialized.

```c
tcs_rfCfg();
Tcs_LteBandConfiguration();

hw_Device();
hw_Acpm__pal_SmCreateEventGroup();

RFIC_TYPE();
PHYP_Subsys_PreStartup__pal_TmCreateMsgTimer();
```

`PHYP_Subsys_PreStartup__pal_TmCreateMsgTimer()` creates the message timer used by the PHY subsystem, which is also connected to the subsequent timer- and message-based task wake-up process.

Finally, an exception object is created, and a handler is registered.

```c
DAT_41828aec = thunk_FUN_04018ae8(99);

thunk_FUN_0400465e();
thunk_FUN_040046d2(DAT_41828aec, 0x4056cc7d);
thunk_FUN_04004668(DAT_41828aec);
```

The registered handler at `0x4056CC7D` is connected to a fatal-processing path related to `"Data Abort with L2C"`.

Once all initialization is complete, the function records the `"pal_init1 completed"` trace and returns.

```c
FUN_40c94da4(
    &DAT_418720e0,
    &DAT_40187d1c,
    0,
    "pal_init1 completed"
);
```

---

## Static PAL Task Startup

When `pal_Init1()` returns, `MainTask_entry()` enters the startup stage in which the static `TaskDescriptor` objects are created as actual RTOS tasks.

First, it registers the callback that will be invoked when startup is complete and the exception dump callback.

```c
DAT_417fc720 = (code *)0x4056cc53;
pal_ExceptionDump_RegisterCallback(0x40570091);
```

If `g_palStaticTaskCount` is not zero, static task startup begins.

```c
if (g_palStaticTaskCount != 0) {
```

`g_palStaticTaskCount` is the number of static descriptors previously calculated by `pal_TaskManager_InitStaticDescriptors()` while iterating through the descriptor table.

The `"PALTskSs"` semaphore is first created with an initial count of 0 to synchronize the startup progress of `MainTask` and the newly created tasks.

```c
create_semaphore(
    &g_palStartupSyncSem,
    "PALTskSs",
    0,
    extraout_r3,
    unaff_r4
);
```

Because its initial count is 0, `MainTask` immediately enters the waiting state when it obtains this semaphore. After all created static tasks reach a specific startup point, they release the semaphore and wake `MainTask` again.

Next, a linked list containing the static descriptors ordered according to startup priority is constructed.

```c
pal_BuildStaticTaskStartupList();
```

```c
void pal_BuildStaticTaskStartupList(void)

{
  int *piVar1;
  uint uVar2;
  int init_node_addr;
  int node_addr;
  int iVar3;
  uint uVar4;
  int startup_list_head_init;
  
  g_palStaticTaskStartupList = &g_palStaticTaskStartupList;
  _DAT_417fc74c = (int *)&g_palStaticTaskStartupList;
  uVar4 = 0;
  do {
                    /* Static startup node layout: +0x00 next, +0x04 prev, +0x08 task_index, +0x0c
                       priority. Node stride is 0x10. */
    init_node_addr = (int)(&DAT_432275e4 + uVar4 * 4);
    *(undefined4 *)init_node_addr = 0;
    (&DAT_432275ec)[uVar4 * 4] = uVar4;
    uVar2 = uVar4 + 1;
    (&DAT_432275f0)[uVar4 * 4] = (uint)(&g_palTaskDescTable)[uVar4].priority;
    uVar4 = uVar2;
  } while (uVar2 < 0xff);
  uVar4 = 0;
  do {
                    /* Build startup list by scanning priority values 0..255; for each priority,
                       append matching task_index nodes. Same-priority order follows descriptor
                       index. */
    iVar3 = 0;
    if (g_palStaticTaskCount != 0) {
      do {
        piVar1 = _DAT_417fc74c;
        node_addr = (int)(&DAT_432275e4 + iVar3 * 4);
        if ((&DAT_432275f0)[iVar3 * 4] == uVar4) {
          if (g_palStaticTaskStartupList == (undefined4 *)0x0) {
            pal_FatalAssert(0xfffff409,"../../../VARIANT/PALVar/Platform_EV/PAL/inc/pal_list.h",
                            0x1e6);
          }
          _DAT_417fc74c = (int *)node_addr;
          *(undefined4 ***)node_addr = &g_palStaticTaskStartupList;
          (&DAT_432275e8)[iVar3 * 4] = piVar1;
          *piVar1 = node_addr;
          g_palStaticStartupListCount = g_palStaticStartupListCount + 1;
        }
        iVar3 = iVar3 + 1;
      } while (iVar3 != g_palStaticTaskCount);
    }
    uVar4 = uVar4 + 1;
  } while (uVar4 < 0x100);
  return;
}
```

After the list is created, the function checks whether the head points back to itself.

```c
if ((undefined4 **)g_palStaticTaskStartupList ==
    &g_palStaticTaskStartupList) {
  pal_FatalAssert(
      0xfffff405,
      "../../../VARIANT/PALVar/Platform_EV/PAL/inc/pal_list.h",
      0x12a
  );
}
```

In a circular linked list, if the head's next pointer points back to the head, the list is empty. If `g_palStaticTaskCount` is not zero but the startup list is empty, the descriptor count and list state do not match, so a fatal assertion is raised.

If the startup list has been constructed normally, the first node is obtained.

```c
puVar3 = g_palStaticTaskStartupList;
```

Several global startup states are then initialized, and interrupts are enabled.

```c
DAT_418c7b74 = 0;
enable_interrupts(0);
```

From this point, if a task that has been created and resumed has a higher priority than `MainTask`, the scheduler can preempt `MainTask` even while task creation is in progress.

The startup list is now traversed, and each static descriptor is processed.

```c
iVar4 = 0;

do {
    ...
    iVar4 = iVar4 + 1;
} while (iVar4 != g_palStaticTaskCount);
```

The third word of each list node stores an index into `g_palTaskDescTable`.

```c
iVar2 = puVar3[2];
```

Therefore, the descriptor currently being processed is selected as follows.

```c
TaskDescriptor *task = &g_palTaskDescTable[iVar2];
```

Before moving to the next node, the linked-list connection state is checked.

```c
if (*(undefined4 **)*puVar3 == puVar3) {
  pal_FatalAssert(
      0xfffff406,
      "../../../VARIANT/PALVar/Platform_EV/PAL/inc/pal_list.h",
      0x156
  );
}

puVar3 = (undefined4 *)*puVar3;
```

If the check succeeds, execution follows the `list_next` field of the current node and moves to the next startup descriptor.

Next, several task IDs are preregistered according to the priority of the current task.

```c
if (*(uint *)(
        &DAT_41827b4c +
        g_palPreRegisterTaskCursor * 8
    ) <
    (uint)g_palTaskDescTable[iVar2].priority) {

  do {
    OS_PreRegisterTaskIds(
        *(int *)(
            &DAT_41827b48 +
            g_palPreRegisterTaskCursor * 8
        ) * 0x108 + 0x41807830,

        *(undefined2 *)(
            &DAT_41827b4c +
            g_palPreRegisterTaskCursor * 8
        )
    );

    g_palPreRegisterTaskCursor++;

  } while (
      *(uint *)(
          &DAT_41827b4c +
          g_palPreRegisterTaskCursor * 8
      ) <
      (uint)g_palTaskDescTable[iVar2].priority
  );
}
```

`OS_PreRegisterTaskIds()` preregisters two consecutive IDs and a priority in the TCB before the static task is actually created. The first ID is used as the signal task ID, and the second ID is used as the regular task ID. Both IDs are configured to point to the same TCB in the global TCB lookup table.

This allows the firmware-defined task ID layout to be preserved regardless of the order in which tasks are later created.

Once task ID preregistration is complete, the startup flag of the current descriptor is updated, and the function decides whether to execute the task immediately or leave it in a deferred state.

```c
bVar1 = g_palTaskDescTable[iVar2].flags;
g_palTaskDescTable[iVar2].flags = bVar1 | 2;
```

The previous `flags` value is preserved, and bit `0x02` is then set. This bit is considered to indicate that the descriptor has been processed during static startup or that task creation has been requested.

Bit `0x04` of the previous `flags` value is then checked.

```c
if ((bVar1 & 4) == 0) {
  pal_CreateTaskFromDescriptor(
      &g_palTaskDescTable[iVar2],
      1
  );
}
else {
  g_palDeferredStartupTaskCount =
      g_palDeferredStartupTaskCount + 1;

  pal_CreateTaskFromDescriptor(
      &g_palTaskDescTable[iVar2],
      0
  );
}
```

For a task whose `0x04` bit is not set, 1 is supplied as the second argument to `pal_CreateTaskFromDescriptor()`. In this case, the RTOS task is created from the descriptor, and `OS_Resume_Task()` is called to transition it into the scheduler's ready state.

In contrast, a descriptor whose `0x04` bit is set is counted as a deferred startup task. The global `g_palDeferredStartupTaskCount` is incremented, and 0 is supplied as the second argument. As a result, the task's TCB and initial context are created, but `OS_Resume_Task()` is not called.

Therefore, while the execution environments of all tasks are constructed during traversal of the static descriptors, whether each task immediately becomes an execution target of the scheduler is determined by the descriptor's `0x04` flag.

```c
iVar4 = iVar4 + 1;
} while (iVar4 != g_palStaticTaskCount);
```

Once this process has been repeated `g_palStaticTaskCount` times, task creation requests for all static descriptors are complete.

---

## pal_CreateTaskFromDescriptor

`MainTask_entry()` passes each `TaskDescriptor` selected from the startup list to `pal_CreateTaskFromDescriptor()`. Based on the PAL task information stored in the descriptor, this function prepares the stack, event group, and TCB and creates the actual RTOS task.

```c
/* Setting prototype: int pal_CreateTaskFromDescriptor(TaskDescriptor *task, int resume) */

int pal_CreateTaskFromDescriptor(TaskDescriptor *task,int resume)

{
  TaskDescriptor *pTVar1;
  short sVar2;
  short extraout_r0;
  void *pvVar3;
  uint uVar4;
  int iVar5;
  
  if (task->name == (char *)0x0) {
    pal_FatalAssert(0x11,"../../../VARIANT/PALVar/Platform_EV/PAL/TaskManager/src/pal_TaskManager.c"
                    ,0x4d7);
  }
  if (task->stack_base == (void *)0x0) {
    pvVar3 = (void *)thunk_FUN_0401622e(4,task->stack_size,
                                        "../../../VARIANT/PALVar/Platform_EV/PAL/TaskManager/src/pal _TaskManager.c"
                                        ,0x4dc);
    task->stack_base = pvVar3;
    if ((pvVar3 != (void *)0x0) ||
       (pal_FatalAssert(0x21,
                        "../../../VARIANT/PALVar/Platform_EV/PAL/TaskManager/src/pal_TaskManager.c",
                        0x4de), task->stack_base != (void *)0x0)) {
      MemClearZero(task->stack_base,task->stack_size);
    }
    task->flags = task->flags | 1;
  }
  task->event_group[0] = 0;
  task->event_group[1] = 0;
  task->event_group[2] = 0;
  task->event_group[3] = 0;
  task->event_group[4] = 0;
  task->event_group[5] = 0;
  task->event_group[6] = 0;
  task->event_group[7] = 0;
  task->event_group[8] = 0;
  task->event_group[9] = 0;
  task->event_group[10] = 0;
  task->event_group[0xb] = 0;
  task->event_group[0xc] = 0;
  task->event_group[0xd] = 0;
  task->event_group[0xe] = 0;
  task->event_group[0xf] = 0;
  task->event_group[0x10] = 0;
  task->event_group[0x11] = 0;
  task->event_group[0x12] = 0;
  task->event_group[0x13] = 0;
  task->event_group[0x14] = 0;
  task->event_group[0x15] = 0;
  task->event_group[0x16] = 0;
  task->event_group[0x17] = 0;
  task->event_group[0x18] = 0;
  task->event_group[0x19] = 0;
  task->event_group[0x1a] = 0;
  task->event_group[0x1b] = 0;
  task->event_group[0x1c] = 0;
  task->event_group[0x1d] = 0;
  task->event_group[0x1e] = 0;
  task->event_group[0x1f] = 0;
  task->event_group[0x20] = 0;
  task->event_group[0x21] = 0;
  task->event_group[0x22] = 0;
  task->event_group[0x23] = 0;
  sVar2 = OS_Create_Event_Group(task->event_group,&DAT_40cc8604);
  if (sVar2 != 0) {
    pal_FatalAssert((int)sVar2,
                    "../../../VARIANT/PALVar/Platform_EV/PAL/TaskManager/src/pal_TaskManager.c",
                    0x5dd);
  }
  memset_zero(&task->tcb,0x78);
  pvVar3 = task->stack_base;
  uVar4 = task->stack_size - 8 & 0xfffffff8;
  if (((uint)pvVar3 & 7) != 0) {
    uVar4 = uVar4 - 8;
    pvVar3 = (void *)((int)pvVar3 + 8U & 0xfffffff8);
  }
  OS_CreateTaskWrapper
            (&task->tcb,task->name,(void *)0x40cc83ef,0,task,(int)pvVar3 + 4,uVar4,
             (uint)task->priority,0,10,0);
  iVar5 = (int)extraout_r0;
  if (iVar5 == 0) {
    task->self_guard = task;
    (task->tcb).user_context = task;
    thunk_FUN_0401646e(task);
    task->state = 2;
    pTVar1 = DAT_417fc73c;
    if (g_palActiveTaskList == 0) {
      pal_FatalAssert(0xfffff409,"../../../VARIANT/PALVar/Platform_EV/PAL/inc/pal_list.h",0x1e6);
    }
    DAT_417fc73c = task;
    task->list_next = (TaskDescriptor *)&g_palActiveTaskList;
    task->list_prev = pTVar1;
    pTVar1->list_next = task;
    DAT_417fc714 = DAT_417fc714 + 1;
    if (resume == 0) {
      iVar5 = 0;
    }
    else {
      sVar2 = OS_Resume_Task(&task->tcb);
      iVar5 = (int)sVar2;
      if (iVar5 != 0) {
        FUN_405705dc(0xfffff40b,iVar5,task);
        return iVar5;
      }
      iVar5 = 0;
    }
  }
  else {
    if ((task->flags & 1) != 0) {
      FUN_40cc91d4(&task->stack_base,
                   "../../../VARIANT/PALVar/Platform_EV/PAL/TaskManager/src/pal_TaskManager.c",0x626
                  );
    }
    task->name = (char *)0x0;
    task->self_guard = (TaskDescriptor *)0x0;
    (task->tcb).user_context = (void *)0x0;
    pal_FatalAssert(iVar5,
                    "../../../VARIANT/PALVar/Platform_EV/PAL/TaskManager/src/pal_TaskManager.c",
                    0x62e);
  }
  return iVar5;
}
```

`TaskDescriptor` is a management structure that represents one task at the PAL layer. In addition to PAL information such as the task name, priority, stack information, and callbacks, the event group and `TCB` used by the RTOS scheduler are also embedded in the descriptor.

The reconstructed descriptor structure is as follows.

```c
typedef struct TaskDescriptor {
    struct TaskDescriptor *list_next;  // 0x000
    struct TaskDescriptor *list_prev;  // 0x004

    uint8_t state;                     // 0x008
                                       // 0=free, 1=cleanup pending, 2=active/created

    uint8_t flags;                     // 0x009
                                       // bit0=manager allocated stack
                                       // bit1=static task
                                       // bit2=create suspended

    uint16_t reserved_0a;              // 0x00A

    uint32_t task_index;               // 0x00C

    void *stack_base;                  // 0x010
    uint8_t reserved_14[16];           // 0x014

    char *name;                        // 0x024

    uint8_t priority;                  // 0x028
    uint8_t reserved_29[3];            // 0x029

    uint32_t stack_size;               // 0x02C

    void (*main_entry)
        (struct TaskDescriptor *task); // 0x030

    void (*pre_start_entry)
        (struct TaskDescriptor *task); // 0x034

    void *user_field_38;               // 0x038

    uint8_t event_group[36];           // 0x03C
    uint8_t reserved_60[40];           // 0x060

    TCB tcb;                           // 0x088

    struct TaskDescriptor *self_guard; // 0x100
    uint32_t reserved_104;             // 0x104
} TaskDescriptor;                      // size: 0x108
```

`pal_CreateTaskFromDescriptor()` first checks the task name and stack.

```c
if (task->name == NULL) {
    pal_FatalAssert(...);
}

if (task->stack_base == NULL) {
    task->stack_base = alloc(task->stack_size);
    MemClearZero(task->stack_base, task->stack_size);
    task->flags |= 1;
}
```

If no stack has been specified in advance, a region of `stack_size` bytes is dynamically allocated, and bit 0 of `flags` is set to indicate that the stack was allocated by the task manager.

The event group and TCB inside the descriptor are then initialized.

```c
memset(task->event_group, 0, 0x24);
OS_Create_Event_Group(task->event_group, &DAT_40cc8604);

memset_zero(&task->tcb, 0x78);
```

After aligning the stack address and size to an 8-byte boundary, `OS_CreateTaskWrapper()` is called.

```c
OS_CreateTaskWrapper(
    &task->tcb,
    task->name,
    (void *)0x40cc83ef,
    0,
    task,
    aligned_stack + 4,
    aligned_size,
    task->priority,
    0,
    10,
    0
);
```

The registered entry point `0x40CC83EF` is not the task-specific `main_entry`. Instead, it is `pal_TaskEntryWrapper()`, which is shared by all PAL tasks. Because `autostart` is 0, only the task's TCB and initial context are created at this stage.

If task creation succeeds, the descriptor and TCB are connected, and the task is registered in the active task list.

```c
task->self_guard = task;
task->tcb.user_context = task;
task->state = 2;
```

Because `TCB.user_context` points to the `TaskDescriptor`, `pal_TaskEntryWrapper()` can later locate the PAL descriptor from the current TCB and call its `pre_start_entry` and `main_entry`.

Finally, the `resume` argument is checked.

```c
if (resume != 0) {
    OS_Resume_Task(&task->tcb);
}
```

If `resume` is 1, the task is transitioned into the ready state. If it is 0, the task remains only in the created state. Therefore, the execution behavior of immediate and deferred tasks is determined by the previously examined `flags & 0x04` value.

```c
/* Setting prototype: short OS_Resume_Task(TCB *tcb) */

short OS_Resume_Task(TCB *tcb)

{
  bool bVar1;
  int in_interrupt_context;
  undefined4 uVar2;
  undefined4 uVar3;
  undefined4 extraout_r3;
  undefined4 unaff_r4;
  uint task_id;
  int panic_context;
  
  in_interrupt_context = thunk_OS_IsInInterruptContext();
  panic_context = DAT_410975d0;
  if (in_interrupt_context != 0) {
    software_interrupt(1);
    DataMemoryBarrier(0x1f);
    *(undefined4 *)(DAT_410975d0 + 8) = DAT_410975cc;
    FUN_4056fa8e(panic_context);
  }
  uVar2 = Scheduler_GetCurrentTaskId();
  task_id = (uint)tcb->task_id;
  uVar3 = disable_interrupt();
  Scheduler_SetReady(task_id);
  bVar1 = Scheduler_ShouldPreempt(task_id);
  if (bVar1) {
    Scheduler_PreemptToTask(uVar2,1,task_id,extraout_r3,unaff_r4);
  }
  else {
    RestoreInterrupts(uVar3);
  }
  return 0;
}
```

The function first checks whether it was called inside an interrupt handler.

```c
if (OS_IsInInterruptContext() != 0) {
    /* fatal processing */
}
```

Because `OS_Resume_Task()` modifies the ready bitmap and can immediately trigger context switching, its use is prohibited in interrupt context. If additional task processing is required from an interrupt, a separate path such as the previously created HISR workers must be used.

The function then obtains the ID of the currently executing task and the ID of the task to be resumed and disables interrupts.

```c
current_task_id = Scheduler_GetCurrentTaskId();
task_id = tcb->task_id;
irq_state = disable_interrupt();
```

The new task is then registered in the scheduler's ready state.

```c
Scheduler_SetReady(task_id);
```

During this process, the ready bitmap and ready word corresponding to the task ID are set, allowing the scheduler to select the task as an execution target.

The function then checks whether the new task should execute before the current task.

```c
if (Scheduler_ShouldPreempt(task_id)) {
    Scheduler_PreemptToTask(current_task_id, 1, task_id, ...);
}
```

If the scheduler determines that preemption is required, it saves the context of the current task and immediately switches to the new task. If preemption is not required, it only restores the interrupt state and continues execution of the current task.

```c
else {
    RestoreInterrupts(irq_state);
}
```

---

## pal_TaskEntryWrapper

The address `0x40CC83EF`, registered by `OS_CreateTaskWrapper()` as the common entry point of every PAL task, is `pal_TaskEntryWrapper()`. When the scheduler executes a new task for the first time, it does not directly enter the task-specific `main_entry`. Instead, it first passes through this wrapper.

```c
/* Setting prototype: void pal_TaskEntryWrapper(void) */

void pal_TaskEntryWrapper(void)

{
  TaskDescriptor *task;
  
  task = pal_GetCurrentTaskDescriptor();
  thunk_pal_TaskEntryInitContext();
  if (task->pre_start_entry != Reset) {
    (*task->pre_start_entry)(task);
  }
  FUN_4056f7f8(&DAT_40cc85f8);
  if (g_palStartupBarrierActive != 0) {
    if (g_palStaticTaskCount == 0) {
      pal_FatalAssert(0x11,
                      "../../../VARIANT/PALVar/Platform_EV/PAL/TaskManager/src/pal_TaskManager.c",
                      0x6c4);
    }
    if (DAT_417fc710 == 0) {
      create_semaphore(&g_palStartupGateSem,&DAT_40cc85fc,0);
    }
    DAT_417fc710 = DAT_417fc710 + 1;
    if ((g_palStaticTaskCount - DAT_417fc71c) - g_palDeferredStartupTaskCount == DAT_417fc710) {
      pal_SmRelease(g_palStartupSyncSem);
    }
    pal_SmObtain(g_palStartupGateSem);
    pal_SmRelease(g_palStartupGateSem);
    DAT_417fc710 = DAT_417fc710 + -1;
    if (DAT_417fc710 == 0) {
      pal_SmDelete(g_palStartupGateSem);
      pal_SmRelease(g_palStartupSyncSem);
    }
  }
  if (task->main_entry != Reset) {
    (*task->main_entry)(task);
  }
  OS_SemaphoreObtainImpl(&DAT_432275b4,1);
  OS_SemaphoreObtainImpl(&DAT_432275b4,1);
  pal_TaskExitAndCleanup(task);
  return;
}
```

First, it obtains the `TaskDescriptor` associated with the current task through the `user_context` of the currently executing TCB and configures the initial context required for PAL task execution.

```c
task = pal_GetCurrentTaskDescriptor();
thunk_pal_TaskEntryInitContext();
```

If a `pre_start_entry` is registered in the descriptor, it is called.

```c
if (task->pre_start_entry != Reset) {
    (*task->pre_start_entry)(task);
}
```

`pre_start_entry` is a callback that performs task-specific initial configuration before the actual `main_entry` is executed. Tasks without a registered callback skip this step. The `Reset` symbol shown by the decompiler is a misinterpretation by Ghidra of `0x0` or `NULL`, apparently confusing it with the Reset Vector.

After `pre_start_entry()` finishes, the function prints a trace and checks whether the startup barrier is active.

```c
FUN_4056f7f8(&DAT_40cc85f8);

if (g_palStartupBarrierActive != 0) {
    ...
}
```

If `g_palStartupBarrierActive` is 0, startup synchronization is skipped, and execution proceeds directly to `main_entry()`. If the value is 1, the current task participates in a barrier that synchronizes its start time with the other static tasks.

When the first task reaches the barrier, a startup gate semaphore with an initial count of 0 is created.

```c
if (DAT_417fc710 == 0) {
    create_semaphore(
        &g_palStartupGateSem,
        &DAT_40cc85fc,
        0
    );
}

DAT_417fc710++;
```

`DAT_417FC710` represents the number of tasks that have currently arrived at the barrier. Because the gate semaphore's count is 0, the tasks enter the waiting state at the subsequent `pal_SmObtain()` call.

When the final immediate task reaches the barrier, it releases `g_palStartupSyncSem`, or `PALTskSs`.

```c
if ((g_palStaticTaskCount - DAT_417fc71c) -
    g_palDeferredStartupTaskCount == DAT_417fc710) {

    pal_SmRelease(g_palStartupSyncSem);
}
```

The number of tasks that actually participate in the barrier is calculated by subtracting the deferred tasks and the tasks excluded from startup from the total number of static tasks. When the final task releases `PALTskSs`, `MainTask`, which is waiting on the semaphore, returns to the ready state.

Each static task then waits at the startup gate.

```c
pal_SmObtain(g_palStartupGateSem);
pal_SmRelease(g_palStartupGateSem);
```

After `MainTask` executes the startup callback and releases the gate, the waiting tasks pass the semaphore to one another and sequentially pass through the barrier.

A task that passes through the barrier decreases the number of waiting tasks.

```c
DAT_417fc710--;

if (DAT_417fc710 == 0) {
    pal_SmDelete(g_palStartupGateSem);
    pal_SmRelease(g_palStartupSyncSem);
}
```

When the final task passes through, the gate semaphore is deleted, and `PALTskSs` is released again. This second release informs `MainTask` that every task has exited the barrier.

After startup barrier processing is complete, the actual task entry registered in the descriptor is executed.

```c
if (task->main_entry != Reset) {
    (*task->main_entry)(task);
}
```

`main_entry` is the callback that performs the actual behavior of each PAL task. In general, it executes a loop that waits for messages or events and therefore frequently does not return.

If `main_entry()` returns, the task obtains `VoidSem` twice and then moves to the task termination and cleanup function.

```c
OS_SemaphoreObtainImpl(&DAT_432275b4, 1);
OS_SemaphoreObtainImpl(&DAT_432275b4, 1);
pal_TaskExitAndCleanup(task);
```

---

## MainTask Startup Completion

When all immediate tasks arrive at the startup barrier, the final task releases `g_palStartupSyncSem`, returning the waiting `MainTask` to the ready state.

When `MainTask` executes again, it calls the startup callback, marks the barrier as complete, and releases the gate semaphore on which the static tasks are waiting.

```c
pal_SmObtain(g_palStartupSyncSem);

(*DAT_417fc720)();

g_palStartupBarrierActive = 0;
pal_SmRelease(g_palStartupGateSem);
```

When `g_palStartupGateSem` is released, the waiting static tasks sequentially pass through the barrier and execute their respective `main_entry()` functions.

`MainTask` obtains `g_palStartupSyncSem` again and waits until all tasks have exited the gate.

```c
pal_SmObtain(g_palStartupSyncSem);
pal_SmDelete(g_palStartupSyncSem);
```

When the final static task passes through the barrier, it releases `g_palStartupSyncSem` again, waking `MainTask`. `MainTask` then deletes the semaphore used for startup synchronization and enters `pal_TaskReaperLoop()`.

After completing static task startup, `MainTask` operates as a management task that cleans up PAL tasks for which termination has been requested.

```c
/* Setting prototype: void pal_TaskReaperLoop(void) */

void pal_TaskReaperLoop(void)

{
  TaskDescriptor *task;
  short status;
  int destroy_status;
  undefined1 auStack_28 [8];
  undefined1 auStack_20 [4];
  undefined1 auStack_1c [4];
  undefined1 auStack_18 [4];
  undefined1 auStack_14 [4];
  undefined1 auStack_10 [4];
  undefined1 auStack_c [4];
  undefined1 auStack_8 [4];
  undefined1 auStack_4 [4];
  
  do {
    pal_SmObtain(g_palTaskCleanupSem);
    pal_SmObtain(g_palTaskManagerMutexSem);
    task = g_palActiveTaskList;
    if (g_palActiveTaskList == (TaskDescriptor *)&g_palActiveTaskList) {
      pal_FatalAssert(0xfffff405,"../../../VARIANT/PALVar/Platform_EV/PAL/inc/pal_list.h",0x12a);
      task = g_palActiveTaskList;
    }
    for (; task != (TaskDescriptor *)0x0; task = task->list_next) {
      status = FUN_410972d4(&task->tcb,auStack_28,auStack_20,auStack_1c,auStack_18,auStack_14,
                            auStack_10,auStack_c,auStack_8,auStack_4);
      if (status != 0) {
        FUN_405705dc(0xfffff40b,(int)status,task);
      }
      if (task->state == 1) {
        destroy_status = pal_DestroyTaskDescriptor(task);
        if (destroy_status != 0) {
          FUN_405705dc(destroy_status,task,0);
        }
        break;
      }
      if (task->list_next->list_next == task) {
        pal_FatalAssert(0xfffff406,"../../../VARIANT/PALVar/Platform_EV/PAL/inc/pal_list.h",0x156);
      }
    }
    pal_SmRelease(g_palTaskManagerMutexSem);
  } while( true );
}
```

First, the function waits for `g_palTaskCleanupSem`, or `"PALTskCs"`.

```c
pal_SmObtain(g_palTaskCleanupSem);
```

Because the initial count is 0, `MainTask` normally waits in the semaphore's wait list. When a PAL task requests termination and cleanup, the semaphore is released, and `MainTask` returns to the ready state.

It then obtains the task manager mutex and iterates through the active task list.

```c
pal_SmObtain(g_palTaskManagerMutexSem);

task = g_palActiveTaskList;

for (; task != NULL; task = task->list_next) {
    ...
}
```

When a task whose descriptor has `state == 1` is found, the task is removed.

```c
if (task->state == 1) {
    pal_DestroyTaskDescriptor(task);
    break;
}
```

`state == 1` indicates that the task has terminated and is waiting for cleanup. `pal_DestroyTaskDescriptor()` is considered to clean up the task's OS objects and stack, remove the descriptor from the active list, and return it to a reusable state.

After cleanup is complete, the mutex is released, and the function waits for the cleanup semaphore again.

As a result, `MainTask_entry()` transitions the PAL runtime and static tasks into the executable state and then continues operating without returning, managing the task lifecycle as a background task inside `pal_TaskReaperLoop()`.
