import serial, time, datetime, json, textwrap
from protocol import *

def wrapText(s: str) -> bytes:
    lines = s.split('\n')
    out = b''
    for line in lines:
        sub = textwrap.wrap(line, width=32)
        for l in sub:
            out += l.encode(encoding="ascii") + b'\n'

    return out

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

def printhelp():
    print("Usage:")
    print("  fstool.py [-vWm] help")
    print("or")
    print("  fstool.py [-vWm] PORT upload SOURCE TARGET")
    print("                        rm (-r) TARGET")
    print("                        ls TARGET")
    print("                        mkdir (-p) TARGET")
    

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true")
    # parser.add_argument("-r", "--recursive", action="store_true")
    parser.add_argument("-W", "--wrap", help="Wrap text lines to 32 characters long", action="store_true")
    parser.add_argument("-m", "--map", help="Use a replacement map for non ascii characters (json file)")
    parser.add_argument("PORT")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    if args.PORT.lower() == "help":
        printhelp()
        exit(0)

    serial_conn = serial.Serial(args.PORT, baudrate=115200)

    if len(args.command) < 1:
        print("Error: Invalid syntax")
        printhelp()
        exit(255)

    _command = args.command[0]
    _args = args.command[1:]

    if _command.lower() == "upload":
        if len(_args) < 2:
            print("Error: Invalid syntax. fstool.py PORT upload (-v) SOURCE TARGET")
            exit(255)
        cmap = {}
        if args.map:
            with open(args.map, encoding="utf-8") as f:
                cmap = getMap(f.read())
        
        if args.verbose:
            print(f"> Write remote={_args[1]} <- local={_args[0]}")
            print("Character map:")
            print(json.dumps(cmap, indent=2, sort_keys=True))
        
        if _args[0][0:3].lower() == "str":
            text = str(eval("'"+_args[0][4:-1]+"'"))
        else:
            with open(_args[0], "r", encoding="utf-8") as f:
                text = replaceAll(f.read(), cmap)
        
        if args.wrap:
            text = wrapText(text)
        else:
            text = text.encode(encoding="ascii")
        
        success = send_file(serial_conn, _args[1], text, verbose=args.verbose)
        if success:
            if args.verbose:
                log("---- FAIL ----")
            exit(1)
        else:
            if args.verbose:
                log("---- SUCCESS ----")
            exit(0)

    elif _command.lower() == "rm":
        if len(_args) < 1:
            print("Error: Invalid syntax. fstool.py PORT rm (-r) TARGET")
            exit(255)

        
        recursive = False
        if len(_args) > 1:
            if _args[0] == "-r": recursive = True
        else:
            if _args[0] == "-r": print("Error: Invalid syntax. fstool.py PORT rm (-r) TARGET")

        resp = send_delete(serial_conn, _args[0] if not recursive else _args[1], args.verbose, recursive=recursive)
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

    elif _command.lower() == "ls":
        if len(_args) < 1:
            print("Error: Invalid syntax. fstool.py PORT ls TARGET")
            exit(255)

            
        _target = _args[0]
        raw = send_list(serial_conn, _target, args.verbose)
        if raw == FS_FAILED_TO_OPEN_FILE:
            print("Error: Failed to open directory. Does it exist?")
            exit(1)
        isDir = [bool(i) for i in raw[0:32]]
        files = [""]
        
        i = 32
        while i < len(raw):
            while raw[i] != 0:
                files[-1] += bytes([raw[i]]).decode()
                i += 1
            files.append("")
            i += 1
        print(f"--- Directory listing of '{_target}' ---")
        # print(raw)
        for i in range(0, len(files)-1):
            _item = files[i]
            _dir = isDir[i]
            if not _item: continue
            print(f" * ({'D' if _dir else 'F'}) {_item}{'/' if _dir else ''}")
    elif _command.lower() == "mkdir":
        if len(_args) < 1:
            print("Error: Invalid syntax. fstool.py PORT mkdir (-p) TARGET")
            exit(255)

        
        parents = False
        if len(_args) > 1:
            if _args[0] == "-p":
                parents = True
            
        target = _args[0] if len(_args) < 2 else _args[1]
        resp = send_mkdir(serial_conn, target, args.verbose, parents)
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
        
