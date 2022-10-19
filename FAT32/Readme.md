## Đồ Án 1: ĐỌC THÔNG TIN FAT32/NTFS 

### FAT32
#### Mã nguồn:
- Gồm 4 file: FATInterface.py, Shell.py, utils.py và main.py
  - FATInterface.py: Cài đặt các class: DISK, DIRECTORY và FILE
    - DISK: Đọc thông tin vùng boot sector từ file_object, đọc tổng số byte của bảng FAT, tổng số byte của bảng RDET. Từ tổng số byte của RDET, gọi class DIRECTORY truyền tổng số byte đó vào để xây dựng cây thư mục gốc
    - DIRECTORY: Nhận vào tổng số byte vùng RDET do class DISK đọc được, phân tích các thông tin của thư mục gốc. Sau đó, xây cây thư mục gốc
    - FILE: đọc và phân tích thông tin file
  - Shell.py: Giả lập shell của window để duyệt cây thư mục
  - utils.py: các hàm cần thiết hỗ trợ cho việc cài đặt 3 class 
  - main.py : Gọi và chạy chương trình
#### Qui trình đọc FAT:
- Sau khi chọn ổ đĩa cần đọc, đọc file nhị phân tại đường dẫn, dẫn tới ổ đĩa đó. Sau đó trả về 1 file_descriptor (1 file object chứa toàn bộ bytes của ổ đĩa. Từ đó ta sẽ phân tích trên file_descriptor này)
- Đọc ổ đĩa(class DISK):
  - Đọc thông tin vùng BOOTSECTOR: Sc, Sb, Nf, Sf,...
  - Đọc cluster bắt đầu của RDET
  - Đọc tổng số byte của 1 bảng FAT
  - Đọc tổng số byte của RDET --> Khởi tạo cây thư mục gốc(từ class DIRECTORY)
  - get_cluster_list_from_fat_table(): Dùng danh sách cluster dò trên bảng FAT trả về số bytes tương ứng.
  - joinLongFileNameFromSubentries(): nối các entry tên dài
- Đọc thông tin DIRECTORY:
  - build_tree(): hàm để dựng được danh sách các subentry tương ứng với thư mục này (dữ liệu là từ SDET/RDET của thư mục). Danh sách này lưu vào mảng subentries[].
  - info_attr(): Các thuộc tính của file/dir trong thư mục gốc
- Đọc thông tin FILE:
  - dump_binary_data(): Trả về mảng các byte của tập tin.
  - info_attr(): Thuộc tính của file
### Tài liệu tham khảo:
- http://www.tavi.co.uk/phobos/fat.html
- https://en.wikipedia.org/wiki/Design_of_the_FAT_file_system
- https://wiki.osdev.org/FAT
- Giải đáp thắc mắc project 1