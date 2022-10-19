import traceback
from Shell import Shell

def main():
    try:
        shell = Shell()
        shell.select_disk()

        with shell.create_fileobject() as f:
            shell.initialize_root_directory(f)
            print('Root directory da duoc khoi tao!\n')
            shell.start_shell()
    except KeyboardInterrupt: 
        pass

if __name__ == '__main__':
    main()
