from django import forms

from .models import Categoria, Producto

_INPUT = "form-control"
_SELECT = "form-select"
_CHECK = "form-check-input"


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            "nombre", "marca", "descripcion", "categoria",
            "precio", "stock_actual", "stock_minimo",
            "material", "forma", "imagen", "activo",
        ]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": _INPUT}),
            "marca": forms.TextInput(attrs={"class": _INPUT}),
            "descripcion": forms.Textarea(attrs={"class": _INPUT, "rows": 3}),
            "categoria": forms.Select(attrs={"class": _SELECT}),
            "precio": forms.NumberInput(attrs={"class": _INPUT, "step": "0.01"}),
            "stock_actual": forms.NumberInput(attrs={"class": _INPUT, "min": "0"}),
            "stock_minimo": forms.NumberInput(attrs={"class": _INPUT, "min": "0"}),
            "material": forms.TextInput(attrs={"class": _INPUT}),
            "forma": forms.TextInput(attrs={"class": _INPUT}),
            "imagen": forms.ClearableFileInput(attrs={"class": _INPUT}),
            "activo": forms.CheckboxInput(attrs={"class": _CHECK}),
        }
        labels = {
            "nombre": "Nombre del producto",
            "stock_actual": "Stock actual",
            "stock_minimo": "Stock mínimo",
            "activo": "Visible en el catálogo",
        }
