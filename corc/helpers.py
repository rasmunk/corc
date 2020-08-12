def is_in(a_values, b_struct):
    num_positives = 0
    a_len = len(a_values.keys())
    for k, v in a_values.items():
        if isinstance(b_struct, dict):
            if k in b_struct and b_struct[k] == v:
                num_positives += 1
        elif isinstance(b_struct, (list, set, tuple)):
            for b in b_struct:
                if b == v:
                    num_positives += 1
        else:
            if hasattr(b_struct, k):
                if getattr(b_struct, k) == v:
                    num_positives += 1
    if num_positives == a_len:
        return True
    return False


def exists_in_list(a_values, list_of_structs):
    for struct in list_of_structs:
        if is_in(a_values, struct):
            return True
    return False


def find_in_list(a_values, list_of_structs):
    for struct in list_of_structs:
        if is_in(a_values, struct):
            return struct
    return None


def exists_in_dict(a_values, dict_of_structs):
    for k, struct in dict_of_structs.items():
        if is_in(a_values, struct):
            return struct
    return None


def find_in_dict(a_values, dict_of_structs):
    for k, struct in dict_of_structs.items():
        if is_in(a_values, struct):
            return struct
    return None


def unset_check(value):
    if isinstance(value, str) and value == "":
        return True
    if isinstance(value, (bytes, bytearray)) and value == bytearray():
        return True
    if isinstance(value, list) and value == []:
        return True
    if isinstance(value, set) and value == set():
        return True
    if isinstance(value, tuple) and value == tuple():
        return True
    if isinstance(value, dict) and value == {}:
        return True
    if value is None:
        return True
    return False
