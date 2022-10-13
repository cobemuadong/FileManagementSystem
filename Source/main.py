import os
import struct

disk_fd = os.open(r'\\.\E:',os.O_RDONLY|os.O_BINARY)
data = os.read(disk_fd,512)
tmp = os.fdopen(disk_fd,'rb')
i = 1024
#tmp.seek(i)
tmp.seek(357951488)

def HexLittleEndianToDecimal(val:str)->int:
    if(len(val) == 1):
        return int(val.hex(),16)
    hex_string = hex(struct.unpack('<I', struct.pack('>I', int(val.hex(), 16)))[0])
    return int(hex_string,16)

count = 0
while True:
    s = tmp.read(1024)
    if(s[0:4].hex() == "46494c45"):
        start = int(s[20:21].hex(),16)
        current = start
        while current < 1024:
            size_of_attribute_content = HexLittleEndianToDecimal(s[current+16:current+19+1])
            first_offset_of_content = HexLittleEndianToDecimal(s[current+20:current+21])
            # start_of_content = first_offset_of_content
            if(HexLittleEndianToDecimal(s[current:current+1]) == 48):
                filename = s[current+first_offset_of_content+66:current+first_offset_of_content+74]
                print(filename.decode("latin-1"))
            current = current + size_of_attribute_content + first_offset_of_content
            if(size_of_attribute_content == 0):
                break
        # first_attribute = int(s[28:29].hex(),base = 16)
        # print(first_attribute) 
        # print(count)
    if(s == ""):
        break
    i+=1024
    tmp.seek(i)