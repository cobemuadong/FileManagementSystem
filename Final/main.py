import os
from Shell import Shell
from NTFS import *

def define_File_System(volume) -> str:
    tmp_fd = os.open(volume, os.O_RDONLY | os.O_BINARY)
    tmp_ptr = os.fdopen(tmp_fd, 'rb')
    buffer = tmp_ptr.read(512)

    if buffer[3:7] == b'NTFS':
        return "NTFS"
    elif buffer[82:87] == b'FAT32':
        return "FAT32"
    else:
        return "None"
    

def main():
    try:
        shell = Shell()
        shell.select_disk()

        system_type = define_File_System(shell.disk_path)

        if system_type == "NTFS":
            ntfs = NTFS(shell.disk_path)
            ntfs.printVolumeInformation()
            ntfs.start_shell()
        elif system_type == "FAT32":
            with shell.create_fileobject() as f:
                shell.initialize_root_directory(f)
                print('Root directory da duoc khoi tao!\n')
                shell.start_shell()
        else:
            print("File system not supported")
    except KeyboardInterrupt: 
        pass

if __name__ == '__main__':
    main()
