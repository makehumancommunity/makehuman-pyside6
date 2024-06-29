# makehuman-pyside6
The program is still under development and is far from being ready for use. So be careful, we will not restore your box, if new makehuman does not do what it should do. Best to use a virtual environment still, especially on Linux with a python already installed.

MAC is not yet support and it could happen, that it will not be done (if we need to leave openGL in future, Vulkan will be used, not proprietary stuff like Metal).

The settings in requirements.txt are considered as minimal versions. Newer versions should(!) work.

* PyOpenGL (for the openGL part)
* PySide6 (for the gui)
* numpy (for faster calculation)
* psutil (for memory debugging, might not be in final version)

When installing these with e.g. pip install, other libraries like shiboken6 will be added.

This installation will change for sure, since it is all under development.

Atm. makehuman.py can only be started on CLI. You also need to 'cd' to the folder.
Call is with the interpreter in front:

	python3 makehuman.py

Currently syntax is like this:

	usage: makehuman.py [-h] [-V] [--multisampling] [-l] [-b BASE] [-A] [-v VERBOSE] [model]

	positional arguments:
  	model                 name of an mhm model file (use with base mesh

	optional arguments:
  	-h, --help            show this help message and exit
  	-V, --version         Show version and License
  	--multisampling       enable multisampling (used for anti-aliasing and alpha-to-coverage transparency rendering)
  	-l                    force to write to log file
  	-b BASE, --base BASE  preselect base mesh use 'none' for no preselection
  	-A, --admin           Support administrative tasks ('Admin'). Command will write into program folder, where makehuman is installed.
  	-v VERBOSE, --verbose VERBOSE
                        bitwise verbose option (add values)
                        1 low log level (standard)
                        2 mid log level
                        4 memory management
                        8 file access
                        16 enable numpy runtime error messages

Hint: multisampling is not yet implemented, there are still prints which do not follow the verbose rules for debugging.

Since makehuman comes with nearly no assets to save space on github, assets must be added.

Makehuman can work with two asset folders, one is called system folder, which is the place, where makehuman itself is installed and one is the user folder.

At the moment it is important that you first start makehuman to set your workspace (user folder) so that you can also download the assets in your
own environment, instead of mixing it with the program code, so that you do not download these assets again and again. This can be done in preferences.

So go to preferences, change MakeHuman user home to e.g. d:\shared\mhuser and logfile to d:\shared\mhuser\log (Windows syntax, Linux accordingly) and press save.

We do not recommend redirecting output in the development phase.


After setting the paths in preferences also the extra CLI tools are able to work with the user folder.
* compile_meshes.py
* compile_targets.py
* getpackages.py

These tools have options and can run without interaction (except getpackages.py) for later use in installation procedures,
but we recommend to start them without any options. In that case you have the chance to abort the command.

* Call **python3 getpackages.py** to get the assets for the hm08 base. (we recommend user space)
* Call **python3 compile_targets.py** to compile system targets first.
* Call **python3 compile_meshes.py** to compile meshes on both system + user folder (mhclo + obj will be compiled to mhbin). In system folder the base mesh itself is compiled.

You can also compile the meshes from  makehuman GUI, also the download can be done from there. Since system space is usually protected (esp. on Linux), a special option "-A" has to be used. Then you need to have the correct user permissions as well.

Be aware that in future times a packet might already contain the standard assets, so that this installation will be simpler.

Hint: The configuration file containing the path of the user folder can be changed also with an editor just in case. It will keep in place, even when you delete the software.

To find this file simply display the version, it is presented in the last line:

	python3 makehuman -V



