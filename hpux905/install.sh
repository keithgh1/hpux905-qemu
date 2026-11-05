# Unattended HP-UX 9.05 install, sourced by hpux905 (needs machine_args,
# start_bg, stop_bg). Each step sends keys on the serial console and waits
# for a regex; screen text goes to /data/install.log.

LOG=$DATA/install.log
: > "$LOG"
P='#\s*$'

step() {   # label keys regex secs
    printf '[%s] %s\n' "$(date +%T)" "$1"
    if ! python3 -I "$HERE/step.py" "$2" "$3" "$4" >> "$LOG" 2>&1; then
        echo "error: timed out at step '$1'; last screen:" >&2
        tail -25 "$LOG" >&2
        stop_bg
        exit 1
    fi
}

# Log in on the serial console as root; .profile asks for the terminal type.
login_root() {
    step "log in as root" "root\r" "\[y/n\]:" 120
    step "terminal: not HP" "n\r" "default: \"80\"" 60
    step "columns" "80\r" "default \"24\"" 60
    step "lines" "24\r" "$P" 60
    step "erase/kill keys" "stty erase '^H' kill '^U'\n" "$P" 30
}

echo "== 1/4 Install CD: prepare disk, copy base system"
machine_args d /tmp/install.iso
start_bg "${TEXT_ARGS[@]}"
step "boot Install CD" "" "terminal type" 300
step "terminal type VT100" "4\r" "Press any key" 120
step "EISA note" "\r" "Press any key" 120
step "welcome" "\r" "Enter selection" 300
step "root disk SEAGATE ST12400N" "\r" "long filenames" 180
step "long file names" "y\r" "Root Disk Swap space" 120
step "accept swap" "\x18" "Do you wish to continue" 120
step "copy base system" "y\r" "Rebooting system to hard disk" 1200
step "reboot to disk" "" 'Press "Return" to continue' 900

echo "== 2/4 Core CD: load all filesets"
python3 -I "$HERE/con.py" mon 'change scsi0-cd2 /tmp/core.iso raw read-only' >/dev/null
step "update main menu" "\r" "Main Menu" 600
step "select all filesets" "\r" "Start Loading Now" 300
step "start loading" "\r" "Start loading filesets now\?" 600
step "load, build kernel, reboot" "y" "Are you ready to link this system to a network\?" 7200

echo "== 3/4 First boot: system parameters"
R='then press \[Return\]'
step "no network" "n\r" "$R" 120
step "continue" "y\r" "$R" 120
step "host name hp715" "hp715\r" "$R" 120
step "confirm" "y\r" "$R" 120
step "North America" "1\r" "$R" 120
step "Eastern time" "3\r" "$R" 120
step "confirm" "y\r" "$R" 120
step "keep clock" "y\r" "$R" 120
step "no root password" "n\r" "Console Login:" 600
login_root
step "default run level 4 (VUE)" "sed 's/^init:[0-9]:initdefault:/init:4:initdefault:/' /etc/inittab > /tmp/it && cp /tmp/it /etc/inittab && sed -n 1p /etc/inittab\n" "$P" 30
step "halt" "cd /; sync; sync; /etc/shutdown -h -y 0\n" "Halted" 300
stop_bg

echo "== 4/4 First graphical boot: keyboard layout"
machine_args c ""
start_bg "${GFX_ARGS[@]}"
step "boot to keyboard prompt" "" "(PS2_DIN_US_English|Console Login:)" 1800
if tail -15 "$LOG" | grep -q PS2_DIN_US_English; then
    step "PS/2 US English" "\r" "Console Login:" 1800
fi
login_root
step "halt" "cd /; sync; sync; /etc/shutdown -h -y 0\n" "Halted" 300
stop_bg

echo "Install complete: $DISK"
