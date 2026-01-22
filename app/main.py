import sys, shutil, subprocess, os,shlex, readline
from pathlib import Path

COMMANDS_BUILTIN = {
    "exit": lambda code=0, *args: sys.exit(int(code)),
    "echo": lambda *x: print(" ".join(x)),  
    "pwd": lambda : print(Path.cwd()),
    "cd": lambda path: change_directory(path)
}

def completer(text, state):
    options = []
    
    # First, add built-in commands that match
    options.extend([cmd + ' ' for cmd in COMMANDS_BUILTIN if cmd.startswith(text)])
    
    # Then, add executable commands from PATH
    path_dirs = os.environ.get('PATH', '').split(os.pathsep)
    for path_dir in path_dirs:
        try:
            dir_path = Path(path_dir)
            if dir_path.exists() and dir_path.is_dir():
                for file in dir_path.iterdir():
                    if file.is_file() and os.access(file, os.X_OK):
                        if file.name.startswith(text) and file.name not in options:
                            options.append(file.name + ' ')
        except (PermissionError, OSError):
            continue
    
    # Remove duplicates and sort
    options = sorted(set(options))
    
    if state < len(options):
        return options[state]
    return None

readline.parse_and_bind("tab: complete")
readline.set_completer(completer)

def main():
    # TODO: Uncomment the code below to pass the first stage
    while True:
        try:
            user_input = shlex.split(input("$ "))  # Changed this line
        except EOFError:
            break
        
        if not user_input:
            continue
            
        command = user_input[0]
        args = user_input[1:]
        
        commands(command, *args) 

def find_executable_path(command_name): 
    executable_path_str = shutil.which(command_name)
    
    if executable_path_str:
        return Path(executable_path_str)
    else:
        return None
    
def change_directory(path):
    if path == "~":
        os.chdir(Path.home())
        return
    
    pth = Path(path)
    
    if not pth.is_absolute():
        pth = (Path.cwd() / pth).resolve()

    if pth.exists() and pth.is_dir():
        os.chdir(pth)
    else:
        print(f"cd: {path}: No such file or directory")
    
def commands(command, *args):
    if ">" in args or "1>" in args or "2>" in args or ">>" in args or "1>>" in args or "2>>" in args:
        redirect_op = None
        i = None
        
        # Find which redirection operator is used
        if ">>" in args or "1>>" in args:
            redirect_op = ">>" if ">>" in args else "1>>"
            i = args.index(redirect_op) 
            mode = 'a'
        elif "2>" in args or "2>>" in args:
            redirect_op = "2>" if "2>" in args else "2>>"
            i = args.index(redirect_op)
            mode = 'w' if "2>" in args else 'a'
        elif ">" in args or "1>" in args:
            redirect_op = ">" if ">" in args else "1>"
            i = args.index(redirect_op)
            mode = 'w'

        arg = args[0:i]
        file = args[i + 1]

        result = subprocess.run(
            [command] + list(arg),
            capture_output=True,
            text=True
        )
        
        if redirect_op in (">", "1>", ">>", "1>>"):
            with open(file, mode) as f:
                f.write(result.stdout)
            if result.stderr:
                print(result.stderr, end="")
        elif redirect_op in ("2>", "2>>"):
            with open(file, mode) as f:
                f.write(result.stderr)
            if result.stdout:
                print(result.stdout, end="")
        return
    
    if command in COMMANDS_BUILTIN:
        COMMANDS_BUILTIN[command](*args)
        return True
    
    elif command == "type":
        # target = ''.join(args)
        target = args[0]
        if target in COMMANDS_BUILTIN or target == "type":
            print(f"{target} is a shell builtin")
            
        elif (path := find_executable_path(target)):
            print(f"{target} is {path}")
        
        else:
            print(f"{target}: not found")
    elif (find_executable_path(command)):
        result = subprocess.run(
            [command] + list(args),
            capture_output=True,
            text=True
        )
        print(result.stdout.strip())
    else:
        print(f"{command}: command not found")
    
if __name__ == "__main__":
    main()
