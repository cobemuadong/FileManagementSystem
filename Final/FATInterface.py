from utils import *

class DISK():
    def __init__(self, file_object):
        """
        Constructor nhận vào 1 tham số là `file_object` python.
        file_object đã chứa dữ liệu, phân tích file này, sau đó
        gán cho các thông số của FAT32.
        
        """
        self.file_object = file_object

        # Đọc boot sector
        bootsec_buffer = read_sector(self.file_object, 0, 1) # đọc sector thứ 0 (sector đầu tiên) và đọc 1 sector

        # Đọc magic number 0xAA55
        signature = getNBytesAtBufferAndReturnDec(bootsec_buffer, 0x1FE, 2)
        assert signature == 0xAA55, "Invalid boot sector: 0xAA55 not found at offset 0x1FA"

        # Số byte/sector
        self.bps = getNBytesAtBufferAndReturnDec(bootsec_buffer, 0xB, 2)
       
        # Đọc Sc (số sector cho 1 cluster)
        self.sc = getNBytesAtBufferAndReturnDec(bootsec_buffer, 0x0D, 1)
        
        # Đọc Sb - số sector để dành trước bảng FAT
        self.sb = getNBytesAtBufferAndReturnDec(bootsec_buffer, 0x0E, 2)
        
        # Đọc Nf - số bảng FAT
        self.nf = getNBytesAtBufferAndReturnDec(bootsec_buffer, 0x10, 1)
        
        # Đọc Sf - số sector cho 1 bảng FAT
        self.sf = getNBytesAtBufferAndReturnDec(bootsec_buffer, 0x24, 4)
        
        # Cluster bắt đầu của RDET
        self.root_cluster = getNBytesAtBufferAndReturnDec(bootsec_buffer, 0x2C, 4)
        
        # Chỉ số sector bắt đầu của data 
        self.begin_sector_of_data = self.sb + self.nf * self.sf

        print('-----------THONG TIN O DIA------------------')
        print('- Bytes/sector:                  :', self.bps)
        print('- Sector/cluster (Sc)            :', self.sc)
        print('- Kich thuoc vung BootSector (Sb):', self.sb)
        print('- So luong bang FAT (Nf)         :', self.nf)
        print('- Kich thuoc bang 1 bang FAT (Sf):', self.sf)
        print('- Cluster bat dau cua RDET       :', self.root_cluster)
        print('- Sector bat dau o vung DATA     :', self.begin_sector_of_data)
        print('\n')

        # Đọc bảng FAT (sf byte tại offset sb)
        self.fat_table_buffer = read_sector(self.file_object, self.sb, self.sf, self.bps)

        # RDET buffer
        # Từ cluster bắt đầu của RDET(root_cluster) --> dò bảng FAT để tìm ra các cluster 
        list_of_rdet_cluster = self.get_cluster_list_from_fat_table(self.root_cluster)
        # Từ danh sách cluster đó, đổi thành danh sách các sector tương ứng
        list_of_rdet_sector = self.cluster_list_to_sector_list(list_of_rdet_cluster)
        # Đổi danh sách các sector của RDET về danh sách byte.
        rdet_buffer = sector_list_return_bytes_list(self.file_object, list_of_rdet_sector, self.bps)
        self.root_directory = DIRECTORY(rdet_buffer, '', self, isrdet=True)
       
    def get_cluster_list_from_fat_table(self, n) -> list: 
        """
        Hàm dò bảng FAT để tìm ra dãy các cluster cho một entry nhất định,
        bắt đầu từ cluster thứ `n` truyền vào.
        """
        # End-of-cluster sign
        eoc_sign = [0x00000000, 0XFFFFFF7, 0xFFFFFF8, 0xFFFFFFF0, 0xFFFFFF0, 0xFFFFFFF]
        if n in eoc_sign:
            return []
        
        next_cluster = n
        list = [next_cluster]

        while True:
            next_cluster = getNBytesAtBufferAndReturnDec(self.fat_table_buffer, next_cluster * 4, 4)
            if next_cluster in eoc_sign:
                break 
            else:
                list.append(next_cluster)
        return list 
        
    def cluster_list_to_sector_list(self, cluster_list) -> list: 
        """
        Hàm chuyển dãy các cluster sang dãy các sector
        Biết rằng 1 cluster có Sc sectors 
        """
        sector_list = []
        
        for cluster in cluster_list:
            begin_sector = self.begin_sector_of_data + (cluster - 2) * self.sc
            for sector in range(begin_sector, begin_sector + self.sc):
                sector_list.append(sector)
        return sector_list

    def joinLongFileNameFromSubentries(subentries: list):
        name = b''
        for subentry in subentries:
            name += getNBytesAtBuffer(subentry, 1, 10)
            name += getNBytesAtBuffer(subentry, 0xE, 12)
            name += getNBytesAtBuffer(subentry, 0x1C, 4)
        name = name.decode('utf-16le', errors='ignore')

        if name.find('\x00') > 0:
            name = name[:name.find('\x00')]
        return name

