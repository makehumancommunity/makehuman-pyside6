# makehuman-pyside6
makehuman new version test

first tests with a new version, needs PySide6 installed

windows start:
        call makehuman on CLI: python3 makehuman -v15 -A
        (-v15 is verbose high level, -A admininstrator for "system" targets)

        start program, hm08 mesh should be visible

        go to preferences, change MakeHuman user home to e.g. d:\shared\mhuser and logfile to d:\shared\mhuser\log if needed
                press save

        go to settings:
                create binaries, system targets (all targets are converted to binaries)
                create binaries, system objects (base.obj and eyes are converted to binaries [.mhbin])

        quit program



        call getpackages on CLI: python3 getpackages.py
	The system assets are downloaded, but as long as it is still development:
                install under user space (1) **
		and enter d to download

	(also possible with gui, downloads, but not yet recommended)


        now start without -A option
                python3 makehuman -v15

        go to settings:
                create user 3d objects (conversion of mhclo + obj files to mhbin file)

		(if the objects were loaded to system space, here create binaries, system objects must be used again)

	for the next start makehuman should only use binaries
