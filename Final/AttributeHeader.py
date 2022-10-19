from byte_decode import to_dec_le


class AttributeHeader:
    def __init__(self,length, resident_flag) -> None:
        self.length = length
        self.resident_flag = resident_flag

class ResidentAttributeHeader(AttributeHeader):
    def __init__(self, length, resident_flag, length_of_attribute, offset_to_attribute) -> None:
        super().__init__(length, resident_flag)
        self.length_of_attribute = length_of_attribute
        self.offset_to_attribute = offset_to_attribute


class NonResidentAttributeHeader(AttributeHeader):
    def __init__(self, length, resident_flag, run_offset, real_size,
    allocated_size) -> None:
        super().__init__(length, resident_flag)
        self.run_offset = run_offset
        self.real_size = real_size
        self.allocated_size = allocated_size


def ReadAttributeHeader(string: bytes, current: int):
    if (string[current+8] > 0):
        return NonResidentAttributeHeader(
            length=to_dec_le(
                string[current+4:current+8]),
            resident_flag=string[current+8],
            run_offset=to_dec_le(
                string[current+32:current+34]),
            real_size=to_dec_le(
                string[current+48:current+48+8]),
            allocated_size=to_dec_le(string[current+40:current+40+8]))
    else:
        return ResidentAttributeHeader(
            length=to_dec_le(
                string[current+4:current+8]),
            resident_flag=string[current+8],
            length_of_attribute=to_dec_le(
                string[current+16:current+20]),
            offset_to_attribute=to_dec_le(
                string[current+20:current+22]))