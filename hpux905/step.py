"""One console interaction: mark log, send keys, wait for a regex, print cleaned screen text.

  step.py KEYS REGEX [SECS] [TAILCHARS]
  KEYS may be "" to send nothing. Escapes \\r \\n \\e are honoured (see con.py).
"""
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import con  # noqa: E402


def clean(t):
    t = re.sub(r"\x1b\[[0-9;?]*[A-Za-z@]", "\n", t)
    t = re.sub(r"\x1b[()][0-9A-Za-z]", "", t)
    t = re.sub(r"\x1b.", "", t)
    t = t.replace("\r", "").replace("\x0f", "").replace("\x0e", "")
    t = re.sub(r"[ \t]+\n", "\n", t)
    return re.sub(r"\n\s*\n+", "\n", t)


def main(argv):
    keys = argv[1]
    regex = re.compile(argv[2], re.M)
    secs = float(argv[3]) if len(argv) > 3 else 120
    tail = int(argv[4]) if len(argv) > 4 else 2500
    con.cmd_mark()
    start = con.get_mark()
    if keys:
        con.cmd_send(keys)
    end = time.time() + secs
    ok = False
    while time.time() < end:
        time.sleep(1.5)
        if regex.search(clean(con.read_log(start))):
            time.sleep(1.5)  # let the rest of the screen arrive
            ok = True
            break
    print("MATCHED" if ok else "TIMEOUT")
    print(clean(con.read_log(start))[-tail:])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
