import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from KiPIDA_action import KiPIDA_PluginAction

if __name__ == '__main__':
    plugin = KiPIDA_PluginAction()
    plugin.defaults()
    plugin.Run()
