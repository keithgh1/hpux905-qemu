"""Drive the guest serial console and HMP monitor of a background guest.

Output is captured by QEMU's chardev logfile ($SERIAL_LOG); this tool
only sends input and polls the log.

  con.py send TEXT        send TEXT (\\r, \\n, \\e escapes honoured)
  con.py wait REGEX SECS  wait until REGEX matches log text written after the
                          last 'mark' (or start of file); prints the tail
  con.py mark             record current log size as the wait origin
  con.py tail [N]         print last N lines (default 40)
  con.py mon CMD          send a HMP monitor command, print reply
"""
import os
import re
import socket
import sys
import time

LOG = os.environ.get("SERIAL_LOG", "/data/serial.log")
MARK = os.environ.get("SERIAL_MARK", "/tmp/serial.mark")
SER_PORT = 4555
MON_PORT = 4556


def unescape(s):
    s = s.replace("\\r", "\r").replace("\\n", "\n").replace("\\e", "\x1b")
    return re.sub(r"\\x([0-9a-fA-F]{2})", lambda m: chr(int(m.group(1), 16)), s)


def read_log(start=0):
    try:
        with open(LOG, "rb") as f:
            f.seek(start)
            return f.read().decode("latin-1")
    except FileNotFoundError:
        return ""


def get_mark():
    try:
        return int(open(MARK).read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def cmd_send(text):
    with socket.create_connection(("127.0.0.1", SER_PORT), timeout=5) as s:
        # slow per-char send; old serial input paths drop bursts
        for ch in unescape(text):
            s.sendall(ch.encode("latin-1"))
            time.sleep(0.03)
        time.sleep(0.2)


def cmd_mark():
    size = os.path.getsize(LOG) if os.path.exists(LOG) else 0
    with open(MARK, "w") as f:
        f.write(str(size))


def cmd_wait(regex, secs):
    pat = re.compile(regex, re.M)
    start = get_mark()
    end = time.time() + float(secs)
    while time.time() < end:
        if pat.search(read_log(start)):
            print("MATCHED")
            cmd_tail(30, start)
            return 0
        time.sleep(1)
    print("TIMEOUT")
    cmd_tail(30, start)
    return 1


def cmd_tail(n=40, start=0):
    text = read_log(start).replace("\r", "")
    print("\n".join(text.split("\n")[-int(n):]))


def cmd_mon(command):
    with socket.create_connection(("127.0.0.1", MON_PORT), timeout=5) as s:
        s.settimeout(1.0)
        buf = b""
        try:
            while True:
                d = s.recv(4096)
                if not d:
                    break
                buf += d
        except socket.timeout:
            pass
        s.sendall(command.encode() + b"\n")
        time.sleep(1.0)
        out = b""
        try:
            while True:
                d = s.recv(65536)
                if not d:
                    break
                out += d
        except socket.timeout:
            pass
        print(out.decode("latin-1").replace("\r", ""))


def cmd_mon_quiet(command):
    """Send an HMP command without waiting for or printing its output."""
    with socket.create_connection(("127.0.0.1", MON_PORT), timeout=5) as s:
        s.sendall(command.encode() + b"\n")
        time.sleep(0.05)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    c = argv[1]
    if c == "send":
        cmd_send(argv[2])
    elif c == "mark":
        cmd_mark()
    elif c == "wait":
        return cmd_wait(argv[2], argv[3])
    elif c == "tail":
        cmd_tail(argv[2] if len(argv) > 2 else 40)
    elif c == "mon":
        cmd_mon(" ".join(argv[2:]))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
