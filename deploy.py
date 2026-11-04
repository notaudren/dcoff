#!/usr/bin/env python3
"""Build dcoff from src/ on-device via Theos, install into devicecheckd's injection scope.
Usage: python3 deploy.py <device-ip> [root-password]  (default root@<ip> / notaudren)"""
import os, sys, posixpath, paramiko, warnings
warnings.filterwarnings("ignore")

HOST = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.23"
PW   = sys.argv[2] if len(sys.argv) > 2 else "notaudren"
USER = "root"
HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, "src")
FILES = ["Tweak.x", "Makefile", "control", "dcoff.plist"]
RDIR = "/var/mobile/dcoff_build"

def main():
    c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username=USER, password=PW, timeout=15, look_for_keys=False, allow_agent=False)
    def run(cmd, t=300):
        i, o, e = c.exec_command(cmd, timeout=t)
        return (o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip()
    run(f"rm -rf {RDIR}; mkdir -p {RDIR}")
    sftp = c.open_sftp()
    for f in FILES: sftp.put(os.path.join(SRC, f), posixpath.join(RDIR, f)); print(f"[+] up {f}")
    sftp.close()
    print("[i] building ...")
    print(run(f"cd {RDIR} && export THEOS=/var/jb/opt/theos && rm -rf .theos packages && "
              f"make package FINALPACKAGE=1 THEOS_PACKAGE_ARCH=iphoneos-arm64e 2>&1 | tail -12"))
    deb = run(f"ls -1 {RDIR}/packages/*.deb 2>/dev/null").split()
    if not deb: print("[!] build FAILED"); c.close(); return
    deb = deb[-1]
    print("[i] installing + restarting devicecheckd ...")
    print(run(f"dpkg -i '{deb}' 2>&1; echo '--- installed ---'; dpkg -l | grep -i dcoff; "
              f"launchctl kickstart -k system/com.apple.devicecheckd 2>&1 || killall -9 devicecheckd 2>&1; echo done"))
    sftp = c.open_sftp(); sftp.get(deb, os.path.join(HERE, "docs", "debs", os.path.basename(deb))); sftp.close()
    print(f"[OK] pulled -> docs/debs/{os.path.basename(deb)}")
    c.close()

if __name__ == "__main__":
    main()
