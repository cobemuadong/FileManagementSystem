from PartitionBootSector import *
from AttributeContent import *
import os
import struct

disk_fd = os.open(r'\\.\E:', os.O_RDONLY | os.O_BINARY)
# data = os.read(disk_fd,512)
tmp = os.fdopen(disk_fd, 'rb')
i = 1024
# tmp.seek(i)
tmp.seek(0)

# This function convert hex string in little endian into unsigned int


def MREF(mft_reference):
    """
    Given a MREF/mft_reference, return the record number part.
    """
    mft_reference = struct.unpack_from("<Q", mft_reference)[0]
    return mft_reference & 0xFFFFFFFFFFFF

def ParseRunData(string):
    size_byte = int(string.hex()[0])
    cluster_count_byte = int(string.hex()[1])
    print(string.hex())
    first_cluster = HexLittleEndianToUnsignedDecimal(string[1+cluster_count_byte:size_byte+cluster_count_byte+1])
    return (size_byte,cluster_count_byte,first_cluster)


def HexLittleEndianToUnsignedDecimal(val: str) -> int:
    if(len(val) == 1):
        return int(val.hex(), 16)
    if(len(val) == 2):
        return struct.unpack('<H', val)[0]
    if(len(val) == 4):
        return struct.unpack('<L', val)[0]
    if(len(val) == 8):
        return struct.unpack('<Q', val)[0]

# This function convert hex string in little endian into signed int

def HexLittleEndianToSignedDecimal(val: str) -> int:
    if(len(val) == 1):
        return struct.unpack('<b', val)[0]
    if(len(val) == 2):
        return struct.unpack('<h', val)[0]
    if(len(val) == 4):
        return struct.unpack('<l', val)[0]
    if(len(val) == 8):
        return struct.unpack('<q', val)[0]


def ReadAttributeHeader(string: bytes, current: int):
    if(string[current+8] > 0):
        return NonResidentAttributeHeader(
        type=string[current:current+4].hex(),
        length=HexLittleEndianToUnsignedDecimal(string[current+4:current+8]),
        resistent_flag=string[current+8],
        name_length=string[current+9],
        name_offset=HexLittleEndianToUnsignedDecimal(string[current+10:current+12]),
        flags=HexLittleEndianToUnsignedDecimal(string[current+12:current+14]),
        attribute_id=HexLittleEndianToUnsignedDecimal(string[current+14:current+16]),
        run_offset=HexLittleEndianToUnsignedDecimal(string[current+32:current+34]),
        runlist = string[current+72:current+80],
        real_size=HexLittleEndianToUnsignedDecimal(string[current+48:current+48+8]),
        allocated_size=HexLittleEndianToUnsignedDecimal(string[current+40:current+40+8]))
    else:
        return ResidentAttributeHeader(
        type=string[current:current+4].hex(),
        length=HexLittleEndianToUnsignedDecimal(string[current+4:current+8]),
        resistent_flag=string[current+8],
        name_length=string[current+9],
        name_offset=string[current+10:current+12],
        flags=string[current+12:current+14],
        attribute_id=string[current+14:current+15],
        length_of_attribute=HexLittleEndianToUnsignedDecimal(
            string[current+16:current+20]),
        offset_to_attribute=HexLittleEndianToUnsignedDecimal(
            string[current+20:current+22]),
        indexed_flag=0)


def ReadAttribute30(string: bytes, current: int) -> Attribute30:
    header = ReadAttributeHeader(string, current)
    filename_length = string[current+header.offset_to_attribute+64]
    filename = string[current+header.offset_to_attribute+66:current +
                      header.offset_to_attribute+header.length_of_attribute]
    if(filename.decode("utf-16le").startswith("$")):
        return None
    a30 = Attribute30(
        header=header,
        filename_length=filename_length,
        filename=filename.decode("utf-16le")
    )
    return a30

def ReadIndexEntry(string, cur) -> IndexEntry:
    return IndexEntry(
        file_ref=MREF(string[cur:cur+8]),
        parent_ref=MREF(string[cur+16:cur+24]),
        length_of_index_entry=HexLittleEndianToUnsignedDecimal(
            string[cur+8:cur+10]),
        length_of_stream=HexLittleEndianToUnsignedDecimal(
            string[cur+10:cur+12]),
        index_flags=HexLittleEndianToUnsignedDecimal(
            string[cur+12:cur+14]),
        size_of_file=HexLittleEndianToUnsignedDecimal(
            string[cur+64:cur+72]),
        length_of_filename=string[cur+80],
        filename=string[cur+82:cur+82+string[cur+80]*2].decode("utf-16le")
    )