class DIRECTORY():
    def __init__(self, total_rdet_buffer: bytes, parent_path: str, disk: DISK, isrdet=False, longfilename_entries=[]):
        # Dãy byte rdet_entry
        self.entry_buffer = total_rdet_buffer
        self.disk = disk # con trỏ đến disk đang chứa thư mục này
        # Danh sách các subentry
        self.subentries = None
        # Nếu KHONG la RDET
        if not isrdet:
            # Tên entry 
            if len(longfilename_entries) > 0:
                longfilename_entries.reverse()
                self.name = DISK.joinLongFileNameFromSubentries(longfilename_entries)
                longfilename_entries.clear()
            else:
                self.name = getNBytesAtBuffer(total_rdet_buffer, 0, 11).decode('utf-8', errors='ignore').strip()
            # Status
            self.attr = getNBytesAtBufferAndReturnDec(total_rdet_buffer, 0xB, 1)

            # Các byte thấp và cao của chỉ số cluster đầu
            highbytes = getNBytesAtBufferAndReturnDec(total_rdet_buffer, 0x14, 2)
            lowbytes = getNBytesAtBufferAndReturnDec(total_rdet_buffer, 0x1A, 2)
            self.begin_cluster = highbytes * 0x100 + lowbytes
            self.path = parent_path + '/' + self.name
        else:
            self.name = getNBytesAtBuffer(total_rdet_buffer, 0, 11).decode('utf-8', errors='ignore').strip()
            self.begin_cluster = self.disk.root_cluster
            self.path = ''

        cluster_list = self.disk.get_cluster_list_from_fat_table(self.begin_cluster)
        self.sectors = self.disk.cluster_list_to_sector_list(cluster_list)
            

    def build_tree(self):
        # Cây đã được tạo rồi thì không tạo nữa, ta return.
        if self.subentries != None: 
            return 
        self.subentries = []
        subentry_index = 0

        # Đọc SDET (dữ liệu nhị phân) của thư mục (Hay RDET của thư mục hiện tại)
        sdet_buffer = sector_list_return_bytes_list(self.disk.file_object, self.sectors, self.disk.bps)
        longfilename_entries_queue = []

        while True:
            subentry_buffer = getNBytesAtBuffer(sdet_buffer, subentry_index, 32)
            # Loai entry
            entry_type = getNBytesAtBufferAndReturnDec(subentry_buffer, 0xB, 1)

            deleted = getNBytesAtBufferAndReturnDec(subentry_buffer,0x00, 1)
            if deleted & 0xe5 == 0xe5:
                subentry_index += 32
                continue

            # if entry_type & 0x02 == 0x02:
            #     subentry_index += 32
            #     continue

            # Entry la thư mục
            if entry_type & 0x10 == 0x10: 
                self.subentries.append(DIRECTORY(subentry_buffer, self.path, self.disk, longfilename_entries=longfilename_entries_queue))

            # Entry là tập tin (archive)
            elif entry_type & 0x20 == 0x20:
                self.subentries.append(FILE(subentry_buffer, self.path, self.disk, longfilename_entries=longfilename_entries_queue))
            # Entry phu
            elif entry_type & 0x0F == 0x0F: 
                longfilename_entries_queue.append(subentry_buffer)
            if entry_type == 0:
                break
            # Đọc tiếp entry khác. Mỗi entry có kích thước 32 byte
            subentry_index += 32

    def info_attr(self):
        """ 
        File attribute cua RDET
        """
        file_attr_table = {
            0x10: 'D',
            0x20: 'A',
            0x01: 'R', 
            0x02: 'H',
            0x04: 'S',
        }

        desc_str = ''
        for attr in file_attr_table:
            if self.attr & attr == attr:
                desc_str += file_attr_table[attr]
        
        return desc_str

class FILE():
    def __init__(self, main_entry_buffer: bytes, parent_path: str, disk: DISK, longfilename_entries=[]):
        
        self.entry_buffer = main_entry_buffer
        self.disk = disk

        # Thuộc tính trạng thái
        self.attr = getNBytesAtBufferAndReturnDec(main_entry_buffer, 0xB, 1)

        # Tên entry 
        if len(longfilename_entries) > 0:
            longfilename_entries.reverse()
            self.name = DISK.joinLongFileNameFromSubentries(longfilename_entries)
            longfilename_entries.clear()
        else:
            name_base = getNBytesAtBuffer(main_entry_buffer, 0, 8).decode('utf-8', errors='ignore').strip()
            name_ext = getNBytesAtBuffer(main_entry_buffer, 8, 3).decode('utf-8', errors='ignore').strip()
            self.name = name_base + '.' + name_ext

        
        # Phần Word(2 byte) cao
        highbytes = getNBytesAtBufferAndReturnDec(main_entry_buffer, 0x14, 2)
        # Phần Word (2 byte) thấp
        lowbytes = getNBytesAtBufferAndReturnDec(main_entry_buffer, 0x1A, 2)

        # Cluster bắt đầu
        self.begin_cluster = highbytes * 0x100 + lowbytes

        # Đường dẫn tập tin
        self.path = parent_path + '/' + self.name

        cluster_list = self.disk.get_cluster_list_from_fat_table(self.begin_cluster)
        self.sectors = self.disk.cluster_list_to_sector_list(cluster_list)

        # Kích thước tập tin
        self.size = getNBytesAtBufferAndReturnDec(main_entry_buffer,0x1C,4)
    
    def dump_binary_data(self):
        """
        Trả về mảng các byte của tập tin
        """
        binary_data = sector_list_return_bytes_list(self.disk.file_object, self.sectors, self.disk.bps)
        # Dua ve dung kich thuoc
        return binary_data[:self.size]
    
    def info_attr(self):
        """ 
        File attribute cua RDET
        """
        file_attr_table = {
            0x10: 'D',
            0x20: 'A',
            0x01: 'R', 
            0x02: 'H',
            0x04: 'S',
        }

        desc_str = ''
        for attr in file_attr_table:
            if self.attr & attr == attr:
                desc_str += file_attr_table[attr]

        return desc_str