from decimal import Decimal, InvalidOperation
from django import forms
from django.forms import ModelForm
from django.core.exceptions import ValidationError

from videos.models import Album, ExternalVideo, Video


class CoordinatesField(forms.CharField):
    """
    Custom field that accepts coordinates in Google Maps format: "lat, lon"
    Returns a tuple of (lat, lon) as Decimal objects
    Automatically rounds to 6 decimal places to match model constraints
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('help_text', 'Enter coordinates as: latitude, longitude (e.g., 35.780327, -78.628655)')
        super().__init__(*args, **kwargs)

    def clean(self, value):
        value = super().clean(value)

        if not value:
            return None

        # Remove extra whitespace
        value = value.strip()

        # Split by comma
        parts = value.split(',')

        if len(parts) != 2:
            raise ValidationError(
                'Invalid coordinate format. Please enter as: latitude, longitude (e.g., 35.780327, -78.628655)'
            )

        try:
            lat = Decimal(parts[0].strip())
            lon = Decimal(parts[1].strip())
        except (InvalidOperation, ValueError):
            raise ValidationError(
                'Coordinates must be valid numbers. Please enter as: latitude, longitude (e.g., 35.780327, -78.628655)'
            )

        # Validate latitude range
        if lat < -90 or lat > 90:
            raise ValidationError('Latitude must be between -90 and 90 degrees.')

        # Validate longitude range
        if lon < -180 or lon > 180:
            raise ValidationError('Longitude must be between -180 and 180 degrees.')

        # Round to 6 decimal places to match model constraints (max_digits=9, decimal_places=6)
        # This allows Google Maps coordinates with many decimal places to be automatically formatted
        lat = lat.quantize(Decimal('0.000001'))
        lon = lon.quantize(Decimal('0.000001'))

        return (lat, lon)


class NewVideoForm(ModelForm):
    album = forms.ModelMultipleChoiceField(queryset=Album.objects.all(), widget=forms.SelectMultiple())
    coordinates = CoordinatesField(required=False, widget=forms.TextInput(attrs={
        'placeholder': '35.780327, -78.628655',
        'class': 'form-control'
    }))

    class Meta:
        model = Video
        fields = ["name",
                  "date_shot",
                  "poster",
                  "video_file",
                  "description",
                  "tags"]
        widgets = {
            "date_shot": forms.DateInput(attrs={"class": "datepicker",
                                                "id": "video_date_field"}),
            "tags": forms.SelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If initial data has lat/lon, populate coordinates field
        if self.initial.get('lat') is not None and self.initial.get('lon') is not None:
            self.initial['coordinates'] = f"{self.initial['lat']}, {self.initial['lon']}"

    def clean(self):
        cleaned_data = super().clean()
        coordinates = cleaned_data.get('coordinates')

        if coordinates:
            lat, lon = coordinates
            cleaned_data['lat'] = lat
            cleaned_data['lon'] = lon

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Set lat and lon from cleaned_data if coordinates were provided
        if 'lat' in self.cleaned_data:
            instance.lat = self.cleaned_data['lat']
        if 'lon' in self.cleaned_data:
            instance.lon = self.cleaned_data['lon']

        if commit:
            instance.save()
            self.save_m2m()

        return instance


class EditVideoForm(ModelForm):
    coordinates = CoordinatesField(required=False, widget=forms.TextInput(attrs={
        'placeholder': '35.780327, -78.628655',
        'class': 'form-control'
    }))

    class Meta:
        model = Video
        fields = ["name",
                  "date_shot",
                  "poster",
                  "video_file",
                  "description",
                  "tags"]
        widgets = {
            "date_shot": forms.DateInput(attrs={"class": "datepicker",
                                                "id": "video_date_field"}),
            "tags": forms.SelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If instance has lat/lon, populate coordinates field
        if self.instance and self.instance.pk:
            if self.instance.lat is not None and self.instance.lon is not None:
                self.initial['coordinates'] = f"{self.instance.lat}, {self.instance.lon}"

    def clean(self):
        cleaned_data = super().clean()
        coordinates = cleaned_data.get('coordinates')

        if coordinates:
            lat, lon = coordinates
            cleaned_data['lat'] = lat
            cleaned_data['lon'] = lon

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Set lat and lon from cleaned_data if coordinates were provided
        if 'lat' in self.cleaned_data:
            instance.lat = self.cleaned_data['lat']
        if 'lon' in self.cleaned_data:
            instance.lon = self.cleaned_data['lon']

        if commit:
            instance.save()
            self.save_m2m()

        return instance


class EditExternalForm(ModelForm):
    coordinates = CoordinatesField(required=False, widget=forms.TextInput(attrs={
        'placeholder': '35.780327, -78.628655',
        'class': 'form-control',
        'id': 'id_coordinates_external'
    }))

    class Meta:
        model = ExternalVideo
        fields = ["name",
                  "date_shot",
                  "embed_code",
                  "poster",
                  "description",
                  "tags"]
        widgets = {
            "date_shot": forms.DateInput(attrs={"class": "datepicker",
                                                "id": "external_date_field"}),
            "tags": forms.SelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If instance has lat/lon, populate coordinates field
        if self.instance and self.instance.pk:
            if self.instance.lat is not None and self.instance.lon is not None:
                self.initial['coordinates'] = f"{self.instance.lat}, {self.instance.lon}"

    def clean(self):
        cleaned_data = super().clean()
        coordinates = cleaned_data.get('coordinates')

        if coordinates:
            lat, lon = coordinates
            cleaned_data['lat'] = lat
            cleaned_data['lon'] = lon

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Set lat and lon from cleaned_data if coordinates were provided
        if 'lat' in self.cleaned_data:
            instance.lat = self.cleaned_data['lat']
        if 'lon' in self.cleaned_data:
            instance.lon = self.cleaned_data['lon']

        if commit:
            instance.save()
            self.save_m2m()

        return instance