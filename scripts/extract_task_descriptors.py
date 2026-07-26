import argparse
import struct

parser = argparse.ArgumentParser(
    description="Extract Shannon task descriptors"
)
parser.add_argument(
    "bin",
    help="Path to modem.bin"
)
args = parser.parse_args()

BIN = args.bin

LOAD_BIAS = 0x4000DBE0
DESC_VA = 0x418077A8
DESC_OFF = DESC_VA - LOAD_BIAS
DESC_SIZE = 0x108
MAX_DESC = 500


def va_to_off(va):
    return va - LOAD_BIAS


def read_u32(data, off):
    return struct.unpack_from("<I", data, off)[0]


def read_cstr(data, va, max_len=128):
    if va == 0:
        return ""

    off = va_to_off(va)

    if off < 0 or off >= len(data):
        return f"<bad_va:0x{va:08X}>"

    end = off
    limit = min(len(data), off + max_len)

    while end < limit and data[end] != 0:
        end += 1

    return data[off:end].decode("ascii", errors="replace")


with open(BIN, "rb") as f:
    data = f.read()


for i in range(MAX_DESC):
    off = DESC_OFF + i * DESC_SIZE

    name_va = read_u32(data, off + 0x24)

    if name_va == 0:
        print(f"end at index {i}")
        break

    priority = read_u32(data, off + 0x28)
    stack_size = read_u32(data, off + 0x2C)
    main_entry = read_u32(data, off + 0x30)
    pre_entry = read_u32(data, off + 0x34)
    flags = data[off + 0x09]

    name = read_cstr(data, name_va)

    print(
        f"[{i:03d}] "
        f"desc_va=0x{DESC_VA + i * DESC_SIZE:08X} "
        f"name={name!r} "
        f"prio={priority} "
        f"stack=0x{stack_size:X} "
        f"flags=0x{flags:02X} "
        f"main=0x{main_entry:08X} "
        f"pre=0x{pre_entry:08X}"
    )