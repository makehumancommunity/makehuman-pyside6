#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse, textwrap
import os
import sys

from PySide6.QtWidgets import QApplication

from core.globenv import programInfo as G
from gui.mainwindow import  MHMainWindow
from gui.application import  MHApplication

def main():
    """
    main simply
    * parses arguments
    * calls environment
    * sets theme
    * starts application itself
    """
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    # optional arguments
    parser.add_argument('-V', '--version', action='store_true',  help="Show version and License")
    parser.add_argument("--noshaders", action="store_true", help="disable shaders")
    parser.add_argument("--multisampling", action="store_true", help="enable multisampling (used for anti-aliasing and alpha-to-coverage transparency rendering)")
    parser.add_argument("-v", "--verbose",  type=int, default = 1, help= textwrap.dedent('''\
            bitwise verbose option (add values)
            1 low log level (standard)
            2 mid log level
            4 enable numpy runtime error messages'''))

    args = parser.parse_args()

    frozen = getattr(sys, 'frozen', False) # frozen means, no source download
    if frozen:
        syspath = os.path.dirname(sys.executable)
    else:
        syspath = os.path.dirname(os.path.realpath(__file__))

    glob = G(frozen, syspath, args.verbose)
    if not glob.environment():
        print (glob.last_error)
        exit (20)

    if args.verbose & 2:
        print (glob)

    theme = glob.existDataFile("themes", glob.config["theme"])
    app = MHApplication(glob, sys.argv)
    if app.setStyles(theme) is False:
        glob.logLine(1, glob.last_error)
    mainwin = MHMainWindow(glob, app)
    mainwin.show()
    app.exec()
    

if __name__ == '__main__':
    main()
