import logging
import random
from datetime import timedelta
from itertools import chain
from operator import attrgetter

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.db.models import Max
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils import timezone

from videos.forms import *
from videos.models import *

logger = logging.getLogger("video_log")


def is_most_recent(this_shot, shot_list):
    if [i.id for i in shot_list].index(this_shot.id) == 0:
        return True
    else:
        return False


def is_oldest(this_shot, shot_list):
    if [i.id for i in shot_list].index(this_shot.id) == len(shot_list) - 1:
        return True
    else:
        return False


def get_next_shot(curr_shot, shot_list):
    """Find the position that curr_shot is in
    next_shot is the one in the after it"""
    next_shot = shot_list[[i.id for i in shot_list].index(curr_shot.id) - 1]

    return next_shot


def get_prev_shot(curr_shot, shot_list):
    """Find the position that curr_video is in
    next_video is the one in the before it"""
    prev_shot = shot_list[[i.id for i in shot_list].index(curr_shot.id) + 1]

    return prev_shot


def combine_and_sort(video_list, all_external):
    combined_qs = chain(video_list, all_external)
    sorted_combined_qs = sorted(combined_qs, key=attrgetter('date_shot'), reverse=True)

    return sorted_combined_qs


def get_random_shot():
    """since we have content spread across multiple models, let's just do video for now"""
    max_id = Video.objects.all().aggregate(max_id=Max("id"))["max_id"]
    while True:
        pk = random.randint(1, max_id)
        random_video = Video.objects.filter(pk=pk).first()
        if random_video:
            return random_video


def video_login(request):
    """This is the login page. The site is supposed to be password protected."""
    message = "Please log in"
    next = ""

    if request.GET:
        next = request.GET["next"]

    if request.POST:
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                message = "Login successful."

                if next == "":
                    return HttpResponseRedirect("/videos/main/")
                else:
                    return HttpResponseRedirect(next)
            else:
                message = "Account is disabled."
        else:
            message = "Invalid login."

    return render(request, "videos_login.html", {"message": message,
                                                 "next": next,
                                                 "show_nav": False})


def video_logout(request):
    logout(request)

    return HttpResponseRedirect("/videos")


def get_map_data():
    video_map_data = serializers.serialize("json",
                                           Video.objects.filter(lat__isnull=False, lon__isnull=False),
                                           fields=("name", "date_shot", "lat", "lon"))
    external_map_data = serializers.serialize("json",
                                              ExternalVideo.objects.filter(lat__isnull=False, lon__isnull=False),
                                              fields=("name", "date_shot", "lat", "lon"))

    return video_map_data, external_map_data


def get_shot(shot_type, shot_id):
    """The shot the user wants to see"""
    if shot_type == "video":
        this_shot = Video.objects.get(id=shot_id)
    elif shot_type == "external":
        this_shot = ExternalVideo.objects.get(id=shot_id)

    return this_shot


@login_required(redirect_field_name="next")
def main(request):
    albums = Album.objects.all()

    all_videos = Video.objects.all()
    all_external = ExternalVideo.objects.all()
    all_shots = combine_and_sort(all_videos, all_external)

    return render(request, "videos_index.html", {"albums": albums,
                                                 "tag_list": Tag.objects.all(),
                                                 "most_recent": all_shots[0:6],
                                                 "show_nav": True})


@login_required(redirect_field_name="next")
def map_view(request):
    video_map_data, external_map_data = get_map_data()

    return render(request, "videos_map.html", {"video_map_data": video_map_data,
                                               "external_map_data": external_map_data,
                                               "show_nav": True})


