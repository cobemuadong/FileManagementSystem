from io import BufferedReader
import os
from byte_decode import *
from AttributeHeader import *

class Node:
    """
    Lớp đối tượng lưu các thông tin về id cha và id con của một mft
    """
    parent_id:int = -1
    children_id:list[int] = []
    sector:int = -1

    def __init__(self, this_id:int):
        self.this_id = this_id
        

class NTFS:
    """
    Lớp cho volume NTFS và các hàm để xử lý lớp này
    """
    mft_id_list:list[Node] = []

    def __init__(self, volume:str):
        self.volume = volume

        tmp_fd = os.open(volume, os.O_RDONLY | os.O_BINARY)
        tmp_ptr = os.fdopen(tmp_fd, 'rb')
        tmp_ptr.seek(0)
        boot_buffer = tmp_ptr.read(512) #boot sector

        #get volume basic information
        self.byte_per_sector = to_dec_le(boot_buffer[11:13])
        self.sector_per_cluster = to_dec_le(boot_buffer[13:14])
        self.reserved_sectors=to_dec_le(boot_buffer[14:14+2])
        self.media_descriptor=boot_buffer[21:21+1].hex()
        self.sector_per_track = to_dec_le(boot_buffer[24:26])
        self.numbers_of_heads=to_dec_le(boot_buffer[26:26+2])
        self.hidden_sectors=to_dec_le(boot_buffer[28:28+4])
        self.total_sectors = to_dec_le(boot_buffer[40:48])
        self.mft_start_cluster = to_dec_le(boot_buffer[48:56])
        self.mftmirr_start_cluster = to_dec_le(boot_buffer[56:64])
        self.mft_size_byte = 2 ** (256 - to_dec_le(boot_buffer[64:68]))
        self.cluster_per_index=to_dec_le(boot_buffer[68:68+4])
        self.volume_serial_number=boot_buffer[72:72+8].hex()
        
        self.mft_zone_total_sectors = int(self.total_sectors / 8) + 1
        self.mft_id_list = []
        self.__gather_mft_id()
        os.close(tmp_fd)

    def printVolumeInformation(self):
        print('----------Volume information---------')
        print('Bytes per sector: ', self.byte_per_sector)
        print('Sectors per cluster (Sc): ', self.sector_per_cluster)
        print('Reserved sectors (Sb): ', self.reserved_sectors)
        print('Media Descriptor: ', self.media_descriptor)
        print('Sector per track: ', self.sector_per_track)
        print('Number of heads: ', self.numbers_of_heads)
        print('Hidden Sectors: ',self.hidden_sectors)
        print('Total sectors: ',self.total_sectors)
        print('MFT begin sector: ',self.mft_start_cluster)
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
            #browse sector-by-sector
            ptr.seek(sector_no * self.byte_per_sector)
            buffer = ptr.read(self.byte_per_sector)
            if buffer[0:4] != b'FILE':  #this sector is not an opening of an mft file
                sector_no += 1
                continue

            #if pass here, this sector IS an MFT FILE
            ptr.seek(sector_no * self.byte_per_sector)
            buffer = ptr.read(self.mft_size_byte)
            this_id = to_dec_le(buffer[44:48])
            children:list[int] = []

            #determine if this_id has already existed in mft_id_list or not
            isExist = False
            for i in self.mft_id_list:
                if i.this_id == this_id:
                    isExist = True
                    break

            # flag to define what kind of file is this
            flag = to_dec_le(buffer[22:24])

            if flag not in [1,3,5,7,9,13]: #in case there is "FILE" signature but is not an mft record
                sector_no += 1
                continue
            
            # flag 1: this is a file
            if flag in [1,5,7,9,13]:
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
            curr_offset = to_dec_le(buffer[20:22]) # offset to first attribute
            while curr_offset < self.mft_size_byte:
                attr_signature = to_dec_le(buffer[curr_offset:curr_offset+4])
                if attr_signature == 144: #0x90 = 144
                    break
                curr_offset += to_dec_le(buffer[curr_offset+4:curr_offset+8])
            
            # resident flag to know whether the index entry is in this record or not
            flag_offset = curr_offset + to_dec_le(buffer[curr_offset+20:curr_offset+22]) + 28
            resident_flag = to_dec_le(buffer[flag_offset:flag_offset+1])

            if resident_flag == 0: # index entry inside this record
                max_offset = curr_offset + to_dec_le(buffer[curr_offset+4:curr_offset+8])
                curr_offset = curr_offset + to_dec_le(buffer[curr_offset+20:curr_offset+22]) + 32

                while curr_offset < max_offset:
                    child_id = to_dec_le(buffer[curr_offset:curr_offset+4])
                    check_this_id = to_dec_le(buffer[curr_offset+16:curr_offset+20])
                    if check_this_id != this_id:
                        break
                    if child_id != 0:
                        children.append(child_id)

                    # move to next
                    curr_offset += to_dec_le(buffer[curr_offset+8:curr_offset+10])

            elif resident_flag == 1: # index entry outside this record
                #move to attribute 0xA0 to get the INDX sector
                while curr_offset < self.mft_size_byte:
                    attr_signature = to_dec_le(buffer[curr_offset:curr_offset+4])
                    if attr_signature == 160: # 0xA0 = 160
                        break
                    curr_offset += to_dec_le(buffer[curr_offset+4:curr_offset+8])

                datarun_offset = curr_offset + to_dec_le(buffer[curr_offset+32:curr_offset+34])
                datarun = parse_datarun(buffer[datarun_offset:datarun_offset+8])

                cluster_max = datarun[1]
                cluster_start = datarun[2]

                cluster_count = 0
                while cluster_count < cluster_max:  # each cluster loop
                    ptr.seek((cluster_start + cluster_count)*self.sector_per_cluster*self.byte_per_sector)
                    temp_buffer = ptr.read(self.sector_per_cluster*self.byte_per_sector)

                    temp_offset = to_dec_le(temp_buffer[24:24+4]) + 24 #find the first index entry and plus 18h = 24d
                    # each index entry loop
                    while temp_offset < self.sector_per_cluster * self.byte_per_sector:
                        child_id = to_dec_le(temp_buffer[temp_offset:temp_offset+4])
                        check_this_id = to_dec_le(temp_buffer[temp_offset+16:temp_offset+20])
                        if check_this_id != this_id:
                            break
                        if child_id != 0:
                            children.append(child_id)

                        # move to next
                        temp_offset += to_dec_le(temp_buffer[temp_offset+8:temp_offset+10])

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

            #update children's parent_id
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
        os.close(fd)
        
    def ReadFileTextBySector(self ,sector):
        tmp_fd = os.open(self.volume, os.O_RDONLY | os.O_BINARY)
        tmp_ptr = os.fdopen(tmp_fd, 'rb')
        tmp_ptr.seek(sector*self.byte_per_sector)

        self.ptr.seek(sector)
        buffer = tmp_ptr.read(self.mft_size_byte)
        current = 0

        #Find attribute $80 $DATA
        current = to_dec_le(buffer[20:22])
        while current < 1024:
            attr_signature = to_dec_le(
                buffer[current:current+4])
            if attr_signature == 128:                
                break
            current += to_dec_le(
            buffer[current+4:current+8])
        
        return self.ReadFileText(tmp_ptr, buffer, current)

    def ReadFileText(self, tmp_ptr:BufferedReader, string, current):
        header = ReadAttributeHeader(string, current)
        if (header.resistent_flag == 0):
            if (header.length_of_attribute % 2 != 0):
                header.length_of_attribute += 1
            os.close(tmp_ptr)    
            return string[current+header.offset_to_attribute: current+header.offset_to_attribute+header.length_of_attribute].decode("utf-8", errors='replace')
        else:
            datarun = string[current+header.run_offset: current+header.length]
            datarun_list = parse_datarun2(datarun)
            
            if (header.real_size % 2 != 0):
                header.real_size += 1
            if(header.real_size <= 1024):
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
                byte_read = total_byte_left > cluster_count*8*512 and total_byte_left or cluster_count*8*512
                data.append(buffer[0:byte_read].decode('utf-8', errors = 'ignore'))

            os.close(tmp_ptr)    
            return ''.join(data)
    
    def ReadFileName(self, sector):
        tmp_fd = os.open(self.volume, os.O_RDONLY | os.O_BINARY)
        tmp_ptr = os.fdopen(tmp_fd, 'rb')
        tmp_ptr.seek(sector*self.byte_per_sector)

        self.ptr.seek(sector)
        buffer = tmp_ptr.read(self.mft_size_byte)
        current = 0

        #Find attribute $30 $FILE_NAME
        current = to_dec_le(buffer[20:22])
        while current < 1024:
            attr_signature = to_dec_le(
                buffer[current:current+4])
            if attr_signature == 48:                
                break
            current += to_dec_le(
            buffer[current+4:current+8])
        
        filename:str
        header = ReadAttributeHeader(buffer, current)
        return filename

