import serial, time, os, datetime

FS_DOES_NOT_EXIST = 255
FS_FAILED_TO_OPEN_FILE = 254
FS_DIR_NOT_EMPTY = 253

def log(*s, pre="", **kw):
    now = datetime.datetime.now()
    t = "["+now.strftime("%H:%M:%S")+f".{now.microsecond//1000:03d}]"
    print(pre+t, *s, **kw)


def send_file(_s: serial.Serial, filename: str, data: bytes, print_return = False, verbose=False) -> int:
    _st = time.time()
    n = 0
    nextt = time.time()
    
    _s.timeout = 2
    if verbose:
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
        if verbose:
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

def send_mkdir(_s: serial.Serial, path: str, verbose=False, parents=False) -> int:
    _s.timeout = 2
    if verbose:
        n = 0
        nextt = time.time()
        log("Sending mkdir command")
    _s.write(b'F')

    if parents:
        _s.write(b'M')
    else:
        _s.write(b'm')

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

def send_delete(_s: serial.Serial, filename: str, verbose=False, recursive=False) -> int:
    _s.timeout = 2
    if verbose:
        n = 0
        nextt = time.time()
        log("Sending delete command")
    _s.write(b'F')
    if not recursive:
        _s.write(b"d")
    else:
        _s.write(b"D")

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
    while c != b"\xff":
        if c == b"\xfe":
            return FS_FAILED_TO_OPEN_FILE  # type: ignore
        data += c
        c = _s.read()
    
    return data
    