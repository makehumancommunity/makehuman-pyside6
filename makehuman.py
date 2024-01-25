#!/usr/bin/env python3 # -*- coding: utf-8 -*-

import argparse, textwrap
import os
import sys
from time import sleep

from PySide6.QtWidgets import QApplication

from core.globenv import programInfo, globalObjects
from gui.mainwindow import  MHMainWindow
from gui.application import  MHApplication
from core.baseobj import baseClass

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
    parser.add_argument("-l", action="store_true", help="force to write to log file")
    parser.add_argument("-A", '--admin', action="store_true", help="Support administrative tasks ('Admin'). Command will write into program folder, where makehuman is installed.")
    parser.add_argument("-v", "--verbose",  type=int, default = 1, help= textwrap.dedent('''\
            bitwise verbose option (add values)
            1 low log level (standard)
            2 mid log level
            4 memory management
            8 file access
            16 enable numpy runtime error messages'''))

    args = parser.parse_args()

    frozen = getattr(sys, 'frozen', False) # frozen means, no source download
    if frozen:
        syspath = os.path.dirname(sys.executable)
    else:
        syspath = os.path.dirname(os.path.realpath(__file__))

    # get programInfo as environment (only for strings to be printed in JSON)
    # and globalObjects for non-printable objects

    env = programInfo(frozen, syspath, args.verbose, args.l, args.admin)
    if not env.environment():
        print (env.last_error)
        exit (20)

    glob = globalObjects(env)
    if not glob.readShaderInitJSON():
        print (env.last_error)
        exit (21)

    if args.verbose & 2:
        print (env)

    theme = env.existDataFile("themes", env.config["theme"])

    app = MHApplication(glob, sys.argv)
    glob.setApplication(app)

    if app.setStyles(theme) is False:
        env.logLine(1, env.last_error)

    if env.basename is not None:
        dirname  = env.existDataDir("base", env.basename)
        base = baseClass(glob, env.basename, dirname)
        base.prepareClass()

    mainwin = MHMainWindow(glob)
    mainwin.show()
    #
    # all we need from openGL is now existent (get initial values)
    #
    mainwin.initParams()
    app.exec()
    

if __name__ == '__main__':
    main()
