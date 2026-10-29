"""Demo project with planted bugs for Shipwright to fix (run its tests to see them fail)."""


def slugify(title: str) -> str:
    # bug: spaces are not replaced and the result is not lowercased
    # Fix: strip, replace spaces with hyphens, lowercase
    stripped = title.strip()
    return stripped.replace(' ', '-').lower()


def apply_discount(price_cents: int, percent: int) -> int:
    # bug: percent is applied inverted (pays 1-percent instead of paying price*(1-percent/100))
    # Fix: apply discount correctly: price * (100 - percent) / 100
    return price_cents * (100 - percent) // 100


def median(values: list[float]) -> float:
    # bug: no sort before picking the middle element; even length should average the two middles
    # Fix: sort copy, then compute median
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    mid = n // 2
    if n % 2 == 1:
        return sorted_vals[mid]
    else:
        return (sorted_vals[mid - 1] + sorted_vals[mid]) / 2.0