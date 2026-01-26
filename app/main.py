import sys, shutil, subprocess, os,shlex, readline, io
from pathlib import Path
from contextlib import redirect_stdout

COMMANDS_BUILTIN = {
    "exit": lambda code=0, *args: sys.exit(int(code)), 
    "echo": lambda *x: print(" ".join(x)),  
    "pwd": lambda : print(Path.cwd()),
    "cd": lambda path: change_directory(path),
    "history": lambda : print()
}


def builtin_echo(args, stdin, stdout):
    print(" ".join(args), file=stdout)

def builtin_pwd(args, stdin, stdout):
    print(Path.cwd(), file=stdout)

def builtin_type(args, stdin, stdout):
    target = args[0]
    if target in COMMANDS_BUILTIN or target == "type":
        print(f"{target} is a shell builtin", file=stdout)
    elif (path := find_executable_path(target)):
        print(f"{target} is {path}", file=stdout)
    else:
        print(f"{target}: not found", file=stdout)


def handle_pipeline(user_input):
    final_builtin_output = None
    commands_list = []
    current = []

    for token in user_input:
        if token == "|":
            commands_list.append(current)
            current = []
        else:
            current.append(token)

    if current:
        commands_list.append(current)

    input_data = None
    processes = []
    prev_proc = None

    for i, cmd_parts in enumerate(commands_list):
        cmd = cmd_parts[0]
        args = cmd_parts[1:]

        next_is_builtin = (
            i + 1 < len(commands_list) and
            commands_list[i + 1][0] in PIPELINE_BUILTINS
        )

        # ---------- BUILTIN ----------
        if cmd in PIPELINE_BUILTINS:
            stdin = io.StringIO(input_data) if input_data else io.StringIO()
            stdout = io.StringIO()

            PIPELINE_BUILTINS[cmd](args, stdin, stdout)
            output = stdout.getvalue()

            if i == len(commands_list) - 1:
                final_builtin_output = output
            else:
                input_data = output
            
            prev_proc = None

        # ---------- FORBIDDEN BUILTIN ----------
        elif cmd in ("cd", "exit"):
            print(f"{cmd}: not allowed in pipeline")
            return

        # ---------- EXTERNAL ----------
        else:
            try:
                # Determine stdin source
                if input_data:
                    stdin_source = subprocess.PIPE
                elif prev_proc is not None:
                    stdin_source = prev_proc.stdout
                else:
                    stdin_source = None
                
                proc = subprocess.Popen(
                    [cmd] + args,
                    stdin=stdin_source,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                processes.append(proc)
                
                # Close the previous stdout in parent to allow proper piping
                if prev_proc is not None and prev_proc.stdout:
                    prev_proc.stdout.close()

                if input_data:
                    proc.stdin.write(input_data)
                    proc.stdin.close()
                    input_data = None

                if i == len(commands_list) - 1:
                    for line in proc.stdout:
                        print(line, end="")
                elif next_is_builtin:
                    input_data = proc.stdout.read()
                
                prev_proc = proc

            except FileNotFoundError:
                print(f"{cmd}: command not found")
                return

    if final_builtin_output is not None:
        print(final_builtin_output, end="")

    for p in processes:
        p.wait()

                
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
    print()
    print('  '.join(matches))  # Join with exactly 2 spaces
    print(f"$ {readline.get_line_buffer()}", end='', flush=True)

readline.parse_and_bind("tab: complete")
readline.set_completer(completer)
readline.set_completion_display_matches_hook(display_matches)

PIPELINE_BUILTINS = {
    "echo": builtin_echo,
    "pwd": builtin_pwd,
    "type": builtin_type,
}

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
