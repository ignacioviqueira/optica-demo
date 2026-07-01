from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def precio_ar(value):
    """Formatea un precio con separador de miles argentino: 135000 → 135.000"""
    try:
        n = int(Decimal(str(value)).quantize(Decimal("1")))
        return f"{n:,}".replace(",", ".")
    except (ValueError, TypeError, InvalidOperation):
        return str(value)
