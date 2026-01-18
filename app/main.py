import sys
# COMMANDS = {
#     "exit": {
#         "meaning": " is a command to exit the shell",
#         "comm": lambda code=0, *args: sys.exit(int(code))              
#     },
#     "echo": {
#         "meaning": " is a command for displaying strings", 
#         "comm": lambda *x: print(" ".join(x))
#     },
#     "type": {
#         "meaning": " is a command to describe a command",
#         "comm": lambda cmd, *x: 
#             print(cmd + COMMANDS[cmd]["meaning"]
#                     if cmd in COMMANDS else 
#                     f"{" ".join([cmd] + list(x))}: command not found")
#     },     
# }

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
        "type": lambda cmd, *x: 
                print(f"{cmd} is a shell builtin"
                      if cmd in COMMANDS else 
                      f"{" ".join([cmd] + list(x))}: not found"),     
    }
    
    if command in COMMANDS:
        COMMANDS[command](*args)
        return True
    else:
        return False
        
    
    
if __name__ == "__main__":
    main()
