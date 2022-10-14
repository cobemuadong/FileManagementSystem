from dataclasses import dataclass
import os
import struct

disk_fd = os.open(r'\\.\E:',os.O_RDONLY|os.O_BINARY)
data = os.read(disk_fd,512)
tmp = os.fdopen(disk_fd,'rb')
i = 1024
#tmp.seek(i)
tmp.seek(0)

#This function conver hex string in little endian into unsigned long long
def HexLittleEndianToUnsignedDecimal(val:str)->int:
    if(len(val) == 1):
        return int(val.hex(),16)
    if(len(val) == 2):
        return struct.unpack('<H', val)[0]
    if(len(val) == 4):
        return struct.unpack('<L', val)[0]
    if(len(val) == 8):
        return struct.unpack('<Q', val)[0]

def HexLittleEndianToSignedDecimal(val:str)->int:
    if(len(val) == 1):
        return struct.unpack('<b', val)[0]
    if(len(val) == 2):
        return struct.unpack('<h', val)[0]
    if(len(val) == 4):
        return struct.unpack('<l', val)[0]
    if(len(val) == 8):
        return struct.unpack('<q', val)[0]

@dataclass
class BPBTable:
    def __init__(self, bytes_per_sector, sectors_per_cluster,
    sectors_per_track, numbers_of_heads, total_sectors, mft_cluster_number) -> None:
        self.__bytes_per_sector = bytes_per_sector
        self.__sectors_per_cluster = sectors_per_cluster
        self.__sectors_per_track = sectors_per_track
        self.__numbers_of_heads = numbers_of_heads
        self.__total_sectors = total_sectors
        self.__mft_cluster_number = mft_cluster_number

    def get_bytes_per_sector(self):
        return self.__bytes_per_sector

    def get_sectors_per_cluster(self):
        return self.__sectors_per_cluster

    def get_sectors_per_track(self):
        return self.__sectors_per_track
    
    def get_numbers_of_heads(self):
        return self.__numbers_of_heads
    
    def get_total_sectors(self):
        return self.__total_sectors

    def get_mft_cluster_number(self):
        return self.__mft_cluster_number

    bytes_per_sector = property(get_bytes_per_sector)
    sectors_per_cluster = property(get_sectors_per_cluster)
    sectors_per_track = property(get_sectors_per_track)
    numbers_of_heads = property(get_numbers_of_heads)
    total_sectors = property(get_total_sectors)
    mft_cluster_number = property(get_mft_cluster_number)

print(data[11:13])
count = 0
s = tmp.read(1024)
bpbtable = BPBTable(
    HexLittleEndianToUnsignedDecimal(s[11:13]),
    HexLittleEndianToUnsignedDecimal(s[13:14]),
    HexLittleEndianToUnsignedDecimal(s[24:26]),
    HexLittleEndianToUnsignedDecimal(s[26:28]),
    HexLittleEndianToUnsignedDecimal(s[40:48]),
    HexLittleEndianToUnsignedDecimal(s[48:48+8])
)
print(bpbtable.total_sectors)
print(bpbtable.mft_cluster_number)
print(bpbtable.bytes_per_sector)
a = bpbtable.sectors_per_cluster*bpbtable.mft_cluster_number*bpbtable.bytes_per_sector + 1024*26
print(a)
print(s[64:68])
i = a
tmp.seek(i)
skipped = 0
while True:
    s = tmp.read(1024)#should read from pbp
    if(s[0:4].hex() == "46494c45"):
        start = int(s[20:21].hex(),16)
        current = start
        while current < 1024:
            size_of_attribute = HexLittleEndianToUnsignedDecimal(s[current+4:current+7+1])
            size_of_attribute_content = HexLittleEndianToUnsignedDecimal(s[current+16:current+19+1])
            first_offset_of_content = HexLittleEndianToUnsignedDecimal(s[current+20:current+21])
            # start_of_content = first_offset_of_content
            if(HexLittleEndianToUnsignedDecimal(s[current:current+1]) == 48):
                filename = s[current+first_offset_of_content+66:current+first_offset_of_content+size_of_attribute_content+1]
                print(filename.decode("latin-1"))
            current = current + size_of_attribute
            if(size_of_attribute_content == 0):
                break
        # first_attribute = int(s[28:29].hex(),base = 16)
        # print(first_attribute)
        # print(count)
    else:
        skipped+=1
    if(i>=bpbtable.total_sectors*bpbtable.bytes_per_sector*0.5):
        break
    if(skipped >= 100):
        break
    i+=1024
    tmp.seek(i)