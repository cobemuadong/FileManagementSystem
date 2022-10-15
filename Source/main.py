from PartitionBootSector import *
import os
import struct

disk_fd = os.open(r'\\.\E:',os.O_RDONLY|os.O_BINARY)
# data = os.read(disk_fd,512)
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


count = 0
s = tmp.read(1024)
pbstable = PartitionBootSector(
    bytes_per_sector = HexLittleEndianToUnsignedDecimal(s[11:11+2]),
    sectors_per_cluster = HexLittleEndianToUnsignedDecimal(s[13:13+1]),
    reserved_sectors = HexLittleEndianToUnsignedDecimal(s[14:14+2]),
    media_descriptor = s[21:21+1].hex(),
    sectors_per_track = HexLittleEndianToUnsignedDecimal(s[24:24+2]),
    numbers_of_heads = HexLittleEndianToUnsignedDecimal(s[26:26+2]),
    hidden_sectors = HexLittleEndianToUnsignedDecimal(s[28:28+4]),
    total_sectors = HexLittleEndianToUnsignedDecimal(s[40:40+8]),
    mft_cluster_number = HexLittleEndianToUnsignedDecimal(s[48:48+8]), 
    mftmirr_cluster_number = HexLittleEndianToUnsignedDecimal(s[56:56+8]),
    bytes_per_file_record_segment = 2**abs(HexLittleEndianToSignedDecimal(s[64:64+1])),
    cluster_per_index = HexLittleEndianToUnsignedDecimal(s[68:68+4]),
    volume_serial_number = s[72:72+8].hex()
)

pbstable.printVolumeInformation()

a = pbstable.sectors_per_cluster*pbstable.mft_cluster_number*pbstable.bytes_per_sector + 1024*26
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
            if(HexLittleEndianToUnsignedDecimal(s[current:current+1]) == 48):
                filename = s[current+first_offset_of_content+66:current+first_offset_of_content+size_of_attribute_content]
                print(filename.decode("utf-16le"))
            current = current + size_of_attribute
            if(size_of_attribute_content == 0):
                break
    else:
        skipped+=1
    if(i>=pbstable.total_sectors*pbstable.bytes_per_sector*0.5):
        break
    if(skipped >= 100):
        break
    i+=1024
    tmp.seek(i)
