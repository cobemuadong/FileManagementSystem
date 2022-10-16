import os
disk_fd = os.open(r'\\.\E:', os.O_RDONLY | os.O_BINARY)
# data = os.read(disk_fd,512)
tmp = os.fdopen(disk_fd, 'rb')
i = 1024
# tmp.seek(i)
tmp.seek(357953536)