import protocol
import argparse
import serial
import os

VERSION = "0.1.1"

parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", action="store_true")
parser.add_argument("COM_PORT")
sys_args = parser.parse_args()

_serial = serial.Serial(sys_args.COM_PORT)

print("FSCLI v"+VERSION)
print("Available commands: help, upload, rm, ls(=dir), cd, mkdir, exit")
print("Use 'help' for more information.")

if sys_args.verbose:
    print()
    print("** Verbose mode **")
    print()

path = "/"

def Dlog(*s):
    print(*s)

def Derror(*s):
    print("\033[1;31mError: "+' '.join([str(_) for _ in s])+"\033[0m")

def printHelp():
    print("help                       Show this message")
    print("exit                       Exit the program")
    print("clear                      Clear the console")
    print("version                    Prints the shell version")
    print("upload [SOURCE] [TARGET]   Upload SOURCE to TARGET (SOURCE = str('some text here') to directly upload text.)")
    print("ls [TARGET]                List TARGET directory's contents")
    print("rm (-r) [TARGET]           Delete TARGET (-r for recursive deletion)")
    print("cd [TARGET]                Change directory to TARGET (Local only)")
    print("mkdir (-p) [TARGET]        Creates a directory at TARGET (-p to create parent directories instead of failing)")


def parse_dir_up(abspath):
    parsed_target = ""
    for part in abspath.strip("/").split("/"):
        if part == ".":
            pass
        elif part == "..":
            parsed_target = "/".join(parsed_target.split("/")[:-1])
        else:
            parsed_target += "/" + part
    
    return parsed_target if parsed_target and parsed_target[0] == "/" else "/"+parsed_target


while True:
    try:
        cmd = input(f"{path} # ")
        if not cmd.strip(): continue
        parts = cmd.split()
        command = parts[0].lower()
        args = parts[1:]

        if   command == "exit":
            Dlog("exit")
            break
        elif command == "help":
            printHelp()
        elif command == "clear":
            if os.name in ("nt", "dos"):
                os.system("cls")
            else:
                os.system("clear")
        elif command == "version":
            Dlog("CLI version",VERSION)
        elif command == "upload":
            if len(args) < 2:
                Derror("Invalid command syntax. Use 'help' for correct usage")

            if args[0][0:3].lower() == "str":
                try:
                    text = str(eval(args[0][4:-1]))
                except Exception as e:
                    Derror(f"Failed to parse the input string. \n  -> {e}")
                    continue
            else:
                try:
                    with open(args[0], "r", encoding="utf-8") as f:
                        text = f.read()
                except Exception as e:
                    Derror(f"Failed to read the input file. \n  -> {e}")
                    continue
            
            try:
                text = text.encode(encoding="ascii")
            except UnicodeEncodeError:
                Derror("The text must be ASCII only.")
                continue
            
            if any(len(s) > 32 for s in text.split(b"\n")):
                Derror("Lines can not be longer then 32 characters.")
            
            target = args[1]

            if target[0] != "/":
                target = path + "/" + target
            
            target = parse_dir_up(target)
            
            status = protocol.send_file(_serial, target, text, verbose=sys_args.verbose)
            if status:
                if sys_args.verbose:
                    protocol.log("---- FAIL ----")
                Derror("Upload failed.")
            else:
                if sys_args.verbose:
                    protocol.log("---- SUCCESS ----")
        elif command == "rm":
            if len(args) < 1:
                Derror("Invalid syntax. Use 'help' for correct usage.")
                continue

            recursive = False
            target = args[0]
            
            
            if len(args) > 1:
                if args[0] == "-r": recursive = True
                target = args[1]
            else:
                if args[0] == "-r": 
                    Derror("Invalid command syntax.")
                    continue
            
            if target[0] != "/":
                target = path + "/" + target

            target = parse_dir_up(target)
            if path.startswith(target):
                Derror("Unable to delete current working directory")
                continue
            resp = protocol.send_delete(_serial, target, sys_args.verbose, recursive=recursive)
            if resp:
                if resp == protocol.FS_DIR_NOT_EMPTY:
                    Derror(f"Directory '{target}' is not empty.")
                elif resp == protocol.FS_FAILED_TO_OPEN_FILE:
                    Derror(" Failed to detele file. Does it exist?")
                
                if sys_args.verbose:
                    protocol.log("---- FAIL ----")
            else:
                if sys_args.verbose:
                    protocol.log("---- SUCCESS ----")
        elif command in ("ls", 'dir'):
            if len(args) < 1:
                target = path
            else:
                target = args[0]

            target = parse_dir_up(target)

            raw = protocol.send_list(_serial, target, sys_args.verbose)
            if raw == protocol.FS_FAILED_TO_OPEN_FILE:
                Derror("Failed to open directory. Does it exist?")
                continue
            
            isDir = [bool(i) for i in raw[0:32]]
            files = [""]
            i = 32
            while i < len(raw):
                while raw[i] != 0:
                    files[-1] += bytes([raw[i]]).decode()
                    i += 1
                files.append("")
                i += 1
            # Dlog(f"--- Directory listing of '{target}' ---")
            for i in range(0, len(files)-1):
                _item = files[i]
                _dir = isDir[i]
                if not _item: continue
                Dlog(f"{'\033[1;34m' if _dir else ''}{_item} \033[0m")
        elif command == "cd":
            if len(args) < 1:
                target = "/"
            else:
                target = args[0]
            if target == "~":
                target = "/"

            if target[0] != "/":
                target = path + ("/" if path != "/" else '') + target

            target = parse_dir_up(target)

            if (protocol.send_list(_serial, target) == protocol.FS_FAILED_TO_OPEN_FILE):
                Derror(f"{target}: Invalid directory")
                continue

            path = target
        elif command == "mkdir":
            if len(args) < 1:
                Derror("Invalid command syntax. Use 'help' for correct usage")
            
            parents = False
            target = args[0]
            if len(args) > 1:
                if args[0] == "-p":
                    parents = True
                    target = args[1]
            else:
                if args[0] == "-p":
                    Derror("Invalid command syntax. Use 'help' for correct usage")
                    continue
            
            if target[0] != "/":
                target = path + ("/" if path != "/" else '') + target
            
            target = parse_dir_up(target)

            resp = protocol.send_mkdir(_serial, target, sys_args.verbose, parents)
            if resp:
                if resp == protocol.FS_FAILED_TO_OPEN_FILE:
                    Derror("Failed to create directory. Is it a valid path?")
                    if sys_args.verbose:
                        protocol.log("Failed with code", resp)
                        protocol.log("---- FAIL ----")
                else:
                    if sys_args.verbose:
                        protocol.log("---- SUCCESS ----")
        else:
            Derror("Command not found.")
    except KeyboardInterrupt:
        Dlog("^C")
    
        
