import sys


def main():
    # TODO: Uncomment the code below to pass the first stage
    while True:
        sys.stdout.write("$ ")
        user_input = input().split()
        
        if not user_input:
            continue
            
        command = user_input[0]
        args = user_input[1:]
        
        result = commands(command, *args)
        if result is False: 
            print(f"{command}: command not found")



def commands(command, *args):
    COMMANDS = {
        "exit": lambda code=0, *args: sys.exit(int(code)),
        "echo": lambda *x: print(" ".join(x)),
    }
    
    if command in COMMANDS:
        COMMANDS[command](*args)
        return True
    else:
        return False
        
    
    
if __name__ == "__main__":
    main()
