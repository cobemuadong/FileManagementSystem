from AttributeHeader import *


class Attribute:
    def __init__(self, header: AttributeHeader) -> None:
        self.header = header

class Attribute30(Attribute):
    def __init__(self, header, filename_length, filename) -> None:
        super().__init__(header)
        self.filename_length = filename_length
        self.filename = filename

class IndexEntry:
    def __init__(self, length_of_index_entry, length_of_stream, index_flags, 
    size_of_file, length_of_filename, filename, file_ref, parent_ref ) -> None:
        self.length_of_index_entry = length_of_index_entry
        self.length_of_stream = length_of_stream
        self.index_flags = index_flags
        self.size_of_file = size_of_file
        self.length_of_filename = length_of_filename
        self.filename = filename
        self.file_ref = file_ref
        self.parent_ref = parent_ref

class IndexRoot:
    def __init__(self, attribute_type, collation_rule, allocation_index_entry, 
    cluster_per_index_record) -> None:
        self.attribute_type = attribute_type
        self.collation_rule = collation_rule
        self.allocation_index_entry = allocation_index_entry
        self.cluster_per_index_record = cluster_per_index_record

class IndexHeader:
    def __init__(self, first_entry_offset, index_entries_size, allocated_size, has_subnode_flag) -> None:
        self.first_entry_offset = first_entry_offset
        self.index_entries_size = index_entries_size
        self.allocated_size = allocated_size
        self.has_subnode_flag = has_subnode_flag


class Attribute90(Attribute):
    def __init__(self, header,index_root: IndexRoot, index_header: IndexHeader, index_entries: list[IndexEntry]) -> None:
        super().__init__(header)
        self.index_entries = index_entries
        self.index_root = index_root
        self.index_header = index_header
    

class File:

    def __init__(self, filename: Attribute30, index: Attribute90) -> None:
        self.filename = filename
        self.index = index
    def printTree(self):
        print(self.filename.filename)
        if(self.index):
            for i in self.index.index_entries:
                print("-----", i.filename)