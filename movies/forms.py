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
        self.fields['formats'].choices = [(f.name, f.name) for f in Format.objects.all()]
        self.fields['collections'].choices = [(c.name, c.name) for c in Collection.objects.all()]


class EditMovieForm(forms.Form):
    imdb_id = forms.CharField(label="IMDB ID", max_length=100, required=True)
    formats = forms.MultipleChoiceField(label="Formats", choices=[], widget=forms.CheckboxSelectMultiple(),
                                        required=False)
    letterboxd_slug = forms.CharField(label="Letterboxd slug", max_length=200, required=False)
    sort_title = forms.CharField(label="Sort Title", max_length=50, required=False)
    collections = forms.MultipleChoiceField(label="Collections", choices=[], widget=forms.CheckboxSelectMultiple(),
                                            required=False)

    def __init__(self, *args, **kwargs):
        movie_instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)

        self.fields['formats'].choices = [(f.name, f.name) for f in Format.objects.all()]
        self.fields['collections'].choices = [(c.name, c.name) for c in Collection.objects.all()]

        if movie_instance:
            self.fields['imdb_id'].initial = movie_instance.imdb_id
            self.fields['letterboxd_slug'].initial = movie_instance.letterboxd_url_slug
            self.fields['sort_title'].initial = movie_instance.sort_title
            self.fields['formats'].initial = [format.name for format in movie_instance.formats.all()]
            self.fields['collections'].initial = [collection.name for collection in movie_instance.collection_set.all()]

