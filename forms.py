from django import forms

from plugins.production_transporter import models
from core import models as core_models


class TransportFilesForm(forms.ModelForm):
    class Meta:
        model = models.TransportFiles
        fields = (
            'files',
        )
        widgets = {
            'files': forms.CheckboxSelectMultiple
        }

    def __init__(self, *args, **kwargs):
        self.article = kwargs.pop('article')
        self.article_files = kwargs.pop('article_files')
        self.files_selected_by = kwargs.pop('files_selected_by')
        super(TransportFilesForm, self).__init__(*args, **kwargs)
        self.fields['files'].queryset = self.article_files

    def save(self, commit=True):
        obj = super(TransportFilesForm, self).save(commit=False)
        obj.article = self.article
        obj.files_selected_by = self.files_selected_by

        if commit:
            obj.save()
            self.save_m2m()

        return obj