def ReadAttribute90(string: bytes, current: int) -> Attribute90:
    header = ReadAttributeHeader(string, current)

    cur = current + 32
    entries: list[IndexEntry] = []
    index_root = IndexRoot(
        attribute_type=string[cur:cur+4].hex(),
        collation_rule=string[cur+4:cur+8].hex(),
        allocation_index_entry=HexLittleEndianToUnsignedDecimal(
            string[cur+8:cur+12]),
        cluster_per_index_record=string[12],
    )
    cur += 16
    index_header = IndexHeader(
        first_entry_offset=HexLittleEndianToUnsignedDecimal(string[cur:cur+4]),
        index_entries_size=HexLittleEndianToUnsignedDecimal(
            string[cur+4:cur+8]),
        allocated_size=HexLittleEndianToUnsignedDecimal(string[cur+8:cur+12]),
        has_subnode_flag=string[cur+12]
    )
    if(index_header.has_subnode_flag != 0):
        return None
    cur += 16
    while (cur + 32 + 16 < current + header.length - 8):
        index_entry = ReadIndexEntry(string,cur)
        entries.append(index_entry)
        cur += index_entry.length_of_index_entry
    a90 = Attribute90(header=header,
                      index_header=index_header,
                      index_root=index_root,
                      index_entries=entries)
    return a90


def readPBSTable(string) -> PartitionBootSector:
    return PartitionBootSector(
        bytes_per_sector=HexLittleEndianToUnsignedDecimal(string[11:11+2]),
        sectors_per_cluster=HexLittleEndianToUnsignedDecimal(string[13:13+1]),
        reserved_sectors=HexLittleEndianToUnsignedDecimal(string[14:14+2]),
        media_descriptor=string[21:21+1].hex(),
        sectors_per_track=HexLittleEndianToUnsignedDecimal(string[24:24+2]),
        numbers_of_heads=HexLittleEndianToUnsignedDecimal(string[26:26+2]),
        hidden_sectors=HexLittleEndianToUnsignedDecimal(string[28:28+4]),
        total_sectors=HexLittleEndianToUnsignedDecimal(string[40:40+8]),
        mft_cluster_number=HexLittleEndianToUnsignedDecimal(string[48:48+8]),
        mftmirr_cluster_number=HexLittleEndianToUnsignedDecimal(
            string[56:56+8]),
        bytes_per_file_record_segment=2**abs(
            HexLittleEndianToSignedDecimal(string[64:64+1])),
        cluster_per_index=HexLittleEndianToUnsignedDecimal(string[68:68+4]),
        volume_serial_number=string[72:72+8].hex())

def ReadFileText(string, current, i):
    header = ReadAttributeHeader(string,current)
    if(header.resistent_flag == 0):
        if(header.length_of_attribute % 2 != 0):
            header.length_of_attribute+=1
        return string[current+header.offset_to_attribute: current+header.offset_to_attribute+header.length_of_attribute].decode("ascii")
    else:
        offset = string[current+header.run_offset: current+header.run_offset+8]
        first_cluster = ParseRunData(offset)[2]
        tmp.seek(first_cluster*8*512)
        if(header.real_size%2!=0):
            header.real_size+=1
        temp = tmp.read(1024*header.allocated_size)
        tmp.seek(i)
        print(first_cluster)
        return temp[0:header.real_size].decode("utf-8", errors='replace')

def isDirectory(string, current):
    if(string[current+8] > 0):
        return False
    if(string[current+24:current+24+8].decode("utf-16le") == "$I30"):
        return True

def hasIndexEntry(string, current):
    if(string[current]):
        pass

def ReadNode() -> list[Node]:
    lists:list[Node] = []
    tmp.seek(0)
    string = tmp.read(1024)
    pbstable = readPBSTable(string)
    i = pbstable.sectors_per_cluster*pbstable.mft_cluster_number * \
        pbstable.bytes_per_sector + pbstable.bytes_per_file_record_segment*26
    skipped = 0
    while True:
        if(skipped >= 100):
            break
        tmp.seek(i)
        i += 1024
        string = tmp.read(1024)
        string = tmp.read(pbstable.bytes_per_file_record_segment)
        if(string[0:4] == b'FILE'):
            first_attribute = HexLittleEndianToUnsignedDecimal(string[20:21])
            attribute_type = HexLittleEndianToSignedDecimal(
                string[first_attribute:first_attribute+4])
            current = first_attribute
            id = HexLittleEndianToUnsignedDecimal(string[44:44+4])
            children_id:list[int] = []
            while True:
                if(string[current:current+4] == b'\xff\xff\xff\xff'):
                    break
                attribute_type = HexLittleEndianToSignedDecimal(
                    string[current:current+4])
                if(attribute_type == 144):
                    a90 = ReadAttribute90(string, current)
                    if(a90 == None):
                        break
                    if(string[current+12] != 0):
                        break
                    if(a90.index_entries != None):
                        for e in a90.index_entries:
                            children_id.append(e.file_ref)            
                    current += a90.header.length
                else:
                    current += ReadAttributeHeader(string, current).length
            
            lists.append(Node(id,children_id,i))
        if(i >= pbstable.total_sectors*pbstable.bytes_per_sector*0.5):
            break
    return lists

