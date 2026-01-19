import sys, shutil, subprocess
from pathlib import Path

def main():
    # TODO: Uncomment the code below to pass the first stage
    while True:
        sys.stdout.write("$ ")
        user_input = input().split()
        
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
    
def find_current_path(command_name):
    
    pass
    
def commands(command, *args):
    COMMANDS_BUILTIN = {
        "exit": lambda code=0, *args: sys.exit(int(code)),
        "echo": lambda *x: print(" ".join(x)),  
        "pwd": lambda : print(Path.cwd())
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
