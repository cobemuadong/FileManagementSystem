from io import BufferedReader
import os
from byte_decode import *
from AttributeHeader import *


class Node:
    """
    Lớp đối tượng lưu các thông tin về id cha và id con của một mft
    """
    parent_id: int = -1
    children_id: list[int] = []
    sector: int = -1

    def __init__(self, this_id: int):
        self.this_id = this_id


class NTFS:
    """
    Lớp cho volume NTFS và các hàm để xử lý lớp này
    """
    mft_id_list: list[Node] = []
    processing_list: list[int] = []

    def __init__(self, volume: str):
        self.volume = volume

        tmp_fd = os.open(volume, os.O_RDONLY | os.O_BINARY)
        tmp_ptr = os.fdopen(tmp_fd, 'rb')
        tmp_ptr.seek(0)
        boot_buffer = tmp_ptr.read(512)  # boot sector

        # get volume basic information
        self.byte_per_sector = to_dec_le(boot_buffer[11:13])
        self.sector_per_cluster = to_dec_le(boot_buffer[13:14])
        self.reserved_sectors = to_dec_le(boot_buffer[14:14+2])
        self.media_descriptor = boot_buffer[21:21+1].hex()
        self.sector_per_track = to_dec_le(boot_buffer[24:26])
        self.numbers_of_heads = to_dec_le(boot_buffer[26:26+2])
        self.hidden_sectors = to_dec_le(boot_buffer[28:28+4])
        self.total_sectors = to_dec_le(boot_buffer[40:48])
        self.mft_start_cluster = to_dec_le(boot_buffer[48:56])
        self.mftmirr_start_cluster = to_dec_le(boot_buffer[56:64])
        self.mft_size_byte = 2 ** (256 - to_dec_le(boot_buffer[64:68]))
        self.cluster_per_index = to_dec_le(boot_buffer[68:68+4])
        self.volume_serial_number = boot_buffer[72:72+8].hex()

        self.mft_zone_total_sectors = int(self.total_sectors / 8) + 1
        self.mft_id_list = []
        self.__gather_mft_id()
        tmp_ptr.close()

    def printVolumeInformation(self):
        print('----------Volume information---------')
        print('Bytes per sector: ', self.byte_per_sector)
        print('Sectors per cluster (Sc): ', self.sector_per_cluster)
        print('Reserved sectors (Sb): ', self.reserved_sectors)
        print('Media Descriptor: ', self.media_descriptor)
        print('Sector per track: ', self.sector_per_track)
        print('Number of heads: ', self.numbers_of_heads)
        print('Hidden Sectors: ', self.hidden_sectors)
        print('Total sectors: ', self.total_sectors)
        print('MFT begin sector: ', self.mft_start_cluster)
        print('MFT Mirror begin sector: ', self.mftmirr_start_cluster)
        print('Bytes per File Record Segment: ', self.mft_size_byte)
        print('Cluster per Index: ', self.cluster_per_index)
        print('Volume serial number: ', self.volume_serial_number)
        print('-------------------------------------')

    def __gather_mft_id(self):
        fd = os.open(self.volume, os.O_RDONLY | os.O_BINARY)
        ptr = os.fdopen(fd, 'rb')

        sector_no = self.mft_start_cluster * self.sector_per_cluster
        sector_max = sector_no + self.mft_zone_total_sectors

        while sector_no < sector_max:
            # browse sector-by-sector
            ptr.seek(sector_no * self.byte_per_sector)
            buffer = ptr.read(self.byte_per_sector)
            if buffer[0:4] != b'FILE':  # this sector is not an opening of an mft file
                sector_no += 1
                continue

            # if pass here, this sector IS an MFT FILE
            ptr.seek(sector_no * self.byte_per_sector)
            buffer = ptr.read(self.mft_size_byte)
            this_id = to_dec_le(buffer[44:48])
            children: list[int] = []

            # determine if this_id has already existed in mft_id_list or not
            isExist = False
            for i in self.mft_id_list:
                if i.this_id == this_id:
                    isExist = True
                    break

            # flag to define what kind of file is this
            flag = to_dec_le(buffer[22:24])

            # in case there is "FILE" signature but is not an mft record
            if flag not in [1, 3, 5, 7, 9, 13]:
                sector_no += 1
                continue

            # flag 1: this is a file
            if flag in [1, 5, 7, 9, 13]:
                if isExist == True:
                    for i in self.mft_id_list:
                        if i.this_id == this_id:
                            i.sector = sector_no
                            i.children_id = children
                            break
                else:
                    node = Node(this_id)
                    node.sector = sector_no
                    node.children_id = children
                    self.mft_id_list.append(node)
                sector_no += 2
                continue

            # flag 3: this is a directory
            # if pass this, this mft record is for a directory
            # go to attribute 0x90
            curr_offset = to_dec_le(buffer[20:22])  # offset to first attribute
            while curr_offset < self.mft_size_byte:
                attr_signature = to_dec_le(buffer[curr_offset:curr_offset+4])
                if attr_signature == 144:  # 0x90 = 144
                    break
                curr_offset += to_dec_le(buffer[curr_offset+4:curr_offset+8])

            # resident flag to know whether the index entry is in this record or not
            flag_offset = curr_offset + \
                to_dec_le(buffer[curr_offset+20:curr_offset+22]) + 28
            resident_flag = to_dec_le(buffer[flag_offset:flag_offset+1])

            if resident_flag == 0:  # index entry inside this record
                max_offset = curr_offset + \
                    to_dec_le(buffer[curr_offset+4:curr_offset+8])
                curr_offset = curr_offset + \
                    to_dec_le(buffer[curr_offset+20:curr_offset+22]) + 32

                while curr_offset < max_offset:
                    child_id = to_dec_le(buffer[curr_offset:curr_offset+4])
                    check_this_id = to_dec_le(
                        buffer[curr_offset+16:curr_offset+20])
                    if check_this_id != this_id:
                        break
                    if child_id != 0:
                        children.append(child_id)

                    # move to next
                    curr_offset += to_dec_le(
                        buffer[curr_offset+8:curr_offset+10])

            elif resident_flag == 1:  # index entry outside this record
                # move to attribute 0xA0 to get the INDX sector
                while curr_offset < self.mft_size_byte:
                    attr_signature = to_dec_le(
                        buffer[curr_offset:curr_offset+4])
                    if attr_signature == 160:  # 0xA0 = 160
                        break
                    curr_offset += to_dec_le(
                        buffer[curr_offset+4:curr_offset+8])

                datarun_offset = curr_offset + \
                    to_dec_le(buffer[curr_offset+32:curr_offset+34])
                datarun = parse_datarun(
                    buffer[datarun_offset:datarun_offset+8])

                cluster_max = datarun[1]
                cluster_start = datarun[2]

                cluster_count = 0
                while cluster_count < cluster_max:  # each cluster loop
                    ptr.seek((cluster_start + cluster_count) *
                             self.sector_per_cluster*self.byte_per_sector)
                    temp_buffer = ptr.read(
                        self.sector_per_cluster*self.byte_per_sector)

                    # find the first index entry and plus 18h = 24d
                    temp_offset = to_dec_le(temp_buffer[24:24+4]) + 24
                    # each index entry loop
                    while temp_offset < self.sector_per_cluster * self.byte_per_sector:
                        child_id = to_dec_le(
                            temp_buffer[temp_offset:temp_offset+4])
                        check_this_id = to_dec_le(
                            temp_buffer[temp_offset+16:temp_offset+20])
                        if check_this_id != this_id:
                            break
                        if child_id != 0:
                            children.append(child_id)

                        # move to next
                        temp_offset += to_dec_le(
                            temp_buffer[temp_offset+8:temp_offset+10])

                    cluster_count += 1

            # write to mft_id_list
            if isExist == True:
                for i in self.mft_id_list:
                    if i.this_id == this_id:
                        i.children_id = children
                        i.sector = sector_no
                        break
            else:
                node = Node(this_id)
                node.children_id = children
                node.sector = sector_no
                self.mft_id_list.append(node)

            # update children's parent_id
            for i in children:
                isExist = False
                for j in self.mft_id_list:
                    if j.this_id == i:
                        j.parent_id = this_id
                        isExist = True
                        break

                if isExist == False:
                    node = Node(i)
                    node.parent_id = this_id
                    self.mft_id_list.append(node)

            sector_no += 2

        # append
        for i in self.mft_id_list:
            if i.this_id == 5:
                i.children_id.append(0)
                break

        self.mft_id_list[0].parent_id = 5
        ptr.close()

    def ReadFileTextBySector(self, sector):
        tmp_fd = os.open(self.volume, os.O_RDONLY | os.O_BINARY)
        tmp_ptr = os.fdopen(tmp_fd, 'rb')
        tmp_ptr.seek(sector*self.byte_per_sector)

        buffer = tmp_ptr.read(self.mft_size_byte)
        current = 0

        # Find attribute $80 $DATA
        current = to_dec_le(buffer[20:22])
        while current < 1024:
            attr_signature = to_dec_le(
                buffer[current:current+4])
            if attr_signature == 128:
                break
            current += to_dec_le(
                buffer[current+4:current+8])

        return self.ReadFileText(tmp_ptr, buffer, current)

    def ReadFileText(self, tmp_ptr: BufferedReader, string: bytes, current):
        header = ReadAttributeHeader(string, current)
        if (header.resident_flag == 0):
            if (header.length_of_attribute % 2 != 0):
                header.length_of_attribute += 1
            return string[current+header.offset_to_attribute: current+header.offset_to_attribute+header.length_of_attribute] \
                .decode("utf-8", errors='replace')
        else:
            datarun = string[current+header.run_offset: current+header.length]
            datarun_list = parse_datarun2(datarun)

            if (header.real_size % 2 != 0):
                header.real_size += 1
            if (header.real_size <= self.byte_per_sector*self.cluster_per_index):
                cluster = datarun_list[0][1]
                tmp_ptr.seek(cluster*8*512)
                temp = tmp_ptr.read(1024*header.allocated_size)
                return temp[0:header.real_size].decode("utf-8", errors='replace')

            total_byte_left = header.real_size
            data = []
            for index in datarun_list:
                cluster = index[1]
                cluster_count = index[0]
                tmp_ptr.seek(cluster*8*512)
                buffer = tmp_ptr.read(cluster_count*8*512)
                byte_read = total_byte_left > cluster_count*8 * \
                    512 and total_byte_left or cluster_count*8*512
                data.append(buffer[0:byte_read].decode(
                    'utf-8', errors='ignore'))
                print(''.join(data))
            return ' '.join(data)

    def ReadFileName(self, sector: int):
        tmp_fd = os.open(self.volume, os.O_RDONLY | os.O_BINARY)
        tmp_ptr = os.fdopen(tmp_fd, 'rb')
        tmp_ptr.seek(sector*self.byte_per_sector)

        buffer = tmp_ptr.read(self.mft_size_byte)
        current = 0

        # Find attribute $30 $FILE_NAME
        current = to_dec_le(buffer[20:22])
        while current < 1024:
            attr_signature = to_dec_le(
                buffer[current:current+4])
            if attr_signature == 48:
                break
            current += to_dec_le(
                buffer[current+4:current+8])

        header = ReadAttributeHeader(buffer, current)
        if (header.resident_flag == 0):
            if (header.length_of_attribute % 2 != 0):
                header.length_of_attribute += 1
    
            return buffer[current+header.offset_to_attribute+66: current+header.offset_to_attribute+header.length_of_attribute].decode("utf-16le", errors='replace')
        
        return ""

    def ReadSize(self, sector:int):
        tmp_fd = os.open(self.volume, os.O_RDONLY | os.O_BINARY)
        tmp_ptr = os.fdopen(tmp_fd, 'rb')
        tmp_ptr.seek(sector*self.byte_per_sector)

        buffer = tmp_ptr.read(self.mft_size_byte)
        current = 0
        current = to_dec_le(buffer[20:22])
        attr_signature = 0
        while current < 1024:
            attr_signature = to_dec_le(
                buffer[current:current+4])
            if attr_signature == 128:                
                break
            current += to_dec_le(
            buffer[current+4:current+8])
        if(attr_signature != 128):
            return -1
        header = ReadAttributeHeader(buffer, current)
        if(header.resident_flag == 0):
            return header.length_of_attribute
        else:
            return header.real_size

    def ReadFilePermission(self, sector:int):
        file_permission_table = {
            0: 'R',
            1: 'H',
            2: 'S',
            5: 'A',
            6: 'D',
            7: 'N',
            8: 'T'
        }
    
        #Find attribute $10
        tmp_fd = os.open(self.volume, os.O_RDONLY | os.O_BINARY)
        tmp_ptr = os.fdopen(tmp_fd, 'rb')
        tmp_ptr.seek(sector*self.byte_per_sector)

        buffer = tmp_ptr.read(self.mft_size_byte)
        current = 0
        current = to_dec_le(buffer[20:22])
        attr_signature = 0
        while current < 1024:
            attr_signature = to_dec_le(buffer[current:current+4])
            if attr_signature == 16:                
                break
            current += to_dec_le(
            buffer[current+4:current+8])
        if(attr_signature != 16):
            return -1
        header = ReadAttributeHeader(buffer, current)
        file_attr = ''
        if(header.resident_flag == 0):
            permission = bin(to_dec_le(buffer[current+56:current+64])).lstrip('0b')
            for i in range(1,len(permission)+1):
                if(permission[-i] == '1'):
                    file_attr+=file_permission_table[i]
            return file_attr
        else:
            return -1
    

    def command_help(self, cmd: str):
        """
        handle 'help' command
        """
        command = cmd.split()
        if len(command) > 1:
            print("'" + cmd + "' is not a valid 'help' command,")
            print("try typing 'help'")
            return

        print("\tHere are all available commands\n")
        print("{:<24}Show all file and folder in current directory".format("'ls'"))
        print("{:<24}Go to directory".format("'cd <dir>'"))
        print("{:<24}Show .txt file content".format("'cat <filename.txt>'"))
        print("{:<24}Go back to parent directory".format("'back'"))
        print("{:<24}Clear screen".format("'cls'"))
        print("{:<24}Exit program".format("'exit'"))

    def command_ls(self, cmd: str):
        '''
        handle ls command
        '''
        command = cmd.split()
        if len(command) > 1:
            print("'" + cmd + "' is not a valid 'ls' command,")
            print("try typing only 'ls'")
            return

        children_id: list[int] = []
        curr_id = self.processing_list[len(self.processing_list)-1]
        for i in self.mft_id_list:
            if i.this_id == curr_id:
                children_id = i.children_id

        # print item(s) in directory
        print("")
        print("{:<8}{:<8}{:<16}Name".format("Status","","Size (KB)"))
        for i in children_id:
            sector_no = self.get_mft_sector(i)
            if self.is_hidden(sector_no):
                continue
            filename = self.ReadFileName(sector_no)
            print("{:<8}".format(self.ReadFilePermission(sector_no)),end = "")
            if self.is_directory(sector_no):
                print("{:<24}".format("<DIR>"), end="")
            else:
                print("{:<8}{:<16}".format("",str(round(self.ReadSize(sector_no)/1024, 2))), end="")
            print(filename)

    def command_cd(self, cmd: str):
        '''
        handle 'cd' command
        '''
        des = cmd[3:len(cmd)]
        if (des[0] == des[len(des)-1]) and (ord(des[0]) in [34, 39]):
            des = des[1:len(des)-1]

        # get current directory children id
        children_id = []
        for i in self.mft_id_list:
            if i.this_id == self.processing_list[len(self.processing_list)-1]:
                children_id = i.children_id

        for i in children_id:
            sector_no = self.get_mft_sector(i)
            if self.ReadFileName(sector_no) == des:
                if self.is_directory(sector_no):
                    self.processing_list.append(i)
                else:
                    print("\t'" + des + "' is not a directory")
                return

        print("\tNo such directory")

    def command_cat(self, cmd: str):
        '''
        handle 'cat' command
        '''
        file_name = cmd[4:len(cmd)]
        if (file_name[0] == file_name[len(file_name)-1]) and (ord(file_name[0]) in [34, 39]):
            file_name = file_name[1:len(file_name)-1]

        if file_name[len(file_name)-4:len(file_name)] != ".txt":
            print("Can only read '.txt' files,")
            print("try using other application to read this file")
            return

        for i in self.mft_id_list:
            if i.this_id == self.processing_list[len(self.processing_list)-1]:
                for j in i.children_id:
                    if self.ReadFileName(self.get_mft_sector(j)) == file_name:
                        if self.is_directory(self.get_mft_sector(j)) == False:
                            print(self.ReadFileTextBySector(
                                self.get_mft_sector(j)))
                        else:
                            print("'" + file_name + "' is not a .txt file")
                        return

        print("\tNo such file")
    
    def get_mft_sector(self, id):
        """
        returns the mft sector_no of input id
        """
        for i in self.mft_id_list:
            if i.this_id == id:
                return i.sector

    def print_path(self, list_id: list[int]):
        """
        print the name path of the input list_id 
        """
        print("\n" + self.volume[4] + ":", end="")
        for i in range(1, len(list_id)):
            print(
                "\\" + self.ReadFileName(self.get_mft_sector(list_id[i])), end="")

        print(">", end="")

    def is_hidden(self, sector) -> bool:
        '''
        check if this mft record is set to be hidden to user
        '''
        tmp_fd = os.open(self.volume, os.O_RDONLY | os.O_BINARY)
        tmp_ptr = os.fdopen(tmp_fd, 'rb')
        tmp_ptr.seek(sector*self.byte_per_sector)
        buffer = tmp_ptr.read(self.mft_size_byte)

        # get to attribute 0x10
        offset = to_dec_le(buffer[20:22])  # seek to attribute header
        # seek to attribute content
        offset += to_dec_le(buffer[offset+20:offset+22])

        file_permission = to_dec_le(buffer[offset+32:offset+33])
        if file_permission in [2, 3, 6, 7, 10, 11, 14, 15]:
            return True

        return False

    def is_directory(self, sector) -> bool:
        '''
        check if this mft record is for a directory
        '''
        tmp_fd = os.open(self.volume, os.O_RDONLY | os.O_BINARY)
        tmp_ptr = os.fdopen(tmp_fd, 'rb')
        tmp_ptr.seek(sector*self.byte_per_sector)
        buffer = tmp_ptr.read(self.mft_size_byte)

        flag = to_dec_le(buffer[22:24])
        if flag == 3:
            return True

        return False

    def command_back(self, cmd: str):
        '''
        handle 'back' command
        '''
        command = cmd.split()
        if len(command) > 1:
            print("'" + cmd + "' is not a valid 'back' command,")
            print(" try typing only 'back'")
            return

        if len(self.processing_list) <= 1:
            print("Already at root directory!")
            return

        self.processing_list.pop()

    def command_cls(self, cmd: str):
        '''
        handle clear screen command
        '''
        command = cmd.split()
        if len(command) > 1:
            print("'" + cmd + "' is not a valid 'cls' command,")
            print(" try typing only 'cls'")
            return

        os.system('cls')

    def process_command(self, cmd: str):
        command = cmd.split()

        if command[0] not in ["help", "ls", "cd", "cat", "back", "cls"]:
            print("'" + command[0] + "' is not recognized as a valid command,")
            print("try typing 'help' to show all valid command")
            return

        if command[0] == "help":
            self.command_help(cmd)
        elif command[0] == "ls":
            self.command_ls(cmd)
        elif command[0] == "cd":
            self.command_cd(cmd)
        elif command[0] == "cat":
            self.command_cat(cmd)
        elif command[0] == "back":
            self.command_back(cmd)
        elif command[0] == "cls":
            self.command_cls(cmd)

    def start_shell(self):
        """
        browse volume with command
        """
        shell_fd = os.open(self.volume, os.O_RDONLY | os.O_BINARY)
        shell_ptr = os.fdopen(shell_fd, 'rb')

        self.processing_list = [5]
        command = " "

        while True:
            self.print_path(self.processing_list)
            command = input()
            if command == "exit":
                print("Exiting program!")
                break
            self.process_command(command)

        shell_ptr.close()
