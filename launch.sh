SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "${SCRIPT_DIR}/.venv/bin/activate"
python_exec="${SCRIPT_DIR}/.venv/bin/$1"
"${python_exec}" "${SCRIPT_DIR}/ipc_entry.py"
source deactivate