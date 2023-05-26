# File: asf_welsh_energy_consultation/utils/formatting.py
"""
Formatting utility functions.
"""

import re


def format_number(n):
    """
    If number is 5 or more digits, add a comma every 3 digits from the right.

    Args:
        n (int): Number to format.

    Returns:
        str: Formatted number.
    """
    if n > 9999:
        return re.sub(r"(\d)(?=(\d{3})+(?!\d))", r"\1,", str(n))
    else:
        return str(n)
