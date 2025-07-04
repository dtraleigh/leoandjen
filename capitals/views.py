import us
from django.core import serializers
from django.core.paginator import Paginator
from django.shortcuts import render

from capitals.models import Capital, Photo


def get_us_capital_visited_order():
    """
    Given a list of capitals, return a dict with name and visited order.
    {"name1": "1", "name2": "2"}
    """
    visited_dict = {}
    us_capitals_by_date_visited = \
        [cap for cap in Capital.objects.exclude(us_state="").order_by("date_visited")]
    for count, capital in enumerate(us_capitals_by_date_visited):
        visited_dict[f"{capital.name}"] = f"{count + 1}"

    return visited_dict


def create_us_states_list():
    """
    A rebuild of create_us_states_list but will create a dictionary
    Create a list of dictionaries for each US state.
    """
    us_states_list = []
    us_states_choices = Capital._meta.get_field("us_state").choices
    us_capital_visited_order = get_us_capital_visited_order()

    for state in us_states_choices:
        capital = {
            "name": us.states.lookup(state[0]).capital,
            "state_name": state[1],
            "state_abbr": state[0],
            "visited": get_visited_status(state[0])
        }
        if capital["visited"]:
            capital["visited_order_position"] = us_capital_visited_order[f"{us.states.lookup(state[0]).capital}"]
        us_states_list.append(capital)

    return us_states_list


def get_visited_status(state_abbr):
    # Check if any US state has been visited
    if Capital.objects.filter(us_state=state_abbr).exists():
        return True
    else:
        return False


def create_us_visited_states():
    # Returns list of state names that we have visited
    # ["Indiana", "North Carolina", ....]
    us_visited_states = []

    us_state_objects = [s for s in Capital.objects.exclude(us_state="")]
    for us_state_object in us_state_objects:
        us_visited_states.append(us.states.lookup(us_state_object.us_state).name)

    return us_visited_states


def create_us_visited_cities():
    # Returns list of city names that we have visited
    # ["Raleigh", "Boston", ....]
    us_visited_cities = []

    us_state_objects = [s for s in Capital.objects.exclude(us_state="")]
    for us_state_object in us_state_objects:
        us_visited_cities.append(us.states.lookup(us_state_object.us_state).capital)

    return us_visited_cities


def get_leaflet_footer_vars():
    us_visited_states = create_us_visited_states()
    us_visited_cities = create_us_visited_cities()
    other_capitals_json = serializers.serialize("json", Capital.objects.filter(us_state=""))

    return us_visited_states, us_visited_cities, other_capitals_json


def home(request):
    sort_order = request.GET.get('sort', 'newest')

    # All visited capitals
    if sort_order == 'oldest':
        all_capitals = Capital.objects.all().select_related("country").order_by("date_visited")
    else:
        all_capitals = Capital.objects.all().select_related("country").order_by("-date_visited")

    all_photos = Photo.objects.all().select_related("capital")

    # Pagination
    paginator = Paginator(all_capitals, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # For the Dashboard
    us_states_list = create_us_states_list()
    other_capitals = Capital.objects.filter(us_state="").select_related("country")
    us_capitals_visited = Capital.objects.exclude(us_state="").select_related("country").count()
    us_capitals_visited_percent = (us_capitals_visited / 50) * 100

    us_visited_states, us_visited_cities, other_capitals_json = get_leaflet_footer_vars()

    return render(request, "capital_main.html", {"all_photos": all_photos,
                                                 "all_capitals": all_capitals,
                                                 "us_capitals_visited": us_capitals_visited,
                                                 "us_capitals_visited_percent": us_capitals_visited_percent,
                                                 "us_states_list": us_states_list,
                                                 "other_capitals": other_capitals,
                                                 "us_visited_states": us_visited_states,
                                                 "us_visited_cities": us_visited_cities,
                                                 "other_capitals_json": other_capitals_json,
                                                 "page_obj": page_obj,
                                                 "current_sort": sort_order})


def map_page(request):
    # Capitals outside the US and DC
    other_capitals_json = serializers.serialize("json", Capital.objects.filter(us_state=""))

    # Returns list of state names that we have visited
    # ["Indiana", "North Carolina", ....]
    us_visited_states = []

    us_state_objects = [s for s in Capital.objects.exclude(us_state="")]
    for us_state_object in us_state_objects:
        us_visited_states.append(us.states.lookup(us_state_object.us_state).name)

    us_visited_states, us_visited_cities, other_capitals_json = get_leaflet_footer_vars()

    return render(request, "capital_map.html", {"us_visited_states": us_visited_states,
                                                "us_visited_cities": us_visited_cities,
                                                "other_capitals_json": other_capitals_json})


def capital_page(request, cap_name):
    capital = Capital.objects.get(name=cap_name)
    all_cap_photos = Photo.objects.filter(capital=capital)

    # Needed for photo CSS in index. Improve later
    all_capitals = Capital.objects.all()

    # For the Dashboard
    us_states_list = create_us_states_list()
    other_capitals = Capital.objects.filter(us_state="")
    us_capitals_visited = Capital.objects.exclude(us_state="").count()
    us_capitals_visited_percent = (us_capitals_visited / 50) * 100

    us_visited_states, us_visited_cities, other_capitals_json = get_leaflet_footer_vars()

    return render(request, "capital_page.html", {"capital": capital,
                                                 "all_photos": all_cap_photos,
                                                 "all_capitals": all_capitals,
                                                 "us_states_list": us_states_list,
                                                 "other_capitals": other_capitals,
                                                 "us_capitals_visited": us_capitals_visited,
                                                 "us_capitals_visited_percent": us_capitals_visited_percent,
                                                 "us_visited_states": us_visited_states,
                                                 "us_visited_cities": us_visited_cities,
                                                 "other_capitals_json": other_capitals_json})
