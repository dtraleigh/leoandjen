import json
import random

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from game_randomizer.models import Bundle, Game, GameReview


@login_required(login_url="/admin")
def randomizer(request):
    total_games = Game.objects.count()
    unplayed_count = Game.objects.filter(
        Q(review__isnull=True) | Q(review__rating__isnull=True)
    ).count()
    reviewed_count = total_games - unplayed_count

    # Rating distribution: how many games at each star level
    rating_counts = dict(
        GameReview.objects.exclude(rating__isnull=True)
        .values_list("rating")
        .annotate(c=Count("id"))
    )
    rating_distribution = {
        "one": rating_counts.get(1, 0),
        "two": rating_counts.get(2, 0),
        "three": rating_counts.get(3, 0),
    }

    # Filler pool for reel animation — 20 random games with image and title
    filler_qs = Game.objects.exclude(image_url="").order_by("?")[:20]
    filler_pool = [
        {"id": g.id, "title": g.title, "image_url": g.image_url}
        for g in filler_qs
    ]

    # Distinct non-empty category tags for the exclusion filter
    categories = sorted(
        Game.objects.exclude(category_tag="")
        .order_by()
        .values_list("category_tag", flat=True)
        .distinct()
    )

    return render(request, "randomizer.html", {
        "total_games": total_games,
        "unplayed_count": unplayed_count,
        "reviewed_count": reviewed_count,
        "rating_distribution": rating_distribution,
        "filler_pool_json": json.dumps(filler_pool),
        "categories": categories,
    })


@login_required(login_url="/admin")
def api_spin(request):
    try:
        count = int(request.GET.get("count", 1))
    except (ValueError, TypeError):
        count = 1
    count = max(1, min(3, count))

    unplayed_only = request.GET.get("unplayed_only") == "true"
    exclude_categories = request.GET.getlist("exclude_category")

    queryset = Game.objects.all()
    if unplayed_only:
        queryset = queryset.filter(
            Q(review__isnull=True) | Q(review__rating__isnull=True)
        )
    if exclude_categories:
        queryset = queryset.exclude(category_tag__in=exclude_categories)

    ids = list(queryset.values_list("id", flat=True))

    if len(ids) < count:
        return JsonResponse(
            {"error": "Not enough games available", "available": len(ids)},
            status=400,
        )

    selected_ids = random.sample(ids, count)
    games = Game.objects.filter(id__in=selected_ids)

    results = [
        {
            "id": g.id,
            "title": g.title,
            "developer": g.developer,
            "developer_url": g.developer_url,
            "description": g.description,
            "category_tag": g.category_tag,
            "image_url": g.image_url,
            "game_url": g.game_url,
            "platforms": g.platforms,
        }
        for g in games
    ]

    return JsonResponse({"games": results})


@login_required(login_url="/admin")
def game_list(request):
    games = Game.objects.select_related("review").prefetch_related("bundles").all()
    bundles = Bundle.objects.all()

    # Collect all unique platforms across the dataset for the filter dropdown
    platform_set = set()
    for g in games:
        for p in g.platforms or []:
            platform_set.add(p)
    platforms = sorted(platform_set)

    # Distinct non-empty category tags for the filter dropdown.
    # .order_by() clears Game.Meta.ordering — otherwise the default `title`
    # ordering gets folded into the SELECT and breaks .distinct().
    categories = sorted(
        Game.objects.exclude(category_tag="")
        .order_by()
        .values_list("category_tag", flat=True)
        .distinct()
    )

    return render(request, "game_list.html", {
        "games": games,
        "bundles": bundles,
        "platforms": platforms,
        "categories": categories,
    })


@login_required(login_url="/admin")
def game_detail(request, game_id):
    game = get_object_or_404(
        Game.objects.prefetch_related("bundles"), id=game_id
    )
    review = getattr(game, "review", None)

    return render(request, "game_detail.html", {
        "game": game,
        "review": review,
    })


@login_required(login_url="/admin")
def save_review(request, game_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    game = get_object_or_404(Game, id=game_id)

    rating_str = request.POST.get("rating", "")
    rating = int(rating_str) if rating_str else None
    if rating is not None and rating not in (1, 2, 3):
        return JsonResponse({"error": "Invalid rating"}, status=400)

    notes = request.POST.get("notes", "")

    review, _ = GameReview.objects.get_or_create(game=game)
    review.rating = rating
    review.notes = notes
    review.save()

    return JsonResponse({"ok": True, "rating": review.rating, "notes": review.notes})
