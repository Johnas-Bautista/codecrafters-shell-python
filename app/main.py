import sys, shutil, subprocess, os,shlex
from pathlib import Path

def main():
    # TODO: Uncomment the code below to pass the first stage
    while True:
        sys.stdout.write("$ ")
        user_input = shlex.split(input())
        
        if not user_input:
            continue
            
        command = user_input[0]
        args = user_input[1:]
        if ">" in user_input or "1>" in user_input:
            if ">" in user_input:
                i = user_input.index(">")
            else:
                i = user_input.index("1>")

            command = user_input[0]
            args = user_input[1:i]
            outfile = user_input[i + 1]

            result = subprocess.run(
                [command] + args,
                capture_output=True,
                text=True
            )
            if result.stderr:
                print(result.stderr, end="")

            Path(outfile).write_text(result.stdout)
            continue
        commands(command, *args)  
        
# def create_pre_valued_files(*command):
#     if ">" in command or "1>" in command:
#         os.system(command_inp)

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
    COMMANDS_BUILTIN = {
        "exit": lambda code=0, *args: sys.exit(int(code)),
        "echo": lambda *x: print(" ".join(x)),  
        "pwd": lambda : print(Path.cwd()),
        "cd": lambda path: change_directory(path)
    }
    
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
