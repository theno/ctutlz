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


# http://stackoverflow.com/a/16891418
def string_without_prefix(prefix ,string):
    '''Return string without prefix.  If string does not start with prefix,
    return string.
    '''
    if string.startswith(prefix):
        return string[len(prefix):]
    return string


def string_with_prefix(prefix, string):
    '''Return string with prefix prepended.  If string already starts with
    prefix, return string.
    '''
    return str(prefix) + string_without_prefix(str(prefix), str(string))
