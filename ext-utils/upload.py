import serial, time, textwrap, datetime, json

# def textWrap(s: str) -> bytes:
#     out = b''

#     lines = s.split('\n')

#     for line in lines:
#         if (len(line) < 29):
#             out += line.encode(encoding='ascii') + b'\n'
#         else:
#             for part in [line[i:i+28] for i in range(0, len(line), 28)]:
#                 out += part.encode(encoding='ascii') + b'\n'
#     return out 

def log(*s):
    now = datetime.datetime.now()
    t = "["+now.strftime("%H:%M:%S")+f".{now.microsecond//1000:03d}]"
    print(t, *s)

def wrapText(s):
    lines = s.split('\n')
    out = b''
    for line in lines:
        sub = textwrap.wrap(line, width=28)
        for l in sub:
            out += l.encode(encoding="ascii") + b'\n'

    return out

def send_data(_s: serial.Serial, data: bytes, print_return = False, verbose=False):
    _s.timeout = 0.1
    if verbose:
        n = 0
        nextt = time.time()
        log("Starting upload...")

    _s.write(b'T')

    l = len(data)
    lb = l.to_bytes(4, "big")

    if verbose:
        log("Data size:", l, "bytes")
    
    _s.write(lb)
    _s.flush()
    
    _s.reset_input_buffer()
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
                log(f"[WARNING] Byte {idx} timed out. Retrying.")
            continue
        if print_return:
            print(_s.read().decode(), end="", flush=True)
            
        
        if verbose:
            now = time.time()
            if now > nextt:
                log(f"Uploading... ({round((n/l) * 100)}%) ({n}/{l} bytes)")
                nextt = now + 0.150
            n += 1
        idx += 1
        if idx == l:
            break
    if verbose:
        log(f"Uploading... (100.00%) ({n}/{l} bytes)")

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

def replaceAll(s: str, cmap: dict) -> str:
    for c in cmap:
        s = s.replace(c, cmap[c])

    return s

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("COM", help="Serial port")
    parser.add_argument("FILE", help="Ascii text file")

    parser.add_argument("-r", "--replace", help="Map of invalid characters to ascii")
    parser.add_argument("-v", "--verbose", help="Print additional information", action="store_true")
    parser.add_argument("-E", "--echo", help="Do not echo returned bytes", dest="echo", action="store_true")
    parser.add_argument("-D", "--debug", help="Only print to console, no upload", action="store_true")
    

    args = parser.parse_args()

    port = args.COM
    file = args.FILE
    if not args.debug:
        s = serial.Serial(port, 9600, write_timeout=1)

    if args.replace:
        with open(args.replace, "r", encoding="utf-8") as m:
            mapdata = m.read()
        charMap = getMap(mapdata)
    else:
        charMap = {}

    if args.verbose:
        print("Character replacement map:")
        print(json.dumps(charMap, indent=2))

    with open(file, "r", encoding="utf-8") as f:
        encoded_text = wrapText(replaceAll(f.read(), charMap))
        if not args.debug:
            send_data(s, encoded_text, print_return=bool(args.echo), verbose=args.verbose)
            s.read(1)
            print("Upload completed. Disconnecting...")
            print("The ESP might reboot depending on your setup.")
            time.sleep(1)
            s.close()
        else:
            print(encoded_text.decode())
            print("Wrapped text to", len(encoded_text.split(b'\n')), "lines.")

    