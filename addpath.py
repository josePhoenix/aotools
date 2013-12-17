import sys
import os.path
import iraf
_aotools_path = os.path.dirname(os.path.dirname(iraf.osfn('aotools$')))

if _aotools_path not in sys.path:
    # Add the directory to path.
    sys.path.insert(1, _aotools_path)
