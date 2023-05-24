from django.db import models


class Capital(models.Model):
    ALABAMA = "AL"
    ALASKA = "AK"
    ARIZONA = "AZ"
    ARKANSAS = "AR"
    CALIFORNIA = "CA"
    COLORADO = "CO"
    CONNECTICUT = "CT"
    DELAWARE = "DE"
    FLORIDA = "FL"
    GEORGIA = "GA"
    HAWAII = "HI"
    IDAHO = "ID"
    ILLINOIS = "IL"
    INDIANA = "IN"
    IOWA = "IA"
    KANSAS = "KS"
    KENTUCKY = "KY"
    LOUISIANA = "LA"
    MAINE = "ME"
    MARYLAND = "MD"
    MASSACHUSETTS = "MA"
    MICHIGAN = "MI"
    MINNESOTA = "MN"
    MISSISSIPPI = "MS"
    MISSOURI = "MO"
    MONTANA = "MT"
    NEBRASKA = "NE"
    NEVADA = "NV"
    NEW_HAMPSHIRE = "NH"
    NEW_JERSEY = "NJ"
    NEW_MEXICO = "NM"
    NEW_YORK = "NY"
    NORTH_CAROLINA = "NC"
    NORTH_DAKOTA = "ND"
    OHIO = "OH"
    OKLAHOMA = "OK"
    OREGON = "OR"
    PENNSYLVANIA = "PA"
    RHODE_ISLAND = "RI"
    SOUTH_CAROLINA = "SC"
    SOUTH_DAKOTA = "SD"
    TENNESSEE = "TN"
    TEXAS = "TX"
    UTAH = "UT"
    VERMONT = "VT"
    VIRGINIA = "VA"
    WASHINGTON = "WA"
    WEST_VIRGINIA = "WV"
    WISCONSIN = "WI"
    WYOMING = "WY"

    STATE_CHOICES = (
        (ALABAMA, "Alabama"),
        (ALASKA, "Alaska"),
        (ARIZONA, "Arizona"),
        (ARKANSAS, "Arkansas"),
        (CALIFORNIA, "California"),
        (COLORADO, "Colorado"),
        (CONNECTICUT, "Connecticut"),
        (DELAWARE, "Delaware"),
        (FLORIDA, "Florida"),
        (GEORGIA, "Georgia"),
        (HAWAII, "Hawaii"),
        (IDAHO, "Idaho"),
        (ILLINOIS, "Illinois"),
        (INDIANA, "Indiana"),
        (IOWA, "Iowa"),
        (KANSAS, "Kansas"),
        (KENTUCKY, "Kentucky"),
        (LOUISIANA, "Louisiana"),
        (MAINE, "Maine"),
        (MARYLAND, "Maryland"),
        (MASSACHUSETTS, "Massachusetts"),
        (MICHIGAN, "Michigan"),
        (MINNESOTA, "Minnesota"),
        (MISSISSIPPI, "Mississippi"),
        (MISSOURI, "Missouri"),
        (MONTANA, "Montana"),
        (NEBRASKA, "Nebraska"),
        (NEVADA, "Nevada"),
        (NEW_HAMPSHIRE, "New Hampshire"),
        (NEW_JERSEY, "New Jersey"),
        (NEW_MEXICO, "New Mexico"),
        (NEW_YORK, "New York"),
        (NORTH_CAROLINA, "North Carolina"),
        (NORTH_DAKOTA, "North Dakota"),
        (OHIO, "Ohio"),
        (OKLAHOMA, "Oklahoma"),
        (OREGON, "Oregon"),
        (PENNSYLVANIA, "Pennsylvania"),
        (RHODE_ISLAND, "Rhode Island"),
        (SOUTH_CAROLINA, "South Carolina"),
        (SOUTH_DAKOTA, "South Dakota"),
        (TENNESSEE, "Tennessee"),
        (TEXAS, "Texas"),
        (UTAH, "Utah"),
        (VERMONT, "Vermont"),
        (VIRGINIA, "Virginia"),
        (WASHINGTON, "Washington"),
        (WEST_VIRGINIA, "West Virginia"),
        (WISCONSIN, "Wisconsin"),
        (WYOMING, "Wyoming"),
    )

    name = models.CharField(max_length=200, unique=True)
    us_state = models.CharField(
        max_length=2,
        choices=STATE_CHOICES,
        blank=True,
        default=None,
        verbose_name="US State",
    )
    date_visited = models.DateField()
    description = models.TextField(blank=True)
    lat = models.DecimalField(max_digits=9, decimal_places=6, default=0, verbose_name="Latitude")
    lon = models.DecimalField(max_digits=9, decimal_places=6, default=0, verbose_name="Longitude")
    flag = models.FileField(upload_to="flags/")
    flag_caption = models.CharField(max_length=300, blank=True)
    country = models.ForeignKey("Country", on_delete=models.CASCADE)
    photo_album_url = models.URLField(blank=True)

    class Meta:
        ordering = ["-date_visited"]

    def __str__(self):
        return f"{self.name}"

    @property
    def get_us_capital_visited_order_position(self):
        # With all the US capitals ordered by -date_visited, return the placement of this capital. Return it as a string
        us_capitals_by_date_visited = \
            [cap for cap in Capital.objects.exclude(us_state="").order_by("date_visited")]
        try:
            return str(us_capitals_by_date_visited.index(self) + 1)
        except ValueError:
            return None

    @property
    def is_us_capital(self):
        if self.us_state == "":
            return False
        return True


class Photo(models.Model):
    name = models.CharField(max_length=200)
    photo_file = models.ImageField(upload_to="photos/")
    capital = models.ForeignKey(Capital, on_delete=models.CASCADE, null=True)
    # photo_width = models.IntegerField(default=1000)
    # photo_height = models.IntegerField(default=664)

    def __str__(self):
        return f"{self.name}"


class Country(models.Model):
    name = models.CharField(max_length=200)
    flag = models.ImageField(upload_to="flags/")

    class Meta:
        verbose_name_plural = "Countries"

    def __str__(self):
        return f"{self.name}"
