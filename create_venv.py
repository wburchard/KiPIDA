import json
import os
import subprocess
import sys
from pathlib import Path


def create_vscode_style_env(project_path: str, python_exe: str):
    # 1. Define paths relative to the current working directory
    project_root = Path(project_path)
    venv_dir = project_root / ".venv"
    vscode_dir = project_root / ".vscode"
    settings_file = vscode_dir / "settings.json"

    print(f"Creating virtual environment in: {venv_dir}")

    # 2. Generate the standard venv using the active Python interpreter
    # This matches VS Code's baseline environment creation
    try:
        subprocess.run(
            [python_exe, "-m", "venv", str(venv_dir)], check=True)
        print("Successfully created .venv folder.")
    except subprocess.SubprocessError as e:
        print(f"Error creating virtual environment: {e}")
        return

    venv_python_exe = os.path.join(project_path, ".venv", "bin", "python3")

    subprocess.run([venv_python_exe, "-m", "pip", "install", "--upgrade",
                    "pip"], check=True)

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

    print(f"Updated {settings_file} with default interpreter path.")

    requirements_path = os.path.join(project_path, 'requirements.txt')
    if os.path.exists(requirements_path):
        print(f"Installing packages from {requirements_path}...")
        # Determine the correct pip executable path based on OS
        if os.name == 'nt':  # Windows
            pip_executable = os.path.join(venv_dir, 'Scripts', 'pip.exe')
        else:  # macOS/Linux/Posix
            pip_executable = os.path.join(venv_dir, 'bin', 'pip')

        subprocess.check_call([pip_executable, 'install',
                              '-r', requirements_path])
        print("Packages installed successfully.")

    print("Environment setup complete. Restart your"
          " VS Code terminal to auto-activate.")


def get_kicad_python_version():
    # Define the default installation path based on the operating system
    if os.name == "nt":
        # Windows default pathway
        kicad_py_path = r"C:\Program Files\KiCad\bin\python.exe"
    elif sys.platform == "darwin":
        # macOS default bundle pathway
        kicad_py_path = \
            "/Applications/KiCad/KiCad.app/Contents/MacOS/kipython"
    else:
        # Linux typically links KiCad to system python packages
        kicad_py_path = "/bin/python3"

    try:
        # Programmatically invoke the executable with the version flag
        result = subprocess.run(
            [kicad_py_path, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
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
    result = subprocess.run(['which', '-a', 'python3'],
                            capture_output=True, text=True)
    output = str(result.stdout)
    for rec in output.split('\n'):
        if len(rec):
            exes.append(rec)
    return exes


def get_python_exe_version(python_exe: str) -> str:
    version: str = ''
    result = subprocess.run([python_exe, '--version'],
                            capture_output=True, text=True)
    output = str(result.stdout)
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
