from django import forms

from .models import LogFile, MeasurementType, SampleMeasurementFile


class LogFileForm(forms.ModelForm):
    class Meta:
        model = LogFile
        fields = ["file", "file_type"]


class MeasurementTypeForm(forms.ModelForm):
    class Meta:
        model = MeasurementType
        fields = ["name", "unit"]


class SampleMeasurementFileForm(forms.ModelForm):
    class Meta:
        model = SampleMeasurementFile
        fields = ["measurement_type", "file"]

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project is not None:
            self.fields["measurement_type"].queryset = MeasurementType.objects.filter(project=project)