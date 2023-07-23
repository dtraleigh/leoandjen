from django import forms

from movies.models import Format, Collection

FORMATS = []
for movie_format in [f for f in Format.objects.all()]:
    FORMATS.append((movie_format.name, movie_format.name))

COLLECTIONS = []
for collection in [c for c in Collection.objects.all()]:
    COLLECTIONS.append((collection.name, collection.name))


class AddMovieForm(forms.Form):
    imdb_id = forms.CharField(label="IMDB ID", max_length=100)
    formats = forms.MultipleChoiceField(label="Formats", choices=FORMATS, widget=forms.CheckboxSelectMultiple())
    is_tv_movie = forms.BooleanField(label="TV Movie?", required=False)
    letterboxd_slug = forms.CharField(label="Letterboxd slug", max_length=200)
    sort_title = forms.CharField(label="Sort Title", max_length=50, required=False)
    collections = forms.MultipleChoiceField(label="Collections",
                                            required=False,
                                            choices=COLLECTIONS,
                                            widget=forms.CheckboxSelectMultiple())
