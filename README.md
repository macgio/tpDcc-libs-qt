# tpQtLib

Collection of Python modules to make your life easier when working with PySide/PyQt.

Also, when working with specific DCCs, tpQtLib will auto import proper modules and will use
DCC specific implementations for PySide/PyQt widgets.

## Installation
### Manual
1. Clone/Download tpQtLib anywhere in your PC (If you download the repo, you will need to extract
the contents of the .zip file).
2. Copy **tpQtLib** folder located inside **source** folder in a path added to **sys.path**

### Automatic
Automatic installation for tpQtLib is not finished yet.

# DCC Implementations
At this moment following DCCs are supported:

* **3ds Max**: https://github.com/tpoveda/tpMaxLib
* **Maya**: https://github.com/tpoveda/tpMayaLib
* **Houdini**: https://github.com/tpoveda/tpHoudiniLib
* **Nuke**: https://github.com/tpoveda/tpNukeLib
* **Blender**: *Work in Progress*

During tpQtLib initialization, if DCC specific implementation package is found in sys.path, tpQtLib
will automatically detect it and will import it.

## Usage

### Initialization Code
tpQtLib must be initialized before being used.
```python
import tpQtLib
tpQtLib.init()
```

### Reloading
For development purposes, you can enable reloading system, so 
you can reload tpQtLib sources without the necessity of restarting
your Python session. Useful when working with DCCs.
```python
import tpQtLib
reload(tpQtLib)
tpQtLib.init(True)
```

### Enabling debug log
By default, tpQtLib logger only logs warning messages. To enable all log messages
you can set TPQTLIB_DEV environment variables to 'True'
```python
import os

os.environ['TPQTLIB_DEV'] = 'True'
import tpQtLib
tpQtLib.init()
```
