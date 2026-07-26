#!/usr/bin/env python3

import argparse
import struct


DEFAULT_LOAD_BIAS = 0x4000DBE0
PTR_STATIC_ENTITY_TABLE = 0x410AC050
DEFAULT_MAX_ENTITIES = 500
ENTRY_SIZE = 0x14

TYPE_NAMES = {
    1: "queue",
    2: "direct_cb",
    3: "deferred_cb",
    4: "alias",
    5: "queue_signal",
}


def u32(data, off):
    if off < 0 or off + 4 > len(data):
        return None

    return struct.unpack_from("<I", data, off)[0]


def va_to_off(va, load_bias):
    return va - load_bias


def read_cstr(data, va, load_bias, max_len=64):
    off = va_to_off(va, load_bias)

    if off < 0 or off >= len(data):
        return None

    out = bytearray()

    for i in range(max_len):
        if off + i >= len(data):
            break

        b = data[off + i]

        if b == 0:
            break

        if b < 0x20 or b > 0x7E:
            return None

        out.append(b)

    if not out:
        return ""

    return out.decode("ascii", errors="replace")


def fmt_ptr(v):
    return f"0x{v:08X}"


def describe_type(entity_type, context, param):
    name = TYPE_NAMES.get(entity_type, "unknown")

    if entity_type == 1:
        return f"{name} queue_depth={param}"

    if entity_type == 2:
        return f"{name} callback={fmt_ptr(param)}"

    if entity_type == 3:
        return (
            f"{name} "
            f"context={fmt_ptr(context)} "
            f"callback={fmt_ptr(param)}"
        )

    if entity_type == 4:
        return f"{name} redirect_entity={param}"

    if entity_type == 5:
        return (
            f"{name} "
            f"signal_target={fmt_ptr(context)} "
            f"queue_depth={param}"
        )

    return name


def main():
    ap = argparse.ArgumentParser(
        description=(
            "Dump Samsung Shannon PAL "
            "static message entity descriptors"
        )
    )

    ap.add_argument("modem_bin")

    ap.add_argument(
        "--load-bias",
        type=lambda x: int(x, 0),
        default=DEFAULT_LOAD_BIAS,
    )

    ap.add_argument(
        "--ptr-va",
        type=lambda x: int(x, 0),
        default=PTR_STATIC_ENTITY_TABLE,
    )

    ap.add_argument(
        "--table-va",
        type=lambda x: int(x, 0),
        default=None,
    )

    ap.add_argument(
        "--max",
        type=int,
        default=DEFAULT_MAX_ENTITIES,
    )

    args = ap.parse_args()

    with open(args.modem_bin, "rb") as f:
        data = f.read()

    if args.table_va is None:
        ptr_off = va_to_off(
            args.ptr_va,
            args.load_bias,
        )

        table_va = u32(data, ptr_off)

        if table_va is None:
            raise SystemExit(
                "failed to read static table pointer at "
                f"{fmt_ptr(args.ptr_va)}"
            )
    else:
        table_va = args.table_va

    table_off = va_to_off(
        table_va,
        args.load_bias,
    )

    print(f"load_bias=0x{args.load_bias:08X}")
    print(
        "ptr_static_entity_table="
        f"{fmt_ptr(args.ptr_va)}"
    )
    print(
        "static_entity_table="
        f"{fmt_ptr(table_va)} "
        f"file_off=0x{table_off:X}"
    )
    print()

    for idx in range(args.max):
        desc_va = table_va + idx * ENTRY_SIZE
        desc_off = table_off + idx * ENTRY_SIZE

        name_ptr = u32(data, desc_off + 0x00)
        context = u32(data, desc_off + 0x04)
        type_raw = u32(data, desc_off + 0x08)
        param = u32(data, desc_off + 0x0C)
        extra = u32(data, desc_off + 0x10)

        fields = (
            name_ptr,
            context,
            type_raw,
            param,
            extra,
        )

        if any(v is None for v in fields):
            print(
                "end: incomplete descriptor "
                f"at index {idx}"
            )
            break

        if name_ptr == 0:
            print(f"end at index {idx}")
            break

        entity_type = type_raw & 0xFF

        name = read_cstr(
            data,
            name_ptr,
            args.load_bias,
        )

        if name is None:
            name = (
                "<non-string:"
                f"{fmt_ptr(name_ptr)}>"
            )

        desc = describe_type(
            entity_type,
            context,
            param,
        )

        print(
            f"[{idx:03d}] "
            f"entity_id={idx:3d} "
            f"desc_va={fmt_ptr(desc_va)} "
            f"name='{name}' "
            f"type={entity_type}"
            f"({TYPE_NAMES.get(entity_type, 'unknown')}) "
            f"context={fmt_ptr(context)} "
            f"param={fmt_ptr(param)} "
            f"extra={fmt_ptr(extra)} "
            f"; {desc}"
        )


if __name__ == "__main__":
    main()