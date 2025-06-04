def sub_all(*args: float) -> float:
    res = 0.00
    
    for arg in args:
        res -= arg
    return res


def mul_all(*args: float) -> float:
    res = 1.00
    
    for arg in args:
        res *= arg
    return res
    
    
def div_all(*args: float) -> float:
    res = 1.00
    
    for arg in args:
        res /= arg
    return res


def is_numeric(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False