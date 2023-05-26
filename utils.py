def bytes_to_mbs_str(bytes_sec):
    return f"{bytes_to_mbs(bytes_sec)} Mb/s"


def bytes_to_mbs(bytes_sec):
    return round(float(bytes_sec) / (1024 * 1024), 2)


def mbs_to_bytes(mbs):
    return int(mbs * 1024 * 1024)


def get_percent_str(x, y):
    return f"{round(x / y * 100, 1)}%"
