def to_hex(val):
    '''Return val as str of hex values concatenated by colons.'''
    if type(val) is int:
        return hex(val)
    try:
        # Python-2.x
        if type(val) is long:
            return hex(val)
    except NameError:
        pass
    # else:
    try:
        # Python-2.x
        return ":".join("{0:02x}".format(ord(char)) for char in val)
    except TypeError:
        # Python-3.x
        return ":".join("{0:02x}".format(char) for char in val)
