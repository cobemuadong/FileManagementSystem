import struct
from AttributeHeader import *
from AttributeContent import *

def HexLittleEndianToUnsignedDecimal(val: str) -> int:
    if(len(val) == 3):
        val += b'\x00'
    if(len(val) == 5):
        val += b'\x00\x00\x00'
    if (len(val) == 1):
        return int(val.hex(), 16)
    if (len(val) == 2):
        return struct.unpack('<H', val)[0]
    if (len(val) == 4):
        return struct.unpack('<L', val)[0]
    if (len(val) == 8):
        return struct.unpack('<Q', val)[0]

def to_dec(val: bytes):
    result = 0
    for i in reversed(val):
        result = result * 16 * 16 + i
    return result

def ReadAttributeHeader(string: bytes, current: int):
    if (string[current+8] > 0):
        return NonResidentAttributeHeader(
            type=string[current:current+4].hex(),
            length=HexLittleEndianToUnsignedDecimal(
                string[current+4:current+8]),
            resistent_flag=string[current+8],
            name_length=string[current+9],
            name_offset=HexLittleEndianToUnsignedDecimal(
                string[current+10:current+12]),
            flags=HexLittleEndianToUnsignedDecimal(
                string[current+12:current+14]),
            attribute_id=HexLittleEndianToUnsignedDecimal(
                string[current+14:current+16]),
            run_offset=HexLittleEndianToUnsignedDecimal(
                string[current+32:current+34]),
            runlist=string[current+72:current+80],
            real_size=HexLittleEndianToUnsignedDecimal(
                string[current+48:current+48+8]),
            allocated_size=HexLittleEndianToUnsignedDecimal(string[current+40:current+40+8]))
    else:
        return ResidentAttributeHeader(
            type=string[current:current+4].hex(),
            length=HexLittleEndianToUnsignedDecimal(
                string[current+4:current+8]),
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

def ParseRunData2(string: str):
    data_run = []
    current = 0
    temp = 0
    while(current < len(string)):
        if(string[current]==0):
            break
        digit_1 = int(string.hex()[current*2])
        digit_2 = int(string.hex()[current*2+1])
        cluster_count_byte = HexLittleEndianToUnsignedDecimal(string[1+current:1+current+digit_2])
        first_cluster = HexLittleEndianToUnsignedDecimal(string[1+current+digit_2:1+current+digit_2+digit_1]) + temp
        temp = first_cluster
        current+=digit_1+digit_2+1
        data_run.append([cluster_count_byte,first_cluster])

    return data_run

def ReadFileTextFromSector(ptr ,sector):
    ptr.seek(sector)
    buffer = ptr.read(1024)
    current = 0

    #Find attribute $80 $DATA
    current = HexLittleEndianToUnsignedDecimal(buffer[20:22])
    while current < 1024:
        attr_signature = HexLittleEndianToUnsignedDecimal(
            buffer[current:current+4])
        if attr_signature == 128:                
            break
        current += HexLittleEndianToUnsignedDecimal(
        buffer[current+4:current+8])
    
    return ReadFileText(ptr, buffer, current)

def ReadFileText(ptr, string, current):
    header = ReadAttributeHeader(string, current)
    if (header.resistent_flag == 0):
        if (header.length_of_attribute % 2 != 0):
            header.length_of_attribute += 1
        return string[current+header.offset_to_attribute: current+header.offset_to_attribute+header.length_of_attribute].decode("utf-8", errors='replace')
    else:
        datarun = string[current+header.run_offset: current+header.length]
        datarun_list = ParseRunData2(datarun)
        
        if (header.real_size % 2 != 0):
            header.real_size += 1
        if(header.real_size <= 1024):
            cluster = datarun_list[0][1]
            ptr.seek(cluster*8*512)
            temp = ptr.read(1024*header.allocated_size)
            return temp[0:header.real_size].decode("utf-8", errors='replace')

        total_byte_left = header.real_size
        data = []
        for index in datarun_list:
            cluster = index[1]
            cluster_count = index[0]
            ptr.seek(cluster*8*512)
            buffer = ptr.read(cluster_count*8*512)
            byte_read = total_byte_left > cluster_count*8*512 and total_byte_left or cluster_count*8*512
            data.append(buffer[0:byte_read].decode('utf-8', errors = 'ignore'))
            print(' '.join(data))
        return ' '.join(data)
            
import os
disk_fd = os.open(r'\\.\C:', os.O_RDONLY | os.O_BINARY)
tmp = os.fdopen(disk_fd, 'rb')
tmp.seek(357968896)
print(ReadFileTextFromSector(tmp,9924641792))