#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the APT/Sileo repo metadata in docs/ from every .deb in docs/debs/.
Generates Packages, Packages.gz, Packages.bz2 and a Release file.
Serve docs/ over HTTPS (e.g. GitHub Pages) and add that URL as a Sileo source."""
import os, gzip, bz2, hashlib, lzma, tarfile, io

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(HERE, "docs")
DEBS = os.path.join(DOCS, "debs")

REPO = {
    "Origin": "dcoff repo",
    "Label": "dcoff",
    "Suite": "stable",
    "Version": "1.0",
    "Codename": "ios",
    "Architectures": "iphoneos-arm64 iphoneos-arm64e",
    "Components": "main",
    "Description": "made with ❤️ by notaudren",
}

def read_control(deb_path):
    data = open(deb_path, "rb").read()
    off = 8; mem = {}
    while off < len(data):
        h = data[off:off+60]; off += 60
        n = h[0:16].decode().strip(); s = int(h[48:58].decode().strip())
        mem[n] = data[off:off+s]; off += s
        if off % 2: off += 1
    ctl_raw = None
    for key in ("control.tar.gz", "control.tar.xz", "control.tar.lzma"):
        if key in mem:
            blob = mem[key]
            raw = gzip.decompress(blob) if key.endswith(".gz") else lzma.decompress(blob)
            ctl_raw = raw; break
    t = tarfile.open(fileobj=io.BytesIO(ctl_raw))
    for m in t.getmembers():
        if m.name.lstrip("./") == "control":
            return t.extractfile(m).read().decode("utf-8")
    raise RuntimeError("no control in " + deb_path)

def parse_control(text):
    fields = {}
    for line in text.splitlines():
        if line and not line.startswith(" ") and ":" in line:
            k, v = line.split(":", 1)
            fields[k.strip()] = v.strip()
    return fields

def hashes(blob):
    return (hashlib.md5(blob).hexdigest(),
            hashlib.sha1(blob).hexdigest(),
            hashlib.sha256(blob).hexdigest())

def main():
    debs = sorted(f for f in os.listdir(DEBS) if f.endswith(".deb"))
    if not debs:
        raise SystemExit("no .deb in " + DEBS)
    stanzas = []
    # field order APT/Sileo likes
    order = ["Package", "Version", "Architecture", "Name", "Description",
             "Author", "Maintainer", "Section", "Depends", "Installed-Size"]
    for deb in debs:
        path = os.path.join(DEBS, deb)
        blob = open(path, "rb").read()
        c = parse_control(read_control(path))
        md5, sha1, sha256 = hashes(blob)
        lines = []
        for k in order:
            if k in c:
                lines.append(f"{k}: {c[k]}")
        for k, v in c.items():
            if k not in order:
                lines.append(f"{k}: {v}")
        lines.append(f"Filename: debs/{deb}")
        lines.append(f"Size: {len(blob)}")
        lines.append(f"MD5sum: {md5}")
        lines.append(f"SHA1: {sha1}")
        lines.append(f"SHA256: {sha256}")
        stanzas.append("\n".join(lines))
        print(f"[+] indexed {deb} ({len(blob)} bytes)")

    packages = ("\n\n".join(stanzas) + "\n").encode("utf-8")
    open(os.path.join(DOCS, "Packages"), "wb").write(packages)
    gzb = gzip.compress(packages, mtime=0)
    open(os.path.join(DOCS, "Packages.gz"), "wb").write(gzb)
    bzb = bz2.compress(packages)
    open(os.path.join(DOCS, "Packages.bz2"), "wb").write(bzb)

    rel = "\n".join(f"{k}: {v}" for k, v in REPO.items()) + "\n"
    files = {"Packages": packages, "Packages.gz": gzb, "Packages.bz2": bzb}
    rel += "MD5Sum:\n"
    for n, b in files.items():
        rel += f" {hashlib.md5(b).hexdigest()} {len(b)} {n}\n"
    rel += "SHA256:\n"
    for n, b in files.items():
        rel += f" {hashlib.sha256(b).hexdigest()} {len(b)} {n}\n"
    open(os.path.join(DOCS, "Release"), "wb").write(rel.encode("utf-8"))

    print("[OK] wrote Packages / Packages.gz / Packages.bz2 / Release in", DOCS)

if __name__ == "__main__":
    main()
