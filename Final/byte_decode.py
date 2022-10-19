'''
module lưu những hàm để xử lý dữ liệu binary/hexadecimal
'''

def to_dec_le(val: bytes):
    """
    Trả về giá trị hệ 10 theo little endian
    """
    result:int = 0
    for i in reversed(val):
        result = result * 16 * 16 + i
    return result

def parse_datarun(val: bytes):
    size_byte = int(val.hex()[0])

    digit_1 = int(val.hex()[0])
    digit_2 = int(val.hex()[1])

    cluster_count_byte = to_dec_le(val[1:1+digit_2])
    first_cluster = to_dec_le(val[1+digit_2:1+digit_2+digit_1])

    return (size_byte, cluster_count_byte, first_cluster)


def parse_datarun2(string: str):
    data_run = []
    current = 0
    temp = 0
    while(current < len(string)):
        if(string[current]==0):
            break
        digit_1 = int(string.hex()[current*2])
        digit_2 = int(string.hex()[current*2+1])
        cluster_count_byte = to_dec_le(string[1+current:1+current+digit_2])
        first_cluster = to_dec_le(string[1+current+digit_2:1+current+digit_2+digit_1]) + temp
        temp = first_cluster
        current+=digit_1+digit_2+1
        data_run.append([cluster_count_byte,first_cluster])

    return data_run

