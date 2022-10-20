import sys 
import os
from FATInterface import *
from utils import *


class Shell:
    """ 
    Cai dat cac ham de duyet cay thu muc
    """

    def __init__(self):
        self.platform =  os.name
        if self.platform not in ['nt']: # Neu la HDH window NT
            raise AttributeError('Khong ho tro loai HDH nay. Chi ho tro Windows NT')
        # Xem thu muc hien tai l
        self.current_dir = None 
        # Lịch sử duyệt (FIFO)
        self.dir_hist = []

    def select_disk(self):
        print('-----------------CHON O DIA--------------------')
        print('NHAP CAC CHU CAI, VI DU: C, D, E, ...')
        disk_path = input('=> MOI NHAP: ')


        self.disk_path = '\\\\.\\' + disk_path + ':'

        print(self.disk_path)

    def create_fileobject(self):
        fd = os.open(self.disk_path, os.O_RDONLY | os.O_BINARY)
        return os.fdopen(fd, 'rb') # trả về 1 file_descriptor

    def initialize_root_directory(self, file_object):
        # Read boot sector
        bootsec_buffer = read_sector(file_object, 0, 1)
        fat32_signature = getNBytesAtBuffer(bootsec_buffer, 0x52, 8) # LOAI FAT

        if b'FAT32' in fat32_signature:
            self.disk = DISK(file_object)
            print('FAT32 da duoc tim thay')


        else: 
            raise AttributeError('Filesystem not supported')

        self.disk.root_directory.build_tree()
        self.current_dir = self.disk.root_directory


    def list_table(self):
        """
        Hàm để tạo ra một bảng thống kê tập tin
        """
        entry_info_list = []
        max_width = dict()

        def max_width_of_each_col(key, value):
            """ 
            Tìm kích thước lớn nhất của mỗi attribute để in bảng cho đẹp
            """    
            if key not in max_width:
                max_width[key] = len(str(value)) + 4
            elif max_width[key] < len(str(value)): 
                max_width[key] = len(str(value)) + 4

        for entry in self.current_dir.subentries:
            entry_info = {
                'name': entry.name, 
                'size': 0 if isinstance(entry, DIRECTORY) else entry.size, 
                'attr': entry.info_attr(),
                'sector': '' if len(entry.sectors) == 0 else entry.sectors[0]
            }

            
            if entry_info['name'] in ('.', '..'):
                continue
            
            entry_info_list.append(entry_info)

            # Cập nhật độ rộng của mỗi cột thuộc tính để in ra cho đẹp mắt
            max_width_of_each_col('name', entry_info['name'])
            max_width_of_each_col('attr', entry_info['attr'])
            max_width_of_each_col('sector', entry_info['sector'])

            # Nếu entry là file
            if isinstance(entry, FILE): 
                max_width_of_each_col('size', entry.size)
            else:
                max_width_of_each_col('size', 5)
        
        
        format_str = '{0: <%d} {1: <%d} {2: <%d} {3: <%d}\n' % (
            max_width['name'], max_width['size'], max_width['attr'], max_width['sector'])

        print_str = ''
        print_str += format_str.format('name', 'size', 'attr', 'sector') 

        for entry in entry_info_list:
            if entry['attr'] == "DHS":
                continue
            print_str += format_str.format(entry['name'], entry['size'], entry['attr'], entry['sector'])

        return print_str
    
    def list(self):
        """
        Liệt kê thư mục gốc
        """
        assert self.current_dir != None, 'Thu muc hien tai dang trong\n'
        self.current_dir.build_tree()

        table = self.list_table()
        print(table)
    
    def history_list(self):
        """
        Handler funciton for 'history list'
        """
        if len(self.dir_hist) == 0:
            print('History is empty')
            return 

        for entry in self.dir_hist:
            print(entry.name)

    def goto_subdir(self, subdir_name):
        """
        Handler function for 'cd'
        """
        for entry in self.current_dir.subentries: 
            if entry.name == subdir_name:
                if isinstance(entry, FILE):
                    print('Cannot cd into a file!')
                else:
                    self.dir_hist.append(self.current_dir)
                    self.current_dir = entry 
                    return
        print('Bad command or filename:', subdir_name)
        
    def history_go_back(self):
        if len(self.dir_hist) == 0:
            print('History trong')
            return 

        last_entry = self.dir_hist[-1]
        self.dir_hist.pop()
        self.current_dir = last_entry

    def help(self):
        print(
        '- ls: Liet ke cac file/folder hien tai.\n' +
        '- cd <dir>: di chuyen vao thu muc <dir>.\n' +
        '- history list: Liet ke cac thu muc cha.\n' +
        '- back: Tro lai thu muc cha.\n' +
        '- cat <text file>: hien thi noi dung tap tin.\n' +
        '- exit: Thoat\n' +
        '\n')


    def read_text_file(self, filename):
        assert filename != None, 'Khong ton tai file nay.'

        for file in self.current_dir.subentries:
            if file.name == filename:
                binary_data: bytes = file.dump_binary_data()
                string_data = binary_data.decode('utf8')
                print('\n', string_data, '\n')
                return 
        raise FileNotFoundError('Khong ton tai file nay' )

    def start_shell(self):
        if self.current_dir == None: 
            return
        
        print('Nhap lenh: help, de duoc ho tro.')
        while True: 
            try:
                input_string = input('%s> ' % self.current_dir.name)
                  
                input_list = input_string.split(' ', 1)
                if (len(input_list)) == 0:
                    return

                input_first = input_list[0]
                if len(input_list) == 1:
                    input_second = None 
                else: 
                    input_second = input_list[1]
                
                # Cac lenh thao tac voi Shell
                if input_first == 'help':
                    self.help()
                elif input_first == 'ls':
                    self.list()
                elif input_first == 'cd':
                    self.goto_subdir(input_second)
                elif input_first == 'history':
                    if input_second == 'list':
                        self.history_list()
                    else:
                        print('Khong ho tro lenh nay. Go lenh: help.')
                elif input_first == 'cat':
                    file_extension = input_second.split('.')[1]
                    if file_extension == 'txt':
                        self.read_text_file(input_second)
                    else:
                        print("Can only read '.txt' files,")
                        if(file_extension == 'mp3' or file_extension =='mp4'):
                            print("Use Media Player to open this file")
                        elif(file_extension == 'doc' or file_extension =='docx'):
                            print("Use Word to open this file")
                        elif(file_extension == 'pptx'):
                            print("Use Power Point to open this file")
                        elif(file_extension == 'jpg' or file_extension == 'png'):
                            print("Use Photos to open this file")
                        else:
                            print("try using other application to read this file")

                elif input_first == 'back':
                    self.history_go_back()
                elif input_first == 'exit':
                    return
                else: 
                    print('Khong ton tai lenh nay: %s. Go lenh: help.' % input_first)
            except Exception as e:
                print('ERROR:', e)
                    