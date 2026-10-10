
import re

"""
Very stupid, but "Regulation H" -> "reg-h"
"""
def get_regulation_code(reg_name):
    if not re.match(r"Regulation [A-Z]-[A-Z]", reg_name):
        return reg_name

    return f"reg-{reg_name[-3:].lower()}"