def Read() -> list[File]:
    files: list[File] = []
    tmp.seek(0)
    string = tmp.read(1024)
    pbstable = readPBSTable(string)
    i = pbstable.sectors_per_cluster*pbstable.mft_cluster_number * \
        pbstable.bytes_per_sector + pbstable.bytes_per_file_record_segment*26
    skipped = 0
    while True:
        if(skipped >= 100):
            break
        tmp.seek(i)
        i += 1024
        string = tmp.read(1024)
        string = tmp.read(pbstable.bytes_per_file_record_segment)
        if(string[0:4] == b'FILE'):
            first_attribute = HexLittleEndianToUnsignedDecimal(string[20:21])
            attribute_type = HexLittleEndianToSignedDecimal(
                string[first_attribute:first_attribute+4])
            current = first_attribute
            a30 = None
            a90 = None
            id = HexLittleEndianToUnsignedDecimal(string[44:44+4])
            file_id_array: list[int] = []
            for f in files:
                if(f.index):
                    for e in f.index.index_entries:
                        file_id_array.append(e.file_ref)
            if(id in file_id_array):
                continue
            while True:
                if(string[current:current+4] == b'\xff\xff\xff\xff'):
                    break
                attribute_type = HexLittleEndianToSignedDecimal(
                    string[current:current+4])
                if(attribute_type == 48):
                    a30 = ReadAttribute30(string, current)
                    if(a30 == None):
                        skipped += 1
                        break
                    current += a30.header.length
                elif(attribute_type == 144):
                    a90 = ReadAttribute90(string, current)
                    if(a90 == None):
                        break
                    current += a90.header.length
                elif(attribute_type == 128):
                    if(a30.filename[-3:] == "txt"):
                        print(ReadFileText(string, current,i))
                    current += ReadAttributeHeader(string, current).length    
                else:
                    current += ReadAttributeHeader(string, current).length
            if(a30 != None or a90 != None):
                files.append(File(a30, a90))
        if(i >= pbstable.total_sectors*pbstable.bytes_per_sector*0.5):
            break
    return files

# lists = ReadNode()
# for i in lists:
#     if(i.parent_id == None):
#         print(i.this_id)
files = Read()
for f in files:
    f.printTree()


# count = 0
# s = tmp.read(1024)
# pbstable = PartitionBootSector(
#     bytes_per_sector=HexLittleEndianToUnsignedDecimal(s[11:11+2]),
#     sectors_per_cluster=HexLittleEndianToUnsignedDecimal(s[13:13+1]),
#     reserved_sectors=HexLittleEndianToUnsignedDecimal(s[14:14+2]),
#     media_descriptor=s[21:21+1].hex(),
#     sectors_per_track=HexLittleEndianToUnsignedDecimal(s[24:24+2]),
#     numbers_of_heads=HexLittleEndianToUnsignedDecimal(s[26:26+2]),
#     hidden_sectors=HexLittleEndianToUnsignedDecimal(s[28:28+4]),
#     total_sectors=HexLittleEndianToUnsignedDecimal(s[40:40+8]),
#     mft_cluster_number=HexLittleEndianToUnsignedDecimal(s[48:48+8]),
#     mftmirr_cluster_number=HexLittleEndianToUnsignedDecimal(s[56:56+8]),
#     bytes_per_file_record_segment=2**abs(
#         HexLittleEndianToSignedDecimal(s[64:64+1])),
#     cluster_per_index=HexLittleEndianToUnsignedDecimal(s[68:68+4]),
#     volume_serial_number=s[72:72+8].hex()
# )

# pbstable.printVolumeInformation()

