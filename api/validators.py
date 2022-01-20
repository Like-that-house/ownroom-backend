import re

from django.contrib.auth.password_validation import get_default_password_validators
from django.core.exceptions import ValidationError


def validated_phone(phoneNumber, errors):
    if re.match('\d{3}-\d{3,4}-\d{4}', phoneNumber) is None:
        errors.append("['전화번호가 형식에 맞지 않습니다.']")
    return errors


def validated_password(password, user=None, password_validators=None):
    """
    Validate whether the password meets all validator requirements.

    If the password is valid, return ``None``.
    If the password is invalid, raise ValidationError with all error messages.
    """
    errors = []
    if password_validators is None:
        password_validators = get_default_password_validators()
    for validator in password_validators:
        try:
            validator.validate(password, user)
        except ValidationError as error:
            errors.append(error)
    return errors