@login_required(redirect_field_name="next")
def upload(request):
    if request.method == "POST":
        upload_form = NewVideoForm(request.POST, request.FILES)

        if upload_form.is_valid():
            new_video = upload_form.save()

            album_choice = upload_form.cleaned_data["album"]
            # logger.debug(album_choice)
            for a in album_choice:
                a.videos.add(new_video)
                a.save()

            messages.info(request, "Successfully uploaded " + new_video.name + ".")

            if "save_video" in request.POST:
                return HttpResponseRedirect("/videos/main/upload/")
            if "save_video_and_main" in request.POST:
                return HttpResponseRedirect("/videos/main/")

    else:
        # Want to prefill the lat and lon with the last video upload session's values.
        # If the most recently uploaded video was within the last hour, prefill it's lat lon
        try:
            recently_uploaded_video = Video.objects.latest("date_added")
            if recently_uploaded_video.date_added > timezone.now() - timedelta(hours=1):
                upload_form = NewVideoForm(
                    initial={"lat": recently_uploaded_video.lat, "lon": recently_uploaded_video.lon})
            else:
                upload_form = NewVideoForm()
        except Exception:
            upload_form = NewVideoForm()

    quick_locations = Location.objects.all()

    return render(request, "videos_upload.html", {"upload_form": upload_form,
                                                  "quick_locations": quick_locations,
                                                  "show_nav": True})


@login_required(redirect_field_name="next")
def album_view(request, album_id):
    all_albums = Album.objects.get(id=album_id)

    album_videos = [v for v in all_albums.videos.all()]
    album_externals = [ex for ex in all_albums.external_videos.all()]

    return render(request, "videos_album.html", {"album": all_albums,
                                                 "album_videos": combine_and_sort(album_videos, album_externals),
                                                 "show_nav": True})


@login_required(redirect_field_name="next")
def shot_view(request, album_id, shot_type, shot_id):
    this_shot = get_shot(shot_type, shot_id)

    # The album the user is within
    current_album = Album.objects.get(id=album_id)

    album_videos = [v for v in current_album.videos.all()]
    album_external = [ex for ex in current_album.external_videos.all()]

    # All the shots within this album
    album_shots = combine_and_sort(album_videos, album_external)

    if not is_most_recent(this_shot, album_shots):
        next_video = get_next_shot(this_shot, album_shots)
        no_next = False
    else:
        next_video = this_shot
        no_next = True

    if not is_oldest(this_shot, album_shots):
        prev_video = get_prev_shot(this_shot, album_shots)
        no_prev = False
    else:
        prev_video = this_shot
        no_prev = True

    video_map_data, external_map_data = get_map_data()

    return render(request, "shot.html", {"video": this_shot,
                                         "current_album": current_album,
                                         "album": current_album,
                                         "album_videos": album_shots,
                                         "video_tags": [t for t in this_shot.tags.all()],
                                         "album_view": True,
                                         "next_video": next_video,
                                         "no_next": no_next,
                                         "no_prev": no_prev,
                                         "prev_video": prev_video,
                                         "video_map_data": video_map_data,
                                         "external_map_data": external_map_data,
                                         "show_nav": True})


@login_required(redirect_field_name="next")
def tag_view(request, tag_name):
    videos_w_tag = Video.objects.filter(tags__name=tag_name)
    externals_w_tag = ExternalVideo.objects.filter(tags__name=tag_name)

    # All the shots with this tag
    videos_w_tag = combine_and_sort(videos_w_tag, externals_w_tag)

    return render(request, "tag.html", {"videos_w_tag": videos_w_tag,
                                        "the_tag": Tag.objects.get(name=tag_name),
                                        "show_nav": True})


@login_required(redirect_field_name="next")
def video_tag_view(request, tag_name, shot_type, shot_id):
    this_shot = get_shot(shot_type, shot_id)

    videos_w_tag = Video.objects.filter(tags__name=tag_name)
    externals_w_tag = ExternalVideo.objects.filter(tags__name=tag_name)
    shots_w_tag = combine_and_sort(videos_w_tag, externals_w_tag)

    if not is_most_recent(this_shot, shots_w_tag):
        next_video = get_next_shot(this_shot, shots_w_tag)
        no_next = False
    else:
        next_video = this_shot
        no_next = True

    if not is_oldest(this_shot, shots_w_tag):
        prev_video = get_prev_shot(this_shot, shots_w_tag)
        no_prev = False
    else:
        prev_video = this_shot
        no_prev = True

    video_map_data, external_map_data = get_map_data()

    return render(request, "shot.html", {"video": this_shot,
                                         "the_tag": Tag.objects.get(name=tag_name),
                                         "video_tags": [t for t in this_shot.tags.all()],
                                         "tag_view": True,
                                         "next_video": next_video,
                                         "no_next": no_next,
                                         "no_prev": no_prev,
                                         "prev_video": prev_video,
                                         "video_map_data": video_map_data,
                                         "external_map_data": external_map_data,
                                         "show_nav": True})


