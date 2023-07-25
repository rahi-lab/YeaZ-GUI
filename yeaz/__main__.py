

def _setup_gui():
    try:
        from PyQt6.QtCore import Qt
    except Exception as e:
        txt = (
            'To run the GUI YeaZ needs to install a package called `PyQt6`.\n\n'
            'You can let YeaZ install it now, or you can abort (press "n")\n'
            'and install it manually with the following command:\n\n'
            'pip install PyQt6\n'
        )
        print('-'*60)
        print(txt)
        while True:
            answer = input('Do you want to install PyQt6 now ([y]/n)? ')
            if answer.lower() == 'y' or not answer:
                import subprocess
                import sys
                subprocess.check_call(
                    [sys.executable, '-m', 'pip', 'install', '-U', 'PyQt6']
                )
                warn_restart = True
                break
            elif answer.lower() == 'n':
                raise e
            else:
                print(
                    f'"{answer}" is not a valid answer. '
                    'Type "y" for "yes", or "n" for "no".'
                )

def run():
    _setup_gui()
    
    print('Initializing application...')
    
    import sys
    from PyQt6.QtWidgets import QApplication
    
    from .GUI_main import App
    #this file contains a dialog window which is opened before the main program
    #and allows to load the nd2 and hdf files by browsing through the computer.
    from .disk import DialogFileBrowser as dfb
    
    app = QApplication(sys.argv)
    
    # If two arguments are given, make them nd2name and hdfname
    if len(sys.argv)==3:
        nd2name1 = sys.argv[1]
        hdfname1 = sys.argv[2]
        ex = App(nd2name1, hdfname1, '')
        print('------------------------------------------------ Welcome to YeaZ-GUI -------------------------------------------------------')

        sys.exit(app.exec())
    
    # Launch file browser otherwise
    else:
        wind = dfb.FileBrowser()
        if wind.exec():
            nd2name1 = wind.nd2name 
            hdfname1 = wind.hdfname
            hdfnewname = wind.newhdfname

            ex = App(str(nd2name1), str(hdfname1), str(hdfnewname))
            print('------------------------------------------------ Welcome to YeaZ-GUI -------------------------------------------------------')
            sys.exit(app.exec())
        else:
            app.exit()