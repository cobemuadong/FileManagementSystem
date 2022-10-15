from dataclasses import dataclass
@dataclass
class PartitionBootSector:
    def __init__(self, bytes_per_sector, sectors_per_cluster, reserved_sectors, media_descriptor,
    sectors_per_track, numbers_of_heads, hidden_sectors , total_sectors, mft_cluster_number, 
    mftmirr_cluster_number, bytes_per_file_record_segment, cluster_per_index, volume_serial_number
    ) -> None:
        self.__bytes_per_sector = bytes_per_sector
        self.__sectors_per_cluster = sectors_per_cluster
        self.__reserved_sectors = reserved_sectors
        self.__media_descriptor = media_descriptor
        self.__sectors_per_track = sectors_per_track
        self.__numbers_of_heads = numbers_of_heads
        self.__hidden_sectors = hidden_sectors
        self.__total_sectors = total_sectors
        self.__mft_cluster_number = mft_cluster_number
        self.__mftmirr_cluster_number = mftmirr_cluster_number
        self.__bytes_per_file_record_segment = bytes_per_file_record_segment
        self.__cluster_per_index = cluster_per_index
        self.__volume_serial_number = volume_serial_number

    def get_bytes_per_sector(self):
        return self.__bytes_per_sector

    def get_sectors_per_cluster(self):
        return self.__sectors_per_cluster

    def get_reserved_sectors(self):
        return self.__reserved_sectors

    def get_media_descriptor(self):
        return self.__media_descriptor

    def get_sectors_per_track(self):
        return self.__sectors_per_track
    
    def get_numbers_of_heads(self):
        return self.__numbers_of_heads

    def get_hidden_sector(self):
        return self.__hidden_sectors
    
    def get_total_sectors(self):
        return self.__total_sectors

    def get_mft_cluster_number(self):
        return self.__mft_cluster_number

    def get_mftmirr_cluster_number(self):
        return self.__mft_cluster_number

    def get_mftmirr_cluster_number(self):
        return self.__mftmirr_cluster_number
    
    def get_bytes_per_file_record_segment(self):
        return self.__bytes_per_file_record_segment

    def get_cluster_per_index(self):
        return self.__cluster_per_index

    def get_volume_serial_number(self):
        return self.__volume_serial_number

    bytes_per_sector = property(get_bytes_per_sector)
    sectors_per_cluster = property(get_sectors_per_cluster)
    reserved_sectors = property(get_reserved_sectors)
    media_descriptor = property(get_media_descriptor)
    sectors_per_track = property(get_sectors_per_track)
    numbers_of_heads = property(get_numbers_of_heads)
    total_sectors = property(get_total_sectors)
    mft_cluster_number = property(get_mft_cluster_number)
    mftmirr_cluster_number = property(get_mftmirr_cluster_number)
    bytes_per_file_record_segment = property(get_bytes_per_file_record_segment)

    def printVolumeInformation(self):
        print('----------Volume information---------')
        print('Bytes per sector: ', self.bytes_per_sector)
        print('Sectors per cluster (Sc): ', self.sectors_per_cluster)
        print('Reserved sectors (Sb): ', self.reserved_sectors)
        print('Media Descriptor: ', self.media_descriptor)
        print('Sector per track: ', self.sectors_per_track)
        print('Number of heads: ', self.numbers_of_heads)
        print('Hidden Sectors: ',self.__hidden_sectors)
        print('Total sectors: ',self.total_sectors)
        print('MFT begin sector: ',self.mft_cluster_number)
        print('MFT Mirror begin sector: ', self.mftmirr_cluster_number)
        print('Bytes per File Record Segment: ', self.bytes_per_file_record_segment)
        print('Cluster per Index: ', self.__cluster_per_index)
        print('Volume serial number: ', self.__volume_serial_number)
        print('-------------------------------------')
