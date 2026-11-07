from django import forms

from .models import ExperimentFileType


class UploadForm(forms.Form):
    kind = forms.ChoiceField(label="Tipo de planilha", choices=ExperimentFileType.choices)
    file = forms.FileField(label="Arquivo (CSV ou Excel)")

    def clean_file(self):
        f = self.cleaned_data["file"]
        if not f.name.lower().endswith((".csv", ".xlsx", ".xls")):
            raise forms.ValidationError("Envie um arquivo .csv, .xlsx ou .xls.")
        return f

class ColumnMappingForm(forms.Form):
    def __init__(self, *args, columns, fields, required_fields, initial_mapping=None, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [("", "---------")] + [(c, c) for c in columns]
        initial_mapping = initial_mapping or {}

        for field, label in fields.items():
            self.fields[field] = forms.ChoiceField(
                label=label,
                choices=choices,
                required=field in required_fields,
                initial=initial_mapping.get(field),
            )

    def clean(self):
        cleaned = super().clean()
        chosen = [col for col in cleaned.values() if col]
        if len(chosen) != len(set(chosen)):
            raise forms.ValidationError("A mesma coluna foi escolhida para mais de um campo.")
        return cleaned

    def get_mapping(self):
        return {field: (col or None) for field, col in self.cleaned_data.items()}