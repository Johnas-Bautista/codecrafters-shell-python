import sys, shutil, subprocess, os,shlex, readline, io
from pathlib import Path
from contextlib import redirect_stdout

COMMANDS_BUILTIN = {
    "exit": lambda code=0, *args: sys.exit(int(code)), 
    "echo": lambda *x: print(" ".join(x)),  
    "pwd": lambda : print(Path.cwd()),
    "cd": lambda path: change_directory(path)
}


def handle_pipeline(user_input):
    """Handle piped commands using subprocess.Popen"""
    # Split commands by pipe
    commands_list = []
    current_cmd = []
    
    for token in user_input:
        if token == "|":
            if current_cmd:
                commands_list.append(current_cmd)
                current_cmd = []
        else:
            current_cmd.append(token)
    
    if current_cmd:
        commands_list.append(current_cmd)
    
    # Create processes
    processes = []
    
    for i, cmd_parts in enumerate(commands_list):
        cmd = cmd_parts[0]
        args = cmd_parts[1:] if len(cmd_parts) > 1 else []
        
        # Set stdin
        if i == 0:
            stdin = None
        else:
            stdin = processes[-1].stdout
        
        # Set stdout  
        stdout = subprocess.PIPE
        
        # Start the process
        try:
            proc = subprocess.Popen(
                [cmd] + args,
                stdin=stdin,
                stdout=stdout,
                stderr=subprocess.PIPE,
                text=True
            )
            processes.append(proc)
            
            # IMPORTANT: Close the stdout in parent after passing to next process
            # This allows the previous process to receive SIGPIPE when next process exits
            if i > 0:
                processes[i - 1].stdout.close()
                
        except FileNotFoundError:
            print(f"{cmd}: command not found")
            # Clean up any started processes
            for p in processes:
                p.terminate()
            return
    
    # Get output from last process
    if processes:
        try:
            last_proc = processes[-1]
            try:
                # Read output line-by-line (important for tail -f)
                for line in last_proc.stdout:
                    print(line, end='')

                last_proc.wait()

            finally:
                # Terminate remaining processes
                for proc in processes[:-1]:
                    proc.terminate()
                    try:
                        proc.wait(timeout=0.1)
                    except subprocess.TimeoutExpired:
                        proc.kill()

        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            for proc in processes:
                proc.terminate()
            raise
        except BrokenPipeError:
            # Handle broken pipe
            for proc in processes:
                proc.terminate()
                
                
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

def completer(text, state):
    options = []
    
    # First, add built-in commands that match
    options.extend([cmd for cmd in COMMANDS_BUILTIN if cmd.startswith(text)])
    
    # Then, add executable commands from PATH
    path_dirs = os.environ.get('PATH', '').split(os.pathsep)
    for path_dir in path_dirs:
        try:
            dir_path = Path(path_dir)
            if dir_path.exists() and dir_path.is_dir():
                for file in dir_path.iterdir():
                    if file.is_file() and os.access(file, os.X_OK):
                        if file.name.startswith(text) and file.name not in options:
                            options.append(file.name)
        except (PermissionError, OSError):
            continue
    
    options = sorted(set(options))
    
    if state < len(options):
        # If there's only one option, add a space after it
        if len(options) == 1:
            return options[state] + ' '
        return options[state]
    return None

def display_matches(substitution, matches, longest_match_length):
    """Custom display function to show completions horizontally with 2 spaces"""
    print()
    print('  '.join(matches))  # Join with exactly 2 spaces
    print(f"$ {readline.get_line_buffer()}", end='', flush=True)

readline.parse_and_bind("tab: complete")
readline.set_completer(completer)
readline.set_completion_display_matches_hook(display_matches)

def main():
    while True:
        try:
            user_input = shlex.split(input("$ "))
        except EOFError:
            break
        
        if not user_input:
            continue
        
        # Check for pipe
        if "|" in user_input:
            handle_pipeline(user_input)
        else:
            command = user_input[0]
            args = user_input[1:]
            commands(command, *args)


    
if __name__ == "__main__":
    main()
