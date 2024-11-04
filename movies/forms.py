from django import forms
from movies.models import Format, Collection

class AddMovieForm(forms.Form):
    imdb_id = forms.CharField(label="IMDB ID", max_length=100)
    formats = forms.MultipleChoiceField(label="Formats", choices=[], widget=forms.CheckboxSelectMultiple())
    is_tv_movie = forms.BooleanField(label="TV Movie?", required=False)
    letterboxd_slug = forms.CharField(label="Letterboxd slug", max_length=200)
    sort_title = forms.CharField(label="Sort Title", max_length=50, required=False)
    collections = forms.MultipleChoiceField(label="Collections", choices=[], required=False, widget=forms.CheckboxSelectMultiple())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate the choices only when the form is initialized
        self.fields['formats'].choices = [(f.name, f.name) for f in Format.objects.all()]
        self.fields['collections'].choices = [(c.name, c.name) for c in Collection.objects.all()]
