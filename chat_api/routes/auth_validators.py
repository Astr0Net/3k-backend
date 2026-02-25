import re

USERNAME_MIN = 3
USERNAME_MAX = 32
PASSWORD_MIN = 8
PASSWORD_MAX = 128

_username_re = re.compile(r"^[a-z0-9._-]+$")


def validate_username(username: str):
    if not username:
        return "username is required"
    if not (USERNAME_MIN <= len(username) <= USERNAME_MAX):
        return f"username length must be {USERNAME_MIN}-{USERNAME_MAX}"
    if not _username_re.match(username):
        return "username contains invalid characters"
    return None


def validate_password(password: str):
    if not password:
        return "password is required"
    if not (PASSWORD_MIN <= len(password) <= PASSWORD_MAX):
        return f"password length must be {PASSWORD_MIN}-{PASSWORD_MAX}"
    if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        return "password must contain at least one letter and one digit"
    return None