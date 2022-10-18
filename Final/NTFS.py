import os
from byte_decode import *

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
        self.sector_per_track = to_dec_le(boot_buffer[24:26])
        self.total_sectors = to_dec_le(boot_buffer[40:48])
        self.mft_start_cluster = to_dec_le(boot_buffer[48:56])
        self.mftmirr_start_cluster = to_dec_le(boot_buffer[56:64])
        self.mft_size_byte = 2 ** (256 - to_dec_le(boot_buffer[64:68]))
        
        self.mft_zone_total_sectors = int(self.total_sectors / 8) + 1
        self.__gather_mft_id()

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

                    temp_offset = 64
                    if this_id == 5:    # $dot record is a bit different
                        temp_offset += 24
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

        for i in self.mft_id_list:
            if i.this_id == 5:
                i.children_id.append(0)
                break

        self.mft_id_list[0].parent_id = 5
        

    
    


