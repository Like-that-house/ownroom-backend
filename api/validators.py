import re
from django.core.exceptions import ValidationError

def validate_phone(phoneNumber):
    return re.match('\d{3}-\d{3,4}-\d{4}', phoneNumber) is not None

