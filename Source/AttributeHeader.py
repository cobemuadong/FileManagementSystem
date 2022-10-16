class AttributeHeader:
    def __init__(self, type, length, resident_flag, name_length, name_offset, flags, 
    attribute_id, length_of_attribute, offset_to_attribute, indexed_flag) -> None:
        self.type = type
        self.length = length
        self.resident_flag = resident_flag
        self.name_length = name_length
        self.name_offset = name_offset
        self.flags = flags
        self.attribute_id = attribute_id
        self.length_of_attribute = length_of_attribute
        self.offset_to_attribute = offset_to_attribute
        self.indexed_flag = indexed_flag

