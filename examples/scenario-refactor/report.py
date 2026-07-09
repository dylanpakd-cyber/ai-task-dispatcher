def line_item(name, cents):
    dollars = cents // 100
    remainder = cents % 100
    return f"{name}: ${dollars}.{remainder:02d}"


def total_line(items):
    cents = sum(c for _, c in items)
    dollars = cents // 100
    remainder = cents % 100
    return f"TOTAL: ${dollars}.{remainder:02d}"
