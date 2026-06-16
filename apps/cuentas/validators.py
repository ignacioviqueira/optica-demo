import re

from django.core.exceptions import ValidationError


class StrongPasswordValidator:
    """
    Exige mayúscula, minúscula, número y carácter especial (HU-01 tesis).
    """

    RULES = [
        (r"[A-Z]", "Al menos una letra mayúscula."),
        (r"[a-z]", "Al menos una letra minúscula."),
        (r"\d", "Al menos un número."),
        (r"[^A-Za-z0-9]", "Al menos un carácter especial (ej. @, #, $, !, %)."),
    ]

    def validate(self, password, user=None):
        errors = [msg for pattern, msg in self.RULES if not re.search(pattern, password)]
        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return (
            "La contraseña debe incluir al menos: una mayúscula, una minúscula, "
            "un número y un carácter especial (ej. @, #, $, !, %)."
        )
