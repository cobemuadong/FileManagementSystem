from NTFS import *

a = NTFS("\\\\.\\F:")

tmp = a.mft_id_list


for i in tmp:
    print("ID:", i.this_id, "----- Parent ID:", i.parent_id, "----- Sector:", i.sector)
    print("Children: ", i.children_id)