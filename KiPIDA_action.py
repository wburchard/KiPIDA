import os
import sys
import json
import logging
import tempfile
import pcbnew
import subprocess
from pathlib import Path

script_path = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(tempfile.gettempdir(), "KiPIDA_action.log")
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s [%(filename)s:%(lineno)d]:"
    " %(message)s",
    filename=log_file,
    filemode="a",
)

try:
    logging.info("Setting up virtual environment paths if any.")
    plugin_config = os.path.join(script_path, 'plugin.json')
    with open(plugin_config, 'r') as f:
        plugin_info = json.load(f)
    identifier = plugin_info['identifier']
    logging.info(f"Plugin identifier: {identifier}")
    if script_path not in sys.path:
        sys.path.insert(0, script_path)
    platform_id = sys.platform
    if platform_id.startswith('linux'):
        version = f"python{sys.version_info.major}.{sys.version_info.minor}"
        venv = os.environ.get("VIRTUAL_ENV")
        if venv is None:
            venv = ''
        logging.info(f"VIRTUAL_ENV: {venv}")
        if len(venv) == 0:
            kicad_cache_home = os.environ.get('KICAD_CACHE_HOME', '')
            if len(kicad_cache_home) == 0:
                logging.error(
                    "KICAD_CACHE_HOME environment variable is not set.")
                exit(1)

        venv_site_packages = os.path.join(
            venv, "lib", version, "site-packages")

        venv_site_packages = venv_site_packages.replace('//', '/')

        if venv_site_packages in sys.path:
            sys.path.remove(venv_site_packages)

        logging.info(f"Inserting '{venv_site_packages}' into sys.path")

        if sys.path[0] == '':
            sys.path[0] = venv_site_packages
        else:
            sys.path.insert(0, venv_site_packages)
    elif os.name == "nt":
        venv = os.environ.get("VIRTUAL_ENV")
        if venv is None:
            venv = ''
        venv = os.path.join(script_path, ".venv")
        if not Path(venv).is_dir():
            logging.error("Virtual environment not found!")
            exit(1)
        venv_site_packages = os.path.join(venv, "lib", "site-packages")
        if venv_site_packages in sys.path:
            sys.path.remove(venv_site_packages)

        logging.info(f"Inserting '{venv_site_packages}' into sys.path")

        if sys.path[0] == '':
            sys.path[0] = venv_site_packages
        else:
            sys.path.insert(0, venv_site_packages)

    logging.info(f"sys.path: {sys.path}")

except Exception as e:
    logging.exception(f"Import Module failed: {e}")


class KiPIDA_PluginAction(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "KiPIDA"
        self.category = "KiPIDA Plugin"
        self.description = "KiPIDA KiCad Power Integrity & Delivery Analyzer)."
        self.show_toolbar_button = True  # Optional, defaults to False
        self.icon_file_name = os.path.join(
            os.path.dirname(__file__), 'resources' 'kipida.png')

    def Run(self):
        logging.info("KiPIDA Plugin action started.")
        try:
            script_dir = str(Path(__file__).resolve().parent.resolve())
            env_dir = os.path.join(script_dir, '.venv')
            venv_cfg = PyVenvCfg(env_dir)
            exe_file = venv_cfg.get_exe_file()
            platform_id = sys.platform
            if platform_id.startswith('linux'):
                startup_script = os.path.join(
                    os.path.dirname(__file__), "launch.sh")
                startup_script = startup_script.replace('//', '/')
            elif os.name == "nt":
                startup_script = os.path.join(
                    os.path.dirname(__file__), "launch.bat")
                startup_script = startup_script.replace('\\\\', '\\')
                startup_script = startup_script.replace('/', '\\')
            else:
                logging.error(f'{platform_id} is not supported.')
                exit(1)
            try:
                if platform_id.startswith('linux'):
                    cmd_list = ['/bin/bash', startup_script, exe_file]
                    logging.info(
                        f'Launching plugin:: "{startup_script}" {exe_file}')
                else:
                    cmd_list = ['cmd.exe', '/k', startup_script, script_dir]
                    logging.info(
                        f'Launching plugin: "{startup_script}" "{script_dir}"')
                # Since this plugin uses the ipc api, we launch it as an
                # independent process to avoid blocking the main kicad thread
                # which will cause the api to timeout.
                with open(os.devnull, 'r+b') as DEVNULL:
                    if os.name == "nt":
                        process = subprocess.Popen(
                            cmd_list,
                            stdin=DEVNULL,   # Redirect std input from null
                            stdout=DEVNULL,  # Redirect std output to null
                            stderr=DEVNULL,  # Redirect std error to null
                            close_fds=True,  # Ensures files are closed
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                    else:
                        process = subprocess.Popen(
                            cmd_list,
                            stdin=DEVNULL,   # Redirect std input from null
                            stdout=DEVNULL,  # Redirect std output to null
                            stderr=DEVNULL,  # Redirect std error to null
                            close_fds=True   # Ensures files are closed
                        )
                    logging.info(f"Plugin launched with PID: {process.pid}")
            except subprocess.CalledProcessError as e:
                logging.error(f"Error running script: {e.stderr}")
            except FileNotFoundError:
                logging.error(f"Error: Script not found at {script_path}")
        except Exception as e:
            logging.exception(f"Failed to run KiPIDA Plugin: {e}")


class PyVenvCfg:
    def __init__(self, venv_path: str):
        venv_config = os.path.join(venv_path, "pyvenv.cfg")
        self._settings = dict()
        with open(venv_config, 'r', encoding="utf-8") as cfg:
            for rec in cfg:
                a = rec.split('=')
                self._settings[a[0].strip()] = a[1].strip()

    def get_home(self) -> str:
        return self._settings['home']

    def get_include_system_site_packages(self) -> bool:
        return bool(self._settings['include-system-site-packages'])

    def get_version(self) -> str:
        return self._settings['version']

    def get_executable(self) -> str:
        if 'executable' in self._settings:
            return self._settings['executable']
        else:
            return ''

    def get_exe_file(self) -> str:
        if 'executable' in self._settings:
            exe_path = self._settings['executable']
            if '/' in exe_path:
                a = exe_path.split('/')
            else:
                a = exe_path.split('\\')
            return a[len(a) - 1]
        else:
            return ''

    def get_command(self) -> str:
        return self._settings['command']
