def is_number(token: str) -> bool:
    try:
        float(token)
        return True
    except ValueError:
        return False
