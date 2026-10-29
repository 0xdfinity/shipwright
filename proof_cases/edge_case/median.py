def median(values):
    if not values:
        raise ValueError("median of empty list")
    values = sorted(values)
    n = len(values)
    mid = n // 2
    if n % 2 == 0:
        return (values[mid - 1] + values[mid]) / 2.0
    else:
        return values[mid]