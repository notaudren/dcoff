#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rename dcneuter -> dcoff inside the prebuilt .deb (no device / no Theos needed).
Pure archive surgery: rename the dylib+plist members and rewrite the control file.
Outputs a clean ar(.deb) with control.tar.gz + data.tar.gz."""
import lzma, gzip, tarfile, io, os, sys, time

SRC = os.environ.get("DCOFF_SRC_DEB",
    r"C:\Users\audre\dcneuter\com.audren.dcneuter_0.1.0_iphoneos-arm64e.deb")
OUT = os.environ.get("DCOFF_OUT_DEB",
    r"C:\Users\audre\dcoff\docs\debs\com.audren.dcoff_0.1.0_iphoneos-arm64e.deb")

NEW_CONTROL = (
    "Package: com.audren.dcoff\n"
    "Name: dcoff\n"
    "Version: 0.1.0\n"
    "Architecture: iphoneos-arm64e\n"
    "Description: made with \u2764\ufe0f by notaudren\n"
    "Maintainer: notaudren\n"
    "Author: notaudren\n"
    "Section: Tweaks\n"
    "Depends: ellekit\n"
    "Installed-Size: 200\n"
)

def read_ar(data):
    assert data[:8] == b"!<arch>\n", "not an ar archive"
    off = 8; out = {}
    while off < len(data):
        hdr = data[off:off+60]; off += 60
        name = hdr[0:16].decode().strip()
        size = int(hdr[48:58].decode().strip())
        out[name] = data[off:off+size]; off += size
        if off % 2: off += 1
    return out

def ar_member(name, blob):
    h = name.ljust(16).encode()
    h += str(int(time.time())).ljust(12).encode()
    h += b"0     "        # uid
    h += b"0     "        # gid
    h += b"100644  "      # mode
    h += str(len(blob)).ljust(10).encode()
    h += b"\x60\x0a"
    pad = b"\n" if len(blob) % 2 else b""
    return h + blob + pad

def rebuild_data_tar(raw):
    src = tarfile.open(fileobj=io.BytesIO(raw))
    buf = io.BytesIO()
    dst = tarfile.open(fileobj=buf, mode="w")
    for m in src.getmembers():
        nm = m.name
        if nm.endswith("dcneuter.dylib"):
            m.name = nm.replace("dcneuter.dylib", "dcoff.dylib")
        elif nm.endswith("dcneuter.plist"):
            m.name = nm.replace("dcneuter.plist", "dcoff.plist")
        f = src.extractfile(m) if m.isfile() else None
        dst.addfile(m, f)
    dst.close()
    return gzip.compress(buf.getvalue(), mtime=0)

def build_control_tar():
    buf = io.BytesIO()
    t = tarfile.open(fileobj=buf, mode="w")
    def add(name, text):
        b = text.encode("utf-8")
        ti = tarfile.TarInfo(name); ti.size = len(b); ti.mode = 0o644
        t.addfile(ti, io.BytesIO(b))
    dot = tarfile.TarInfo("."); dot.type = tarfile.DIRTYPE; dot.mode = 0o755
    t.addfile(dot)
    add("./control", NEW_CONTROL)
    t.close()
    return gzip.compress(buf.getvalue(), mtime=0)

def main():
    data = open(SRC, "rb").read()
    mem = read_ar(data)
    data_gz = rebuild_data_tar(lzma.decompress(mem["data.tar.lzma"]))
    ctl_gz = build_control_tar()
    out = b"!<arch>\n"
    out += ar_member("debian-binary", b"2.0\n")
    out += ar_member("control.tar.gz", ctl_gz)
    out += ar_member("data.tar.gz", data_gz)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "wb").write(out)
    # verify
    v = read_ar(open(OUT, "rb").read())
    dt = tarfile.open(fileobj=io.BytesIO(gzip.decompress(v["data.tar.gz"])))
    print("[OK] wrote", OUT, f"({len(out)} bytes)")
    print("data.tar members:")
    for m in dt.getmembers():
        if m.isfile():
            print("  ", m.name, m.size)
    print("control:")
    ct = tarfile.open(fileobj=io.BytesIO(gzip.decompress(v["control.tar.gz"])))
    print(ct.extractfile("./control").read().decode("utf-8"))

if __name__ == "__main__":
    main()
