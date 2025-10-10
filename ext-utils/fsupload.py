import serial, time, datetime, json, textwrap

FS_DOES_NOT_EXIST = 255
FS_FAILED_TO_OPEN_FILE = 254
FS_DIR_NOT_EMPTY = 253

def log(*s, pre="", **kw):
    now = datetime.datetime.now()
    t = "["+now.strftime("%H:%M:%S")+f".{now.microsecond//1000:03d}]"
    print(pre+t, *s, **kw)

def wrapText(s: str) -> bytes:
    lines = s.split('\n')
    out = b''
    for line in lines:
        sub = textwrap.wrap(line, width=32)
        for l in sub:
            out += l.encode(encoding="ascii") + b'\n'

    return out

def send_file(_s: serial.Serial, filename: str, data: bytes, print_return = False, verbose=False) -> int:
    _st = time.time()
    
    _s.timeout = 2
    if verbose:
        n = 0
        nextt = time.time()
        log("Starting upload.")
        log("Sending write command and filename")

    _s.write(b'Fw')
    idx = 0
    while True:
        i = filename[idx].encode(encoding="ascii")
        _s.write(i)
        # print("Write")
        _s.flush()
        r = _s.read().decode()
        if r == "":
            if verbose:
                log(f"[WARNING] Byte {idx} timed out. Retrying.", pre="\033[2K")
            continue
        if print_return:
            print(_s.read().decode(), end="", flush=True)
        idx += 1
        if idx == len(filename):
            break
    
    

    _s.write(b"\x00")
    if verbose:
        log("Waiting for filename ack...")
    
    # print(_s.read_all())
    ack = _s.read()[0]
    if ack == FS_FAILED_TO_OPEN_FILE:
        log("Failed to open file. Does the parent directory exist?")
        return ack
    
    l = len(data)
    lb = l.to_bytes(3, "big")

    
    if verbose:
        log("Data size:", l, "bytes")
    
    _s.write(lb)
    _s.flush()

    _s.reset_input_buffer()

    _s.timeout = 0.1
    idx = 0
    while True:
        i = data[idx]
        _s.write(bytearray([i]))
        # print("Write")
        _s.flush()
        # print("Wait")
        r = _s.read().decode()
        if r == "":
            if verbose:
                log(f"[WARNING] Byte {idx} timed out. Retrying.", pre="\033[2K")
            continue
        if print_return:
            print(_s.read().decode(), end="", flush=True)
            
        
        if verbose:
            now = time.time()
            if now > nextt:
                log(f"Uploading... ({round((n/l) * 100)}%) {n}/{l} bytes ({(n/(time.time()-_st))/1000:.03f} kB/s)\r", end="")
                nextt = now + 0.150
            n += 1
        idx += 1
        if idx == l:
            break
    if verbose:
        log(f"Uploading... (100.00%) {n}/{l} bytes (Average speed: {n/(time.time()-_st)/1000:.03f} kB/s)")
        log("Waiting for ACK.")
    
    _s.timeout = None
    _s.read()

    return 0

def getMap(mapString: str):
    lines = mapString.split("\n")
    line_data = [line.split("//")[0] for line in lines if line.split("//")[0]]
    
    map_data = {}

    for entry in line_data:
        entry_data = [i for i in entry.split() if i]
        if len(entry_data) < 2:
            raise ValueError("Invalid map format!")
        replacedChars = [i for i in entry_data[0].split(";") if i]
        for i in range(len(replacedChars)):
            item = replacedChars[i]
            if item[0:2] == "U+":
                replacedChars[i] = chr(int(item[2:], 16))
        
        replacedWith = entry_data[1]
        if replacedWith[0:2] == "U+":
            c = int(replacedWith[2:], 16)
            replacedWith = ""
            if c != 0:
                replacedWith = chr(c)

        for char in replacedChars:
            map_data[char] = replacedWith

    return map_data

def send_mkdir(_s: serial.Serial, path: str, verbose=False) -> int:
    _s.timeout = 2
    if verbose:
        n = 0
        nextt = time.time()
        log("Sending mkdir command")
    _s.write(b'Fm')

    if verbose:
        log("Sending path")

    idx = 0
    while True:
        i = path[idx].encode(encoding="ascii")
        _s.write(i)
        _s.flush()
        time.sleep(0.01)
        r = _s.read().decode()
        if r == "":
            if verbose:
                log(f"[WARNING] Byte {idx} timed out. Retrying.", pre="\033[2K")
                continue

        idx += 1
        if idx == len(path):
            break
    
    _s.write(b"\x00")

    if verbose:
        log("Waiting for ACK")

    _s.timeout = None
    
    time.sleep(0.01)

    ack = _s.read()[0]

    return ack

