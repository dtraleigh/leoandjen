from django import forms
from django.forms import ModelForm
from videos.models import Video, Album, ExternalVideo


class NewVideoForm(ModelForm):
    album = forms.ModelMultipleChoiceField(queryset=Album.objects.all(), widget=forms.SelectMultiple())

    class Meta:
        model = Video
        fields = ["name",
                  "date_shot",
                  "poster",
                  "video_file",
                  "description",
                  "rich_description",
                  "tags",
                  "lat",
                  "lon"]
        widgets = {
            "date_shot": forms.DateInput(attrs={"class": "datepicker",
                                                "id": "video_date_field"}),
            "tags": forms.SelectMultiple(),
        }


class EditVideoForm(ModelForm):

    class Meta:
        model = Video
        fields = ["name",
                  "date_shot",
                  "poster",
                  "video_file",
                  "description",
                  "rich_description",
                  "tags",
                  "lat",
                  "lon"]
        widgets = {
            "date_shot": forms.DateInput(attrs={"class": "datepicker",
                                                "id": "video_date_field"}),
            "tags": forms.SelectMultiple(),
        }
        
        
class EditExternalForm(ModelForm):

    class Meta:
        model = ExternalVideo
        fields = ["name",
                  "date_shot",
                  "embed_code",
                  "poster",
                  "description",
                  "rich_description",
                  "tags",
                  "lat",
                  "lon"
                  ]
        widgets = {
            "date_shot": forms.DateInput(attrs={"class": "datepicker",
                                                "id": "external_date_field"}),
            "tags": forms.SelectMultiple(),
            "lat": forms.NumberInput(attrs={"id": "id_lat_external"}),
            "lon": forms.NumberInput(attrs={"id": "id_lon_external"})
        }
