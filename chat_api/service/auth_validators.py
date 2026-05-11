import re

USERNAME_MIN = 3
USERNAME_MAX = 32
PASSWORD_MIN = 8
PASSWORD_MAX = 128

# username: lowercase letters, numbers, dot, underscore, dash
_username_re = re.compile(r"^[a-z0-9._-]+$")

# basic email pattern
_email_re = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

# iran phone numbers: 0912..., +98912..., 98912...
_phone_re = re.compile(r"^(\+98|98|0)?9\d{9}$")


def validate_username(username: str):
    if not username:
        return "username is required"

    username = username.strip().lower()

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

    if not any(c.isalpha() for c in password):
        return "password must contain at least one letter"

    if not any(c.isdigit() for c in password):
        return "password must contain at least one digit"

    return None


def validate_email(email: str):
    """
    Email is optional, but if provided must be valid.
    """

    if not email:
        return None

    email = email.strip().lower()

    if len(email) > 255:
        return "email is too long"

    if not _email_re.match(email):
        return "invalid email format"

    return None


def validate_phone_number(phone: str):
    """
    Phone number is optional.
    Supports Iranian mobile formats:
    0912xxxxxxx
    +98912xxxxxxx
    98912xxxxxxx
    """

    if not phone:
        return None

    phone = phone.strip()

    if len(phone) > 20:
        return "phone number is too long"

    if not _phone_re.match(phone):
        return "invalid phone number format"

    return None
