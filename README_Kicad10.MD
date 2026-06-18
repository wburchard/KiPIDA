# Kicad 10 Support

Support for Kicad 10 (tested with version 10.0.3) has been added for Linux (tested
on Ubuntu 26.04) and Windows 11.

## Installation

1. Ensure that the Kicad API is enabled (see the installation nodes for Kicad 9).
2. Locate your KiCad plugins directory:
   - **Windows:** `%APPDATA%\kicad\10.0\plugins`
   - **Linux:** `~/.local/share/kicad/10.0/plugins`
3. Copy the `KiPIDA` folder into the `plugins` directory.
4. Open a terminal and change into the `KiPIDA` folder.
5. Execute the appropriate `create_venv` bash or batch file.
   - **Windows:** `create_venv.bat`
   - **Linux:** `./create_venv.sh`
6. Copy the contents of `plugin_kicad10.json` into `plugin.json` (replacing
   its contents).
