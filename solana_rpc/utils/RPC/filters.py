def create_memcmp_filter(offset, bytes_data, encoding="base58"):
    return {"memcmp": {"offset": offset, "bytes": bytes_data, "encoding": encoding}}

def create_datasize_filter(datasize):
    return {"dataSize": datasize}

def get_offset(layout, field_name):
    ''' For getting offset of a field from a layout(struct) '''
    offset = 0
    for subcon in layout.subcons:
        if subcon.name == field_name:
            return offset
        offset += subcon.sizeof()
    return -1  # Field not found