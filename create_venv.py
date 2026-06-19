import json
import os
import subprocess
from pathlib import Path


def create_vscode_style_env(project_path: str, python_exe: str):
    # 1. Define paths relative to the current working directory
    project_root = Path(project_path)
    venv_dir = project_root / ".venv"
    vscode_dir = project_root / ".vscode"
    settings_file = vscode_dir / "settings.json"

    print(f"Creating virtual environment in: {str(venv_dir)}")

    # 2. Generate the standard venv using the active Python interpreter
    # This matches VS Code's baseline environment creation
    try:
        results = subprocess.run(
            [python_exe, "-m", "venv", "--system-site-packages",
             str(venv_dir)], check=True, capture_output=True, text=True)
        print(results.stdout)
        if (results.stderr):
            print(results.stderr)
            return
        print("Successfully created virtual environment.")
    except subprocess.SubprocessError as e:
        print(f"Error creating virtual environment: {e}")
        return

    if os.name == "nt":
        results = subprocess.run(
            [".venv\\Scripts\\activate.bat"],
            check=True, capture_output=True, text=True)
        print(results.stdout)
        if (results.stderr):
            print(results.stderr)
            return
        print("Virtual environment activated.")

    print("Updating pip...")
    if os.name == "nt":
        venv_python_exe = os.path.join(
            project_path, ".venv", "Scripts", "pythonw")
    else:
        venv_python_exe = os.path.join(
            project_path, ".venv", "bin", "python3")

    results = subprocess.run(
        [venv_python_exe, "-m", "pip", "install", "--upgrade", "pip"],
        check=True, capture_output=True, text=True)
    print(results.stdout)
    if 'Successfully installed' not in str(results.stdout):
        if (results.stderr):
            print(results.stderr)
            return

    # 3. Determine the correct interpreter path based on the OS
    # Windows uses 'Scripts', while macOS/Linux use 'bin'
    if os.name == "nt":
        interpreter_path = os.path.join(
            "${workspaceFolder}", ".venv", "Scripts", "python.exe")
    else:
        interpreter_path = os.path.join(
            "${workspaceFolder}", ".venv", "bin", "python3")

    # 4. Create or update .vscode/settings.json to force VS Code
    # integration.
    vscode_dir.mkdir(exist_ok=True)

    # Load existing settings if they exist to prevent overwriting
    # user preferences.
    settings_data = {}
    if settings_file.exists():
        try:
            with open(settings_file, "r") as f:
                settings_data = json.load(f)
        except json.JSONDecodeError:
            print("Warning: Existing settings.json is invalid."
                  " Creating a new one.")

    # Apply the exact key VS Code uses to target the environment
    settings_data["python.defaultInterpreterPath"] = interpreter_path

    # Save the updated configuration
    with open(settings_file, "w") as f:
        json.dump(settings_data, f, indent=4)

    print(f"Updated {str(settings_file)} with default interpreter path.")

    requirements_path = os.path.join(project_path, 'requirements.txt')
    if os.path.exists(requirements_path):
        print(f"Installing packages from {requirements_path}...")
        # Determine the correct pip executable path based on OS
        if os.name == 'nt':  # Windows
            pip_executable = os.path.join(venv_dir, 'Scripts', 'pip.exe')
        else:  # macOS/Linux/Posix
            pip_executable = os.path.join(venv_dir, 'bin', 'pip')

        results = subprocess.run(
            [pip_executable, 'install', '-r', requirements_path],
            capture_output=True, text=True, check=True)
        print(results.stdout)
        if (results.stderr):
            print(results.stderr)
            return

        print("Packages installed successfully.")

    print("Environment setup complete. Restart your"
          " VS Code terminal to auto-activate.")


def get_kicad_python_version():
    # Define the default installation path based on the operating system
    if os.name == "nt":
        # Windows default pathway
        kicad_py_path = r"C:\Program Files\KiCad\10.0\bin\pythonw.exe"
    else:
        # Linux typically links KiCad to system python packages
        kicad_py_path = "/bin/python3"

    print(f'kicad_py_path: {kicad_py_path}')
    try:
        # Programmatically invoke the executable with the version flag
        result = subprocess.run(
            [kicad_py_path, "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        # Combine outputs as some older installations output to stderr
        output = result.stdout or result.stderr
        a = output.strip().split(' ')
        return a[len(a)-1]
    except FileNotFoundError:
        return f"KiCad Python executable not found at specified path:" \
               f"{kicad_py_path}"
    except Exception as e:
        return f"An error occurred: {str(e)}"


def get_python_executables() -> list:
    exes = []
    if os.name == "nt":
        result = subprocess.run(["py", "-0p"],
                                capture_output=True, text=True)
    else:
        result = subprocess.run(['which', '-a', 'python3'],
                                capture_output=True, text=True)
    output = str(result.stdout)
    for rec in output.split('\n'):
        if len(rec):
            if os.name == 'nt':
                p = rec.find("\\Users\\")
                if p:
                    p = p - 2
                    exes.append(rec[p:])
            else:
                exes.append(rec)
    if os.name == 'nt':
        exes.append(r"C:\Program Files\KiCad\10.0\bin\pythonw.exe")
    return exes


def get_python_exe_version(python_exe: str) -> str:
    version: str = ''
    result = subprocess.run([python_exe, '--version'],
                            capture_output=True, text=True, check=True)
    output = str(result.stdout or result.stderr)
    for rec in output.strip().split('\n'):
        if len(rec):
            a = rec.split(' ')
            version = a[len(a)-1]
            break
    return version


if __name__ == "__main__":
    kicad_python_version = get_kicad_python_version()
    print(f"Detected Kicad Python version: {kicad_python_version}")
    python_executables = get_python_executables()
    matching_exe = ''
    for python_exe in python_executables:
        if '.venv' in python_exe:
            continue
        print(f"Checking python version using {python_exe}")
        version = get_python_exe_version(python_exe)
        if version.startswith(kicad_python_version):
            matching_exe = python_exe
            break
    if len(matching_exe):
        saved_cwd = os.getcwd()
        # matching_exe = '/bin/python3'
        print(f'Using Python executable: {matching_exe}')
        create_vscode_style_env(os.getcwd(), matching_exe)
        os.chdir(saved_cwd)
    else:
        print("Could not identify Kicad Python version.  Venv not created.")