# a = pbstable.sectors_per_cluster*pbstable.mft_cluster_number * \
#     pbstable.bytes_per_sector + 1024*26
# i = a
# tmp.seek(i)
# skipped = 0
# files: list[File] = []
# count = 0
# break_flag = False
# while True:
#     s = tmp.read(1024)  # should read from pbp
#     count += 1
#     if(s[0:4].hex() == "46494c45"):
#         start = int(s[20:21].hex(), 16)
#         current = start
#         file: File
#         while current < 1024:
#             size_of_attribute = HexLittleEndianToUnsignedDecimal(
#                 s[current+4:current+7+1])
#             size_of_attribute_content = HexLittleEndianToUnsignedDecimal(
#                 s[current+16:current+19+1])
#             first_offset_of_content = HexLittleEndianToUnsignedDecimal(
#                 s[current+20:current+21])
#             header: AttributeHeader
#             a30: Attribute30 = None
#             a90: Attribute90 = None
#             if(HexLittleEndianToUnsignedDecimal(s[current:current+1]) == 48):
#                 if(s[current+first_offset_of_content+66:current+first_offset_of_content+size_of_attribute_content]
#                    .decode("utf-16le").startswith("$")):
#                     break
#                 header = AttributeHeader(
#                     type=s[current:current+4].hex(),
#                     length=HexLittleEndianToUnsignedDecimal(
#                         s[current+4:current+8]),
#                     resistent_flag=s[current+8],
#                     name_length=s[current+9],
#                     name_offset=s[current+10:current+12],
#                     flags=s[current+12:current+14],
#                     attribute_id=s[current+14:current+15],
#                     length_of_attribute=HexLittleEndianToUnsignedDecimal(
#                         s[current+16:current+20]),
#                     offset_to_attribute=HexLittleEndianToUnsignedDecimal(
#                         s[current+20:current+22]),
#                     indexed_flag=0)
#                 filename_length = s[current+first_offset_of_content+64]
#                 filename = s[current+first_offset_of_content+66:current +
#                              first_offset_of_content+size_of_attribute_content]
#                 a30 = Attribute30(
#                     header=header,
#                     filename_length=filename_length,
#                     filename=filename.decode("utf-16le")
#                 )
#                 # filename = s[current+first_offset_of_content+66:current+first_offset_of_content+size_of_attribute_content]
#                 # print(filename.decode("utf-16le"))
#             if(HexLittleEndianToUnsignedDecimal(s[current:current+1]) == 144):
#                 header = AttributeHeader(
#                     type=HexLittleEndianToSignedDecimal(s[current:current+4]),
#                     length=HexLittleEndianToUnsignedDecimal(
#                         s[current+4:current+8]),
#                     resistent_flag=s[current+8],
#                     name_length=s[current+9],
#                     name_offset=s[current+10:current+12],
#                     flags=s[current+12:current+14],
#                     attribute_id=s[current+14:current+15],
#                     length_of_attribute=HexLittleEndianToUnsignedDecimal(
#                         s[current+16:current+20]),
#                     offset_to_attribute=HexLittleEndianToUnsignedDecimal(
#                         s[current+20:current+22]),
#                     indexed_flag=0)

#                 cur = current + 32
#                 entries: list[IndexEntry] = []
#                 index_root = IndexRoot(
#                     attribute_type=s[cur:cur+4].hex(),
#                     collation_rule=s[cur+4:cur+8].hex(),
#                     allocation_index_entry=HexLittleEndianToUnsignedDecimal(
#                         s[cur+8:cur+12]),
#                     cluster_per_index_record=s[12],
#                 )
#                 cur += 16
#                 index_header = IndexHeader(
#                     first_entry_offset=HexLittleEndianToUnsignedDecimal(
#                         s[cur:cur+4]),
#                     index_entries_size=HexLittleEndianToUnsignedDecimal(
#                         s[cur+4:cur+8]),
#                     allocated_size=HexLittleEndianToUnsignedDecimal(
#                         s[cur+8:cur+12]),
#                     has_subnode_flag=s[cur+12]
#                 )
#                 if(index_header.has_subnode_flag != 0):
#                     break
#                 cur += 16
#                 while (cur + 32 + 16 < current + header.length - 8):
#                     index_entry = IndexEntry(
#                         length_of_index_entry=HexLittleEndianToUnsignedDecimal(
#                             s[cur+8:cur+10]),
#                         length_of_stream=HexLittleEndianToUnsignedDecimal(
#                             s[cur+10:cur+12]),
#                         index_flags=HexLittleEndianToUnsignedDecimal(
#                             s[cur+12:cur+14]),
#                         size_of_file=HexLittleEndianToUnsignedDecimal(
#                             s[cur+64:cur+72]),
#                         length_of_filename=s[cur+80],
#                         filename=s[cur+82:cur+82+s[cur+80]
#                                    * 2].decode("utf-16le")
#                     )
#                     entries.append(index_entry)
#                     cur += index_entry.length_of_index_entry
#                 a90 = Attribute90(header=header,
#                                   index_header=index_header,
#                                   index_root=index_root,
#                                   index_entries=entries)

#                 break_flag = True

#             current = current + size_of_attribute
#             if(size_of_attribute_content == 0):
#                 break
#             if(break_flag):
#                 break
#     else:
#         skipped += 1
#     # if(i>=pbstable.total_sectors*pbstable.bytes_per_sector*0.5):
#     #     break
#     if(skipped >= 100):
#         break
#     i += 1024
#     tmp.seek(i)

# f: File
# for f in files:
#     print(f.file_name.filename)
#     f.printTree()