@login_required(redirect_field_name="next")
def recent_view(request, shot_type, shot_id):
    this_shot = get_shot(shot_type, shot_id)

    all_videos = Video.objects.all()
    all_external = ExternalVideo.objects.all()
    all_shots = combine_and_sort(all_videos, all_external)

    if not is_most_recent(this_shot, all_shots):
        next_video = get_next_shot(this_shot, all_shots)
        no_next = False
    else:
        next_video = this_shot
        no_next = True

    if not is_oldest(this_shot, all_shots):
        prev_video = get_prev_shot(this_shot, all_shots)
        no_prev = False
    else:
        prev_video = this_shot
        no_prev = True

    video_map_data, external_map_data = get_map_data()

    return render(request, "shot.html", {"video": this_shot,
                                         "video_tags": [t for t in this_shot.tags.all()],
                                         "next_video": next_video,
                                         "prev_video": prev_video,
                                         "no_next": no_next,
                                         "no_prev": no_prev,
                                         "recent_view": True,
                                         "video_map_data": video_map_data,
                                         "external_map_data": external_map_data,
                                         "show_nav": True})


@login_required(redirect_field_name="next")
def shot_edit_view(request, shot_type, shot_id):
    shot_to_edit = get_shot(shot_type, shot_id)

    if request.method == "POST":
        next_url = request.GET.get("next", None)

        if shot_type == "video":
            edit_form = EditVideoForm(request.POST, instance=shot_to_edit)
        if shot_type == "external":
            edit_form = EditExternalForm(request.POST, instance=shot_to_edit)

        if "cancel-button" in request.POST:
            messages.info(request, "Canceled edit to " + shot_to_edit.name + ".")

            return HttpResponseRedirect("/videos/main/")

        if edit_form.is_valid():
            edit_form.save()
            messages.success(request, "Details for " + shot_to_edit.name + " updated.")

            if "save_video_and_main" in request.POST:
                return HttpResponseRedirect("/videos/main/")

            if "save_shot" in request.POST:
                if next_url:
                    return HttpResponseRedirect(next_url)

    else:
        if shot_type == "video":
            edit_form = EditVideoForm(instance=shot_to_edit)
        if shot_type == "external":
            edit_form = EditExternalForm(instance=shot_to_edit)

    quick_locations = Location.objects.all()

    return render(request, "videos_edit.html", {"edit_form": edit_form,
                                                "quick_locations": quick_locations,
                                                "from": request.GET.get("from", None),
                                                "show_nav": True})


@login_required(redirect_field_name="next")
def random_shot_view(request):
    random_shot = get_random_shot()

    video_map_data, external_map_data = get_map_data()

    return render(request, "videos_random.html", {"video": random_shot,
                                                  "video_tags": [t for t in random_shot.tags.all()],
                                                  "video_map_data": video_map_data,
                                                  "external_map_data": external_map_data,
                                                  "show_nav": True})


@login_required(redirect_field_name="next")
def map_shot(request, shot_type, shot_id):
    this_shot = get_shot(shot_type, shot_id)

    video_map_data, external_map_data = get_map_data()

    return render(request, "map_shot.html", {"video": this_shot,
                                             "video_tags": [t for t in this_shot.tags.all()],
                                             "video_map_data": video_map_data,
                                             "external_map_data": external_map_data,
                                             "show_nav": True})