def send_delete(_s: serial.Serial, filename: str, verbose=False) -> int:
    _s.timeout = 2
    if verbose:
        n = 0
        nextt = time.time()
        log("Sending delete command")
    _s.write(b'Fd')

    if verbose:
        log("Sending filename")

    idx = 0
    while True:
        i = filename[idx].encode(encoding="ascii")
        _s.write(i)
        _s.flush()
        time.sleep(0.01)
        r = _s.read().decode()
        if r == "":
            if verbose:
                log(f"[WARNING] Byte {idx} timed out. Retrying.", pre="\033[2K")
                continue
            # r = _s.read().decode()
            # if r == "":
            #     log(f"[WARNING] Byte {idx} timed out. Second read failed. Skipping.", pre="\033[2K")

        idx += 1
        if idx == len(filename):
            break
    
    _s.write(b"\x00")

    if verbose:
        log("Waiting for ACK")

    _s.timeout = None
    
    time.sleep(0.01)

    ack = _s.read()[0]

    return ack

def send_list(_s: serial.Serial, path: str, verbose=False) -> bytes:
    data = b""
    _s.timeout = 2
    if verbose:
        n = 0
        nextt = time.time()
        log("Sending ls command")
    _s.write(b'Fl')

    if verbose:
        log("Sending path")
    
    idx = 0
    while True:
        i = path[idx].encode(encoding="ascii")
        _s.write(i)
        _s.flush()
        time.sleep(0.01)
        r = _s.read().decode()
        if r == "":
            if verbose:
                log(f"[WARNING] Byte {idx} timed out. Retrying.", pre="\033[2K")
                continue

        idx += 1
        if idx == len(path):
            break
    
    _s.write(b"\x00")

    _s.timeout = 1
    c = _s.read()
    while c != b"255":
        data += c
    
    return data
    

def replaceAll(s: str, cmap: dict) -> str:
    for c in cmap:
        s = s.replace(c, cmap[c])

    return s

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("PORT", help="The COM port to use")
    parser.add_argument("REMOTE_FILE")
    parser.add_argument("-v", "--verbose", help="Print extra info", action="store_true")
    parser.add_argument("-W", "--wrap", help="Wrap text lines to 32 characters long", action="store_true")
    parser.add_argument("-m", "--map", help="Use a replacement map for non ascii characters (json file)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-w", "--write", help="Upload the specified file")
    group.add_argument("-r", "--delete", action="store_true")
    group.add_argument("-d", "--mkdir", action="store_true")

    args = parser.parse_args()

    serial_conn = serial.Serial(args.PORT, baudrate=115200)
    
    cmap = {}

    if args.write:
        if args.map:
            with open(args.map, encoding="utf-8") as f:
                cmap = getMap(f.read())
        
        if args.verbose:
            print(f"> Write remote={args.REMOTE_FILE} <- local={args.write}")
            print("Character map:")
            print(json.dumps(cmap, indent=2, sort_keys=True))
        
        if args.write[0:4].lower() == "str:":
            text = str(eval(args.write[4:]))
        else:
            with open(args.write, "r", encoding="utf-8") as f:
                text = replaceAll(f.read(), cmap)
            
        if args.wrap:
            text = wrapText(text)
        else:
            text = text.encode(encoding="ascii")

        success = send_file(serial_conn, args.REMOTE_FILE, text, verbose=args.verbose)
        if success:
            if args.verbose:
                log("---- FAIL ----")
            exit(1)
            # print(serial_conn.read_all())
        else:
            if args.verbose:
                log("---- SUCCESS ----")
            exit(0)
    elif args.delete:
        if args.verbose:
            print("> Delete", args.REMOTE_FILE)
        
        resp = send_delete(serial_conn, args.REMOTE_FILE, args.verbose)
        if resp:
            if resp == FS_DIR_NOT_EMPTY:
                print(f"Error: directory '{args.REMOTE_FILE}' is not empty.")
            elif resp == FS_FAILED_TO_OPEN_FILE:
                print("Error: Failed to detele file. Does it exist?")
            if args.verbose:
                log("---- FAIL ----")
            exit(1)
        else:
            if args.verbose:
                log("---- SUCCESS ----")
            exit(0)
    elif args.mkdir:
        print("> Mkdir", args.REMOTE_FILE)
        resp = send_mkdir(serial_conn, args.REMOTE_FILE, args.verbose)
        if resp:
            if resp == FS_FAILED_TO_OPEN_FILE:
                print("Error: failed to create directory. Is it a valid path?")
            if args.verbose:
                log("Failed with code", resp)
                log("---- FAIL ----")
            exit(1)
        else:
            if args.verbose:
                log("---- SUCCESS ----")
            exit(0)



