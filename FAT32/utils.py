
def Hex2Dec(str) -> int:
    return int(str, 16)

def read_sector(file, sector_begin, size = 1, bps = 512)-> bytes:
    """
    Hàm trả về tổng số byte của n sector, bắt đầu tại sector_begin. Đọc size*bps byte
    """
    file.seek(sector_begin*bps)
    return file.read(size*bps)

def getNBytesAtBuffer(buffer, offset, size)-> bytes:
    """ 
    Trong buffer, thì dữ liệu là byte
    Lấy n bytes ra tại địa chỉ offset trong buffer
    """
    return buffer[offset:offset+size]

def getNBytesAtBufferAndReturnDec(buffer, offset, size) -> int:
    """
    Byte --> Hex ---> Dec
    """
    found_data = getNBytesAtBuffer(buffer, offset, size)
    """
    - Xử lý little endian: buffer[::-1]
    - convert byte sang hex: buffer[::-1].hex()
    - dec(): hàm chuyển hex to dec đã được cài đặt ở trên
    """ 
    return Hex2Dec(found_data[::-1].hex())

def sector_list_return_bytes_list(file_object, sector_list, bps = 512):
    """ 
    Đọc 1 dãy sector từ mảng sector_list 
    Trả về: Một dãy byte tương ứng với dãy sector
    """
    buffer = b''
    for sector in sector_list: 
        buffer += read_sector(file_object, sector, 1, bps)
    return buffer

