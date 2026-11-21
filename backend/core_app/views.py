from rest_framework.decorators import api_view
from rest_framework.response import Response

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import BundleSize, Cinema, Movie

from .serializers import MovieSerializer


# ---------------------------------------------------------------------------
# Feature 1 logic: plain functions on a dict {movie_id: [prerequisite_ids]}
# ---------------------------------------------------------------------------

def rewatch_order(target_id, graph):
    """Return every movie needed before target_id, prerequisites first."""
    order = []

    def visit(movie_id):
        # sorted() just keeps the output in a stable order
        for prereq_id in sorted(graph.get(movie_id, [])):
            if prereq_id not in order:
                visit(prereq_id)           # first list what this prerequisite needs
                order.append(prereq_id)    # then list the prerequisite itself

    visit(target_id)
    return order


def would_create_cycle(movie_id, new_prereq_ids, graph):
    """Return True if giving movie_id these prerequisites creates a loop."""
    for prereq_id in new_prereq_ids:
        # A movie can't need itself
        if prereq_id == movie_id:
            return True
        # A movie can't need something that already needs it
        if movie_id in rewatch_order(prereq_id, graph):
            return True
    return False


def summarize_rewatch(order, movies):
    """Count watched movies and add up the runtime of the unwatched ones.

    order:  list of movie ids (the rewatch list)
    movies: dict {movie_id: {"runtime": int, "watched": bool}}
    """
    watched_count = 0
    remaining_runtime = 0

    for movie_id in order:
        if movies[movie_id]["watched"]:
            watched_count += 1
        else:
            remaining_runtime += movies[movie_id]["runtime"]

    return {
        "total_count": len(order),
        "watched_count": watched_count,
        "remaining_runtime_minutes": remaining_runtime,
    }


# ---------------------------------------------------------------------------
# Feature 2 logic: booking quote
# ---------------------------------------------------------------------------

def min_bundles(sizes, group_size):
    """Fewest bundles that add up to exactly group_size seats.

    sizes: list of bundle sizes, e.g. [2, 5]
    Returns a dict {bundle_size: how_many}, or None if it's not possible.
    """
    # fewest[n] = fewest bundles needed for exactly n seats (None = impossible)
    fewest = [None] * (group_size + 1)
    # last_used[n] = the bundle size used last to reach n seats
    last_used = [None] * (group_size + 1)
    fewest[0] = 0

    for n in range(1, group_size + 1):
        for size in sizes:
            if size <= n and fewest[n - size] is not None:
                count = fewest[n - size] + 1
                if fewest[n] is None or count < fewest[n]:
                    fewest[n] = count
                    last_used[n] = size

    if fewest[group_size] is None:
        return None

    # Walk back from group_size, counting each bundle used
    result = {}
    n = group_size
    while n > 0:
        size = last_used[n]
        result[size] = result.get(size, 0) + 1
        n -= size

    return result





# ---------------------------------------------------------------------------
# API views
# ---------------------------------------------------------------------------

@api_view(["GET"])
def health(request):
    return Response({"status": "ok"})


@api_view(["GET", "POST"])
def movie_list(request):
    # GET /api/movies: list all movies
    if request.method == "GET":
        movies = Movie.objects.all()
        return Response(MovieSerializer(movies, many=True).data)

    # POST /api/movies: create one movie
    serializer = MovieSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"code": "VALIDATION_ERROR", "message": str(serializer.errors)}, status=400
        )

    title = serializer.validated_data["title"]
    if Movie.objects.filter(title__iexact=title).exists():
        return Response(
            {"code": "DUPLICATE_NAME", "message": "A movie with this title already exists."},
            status=409,
        )

    serializer.save()
    return Response(serializer.data, status=201)



@api_view(["PATCH"])
def movie_detail(request, movie_id):
    # 1. Find the movie
    try:
        movie = Movie.objects.get(id=movie_id)
    except Movie.DoesNotExist:
        return Response({"code": "NOT_FOUND", "message": "Movie not found."}, status=404)

    # 2. Check the fields (partial=True: only the fields sent are checked)
    serializer = MovieSerializer(movie, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(
            {"code": "VALIDATION_ERROR", "message": str(serializer.errors)}, status=400
        )
    data = serializer.validated_data

    # 3. If the title changes, it must not match another movie (ignoring case)
    if "title" in data:
        if Movie.objects.filter(title__iexact=data["title"]).exclude(id=movie.id).exists():
            return Response(
                {"code": "DUPLICATE_NAME", "message": "A movie with this title already exists."},
                status=409,
            )

    # 4. If prerequisites change, they must not create a loop
    if "prerequisites" in data:
        new_ids = [prereq.id for prereq in data["prerequisites"]]
        graph = {m.id: [p.id for p in m.prerequisites.all()] for m in Movie.objects.all()}
        if would_create_cycle(movie.id, new_ids, graph):
            return Response(
                {"code": "CIRCULAR_DEPENDENCY", "message": "These prerequisites would create a loop."},
                status=409,
            )

    # 5. Save and return the updated movie
    serializer.save()
    return Response(serializer.data)





@api_view(["GET"])
def movie_rewatch_order(request, movie_id):
    # 1. Find the target movie
    try:
        target = Movie.objects.get(id=movie_id)
    except Movie.DoesNotExist:
        return Response({"code": "NOT_FOUND", "message": "Movie not found."}, status=404)

    # 2. Read all movies once: {id: {title, runtime, watched}} and {id: [prerequisite ids]}
    movies = {}
    graph = {}
    for m in Movie.objects.all():
        movies[m.id] = {"title": m.title, "runtime": m.runtime, "watched": m.watched}
        graph[m.id] = [p.id for p in m.prerequisites.all()]

    # 3. Use the functions from Feature 1
    order = rewatch_order(target.id, graph)
    summary = summarize_rewatch(order, movies)

    # 4. Build the response
    return Response({
        "target": {"id": target.id, "title": target.title},
        "order": [
            {"id": movie_id, "title": movies[movie_id]["title"],
             "runtime": movies[movie_id]["runtime"], "watched": movies[movie_id]["watched"]}
            for movie_id in order
        ],
        "total_count": summary["total_count"],
        "watched_count": summary["watched_count"],
        "remaining_runtime_minutes": summary["remaining_runtime_minutes"],
    })





@api_view(["GET", "POST"])
def cinema_list(request):
    # GET /api/cinemas: list all cinemas with their bundle sizes
    if request.method == "GET":
        cinemas = []
        for cinema in Cinema.objects.all():
            sizes = [b.seats for b in cinema.bundle_sizes.all()]
            cinemas.append({"id": cinema.id, "name": cinema.name, "bundle_sizes": sizes})
        return Response(cinemas)

    # POST /api/cinemas: create one cinema
    name = request.data.get("name")
    sizes = request.data.get("bundle_sizes")

    # Check the name
    if not isinstance(name, str) or name.strip() == "" or len(name) > 255:
        return Response(
            {"code": "VALIDATION_ERROR", "message": "name must be text of 1 to 255 characters."},
            status=400,
        )
    name = " ".join(name.split())

    # Check the bundle sizes
    if not isinstance(sizes, list) or not 1 <= len(sizes) <= 10:
        return Response(
            {"code": "VALIDATION_ERROR", "message": "bundle_sizes must be a list of 1 to 10 sizes."},
            status=400,
        )
    for size in sizes:
        if not isinstance(size, int) or not 1 <= size <= 500:
            return Response(
                {"code": "VALIDATION_ERROR", "message": "each bundle size must be a whole number from 1 to 500."},
                status=400,
            )
    if len(set(sizes)) != len(sizes):
        return Response(
            {"code": "VALIDATION_ERROR", "message": "bundle sizes must all be different."},
            status=400,
        )

    # Check the name is not taken (ignoring case)
    if Cinema.objects.filter(name__iexact=name).exists():
        return Response(
            {"code": "DUPLICATE_NAME", "message": "A cinema with this name already exists."},
            status=409,
        )

    # Everything is valid: save the cinema and its bundle sizes
    cinema = Cinema.objects.create(name=name)
    for size in sizes:
        BundleSize.objects.create(cinema=cinema, seats=size)

    return Response(
        {"id": cinema.id, "name": cinema.name, "bundle_sizes": sorted(sizes)},
        status=201,
    )


@api_view(["GET"])
def cinema_booking(request, cinema_id):
    # 1. Find the cinema
    try:
        cinema = Cinema.objects.get(id=cinema_id)
    except Cinema.DoesNotExist:
        return Response({"code": "NOT_FOUND", "message": "Cinema not found."}, status=404)

    # 2. Check groupSize: a whole number from 1 to 10,000
    try:
        group_size = int(request.query_params.get("groupSize"))
    except (TypeError, ValueError):
        return Response(
            {"code": "VALIDATION_ERROR", "message": "groupSize is required and must be a whole number."},
            status=400,
        )
    if not 1 <= group_size <= 10000:
        return Response(
            {"code": "VALIDATION_ERROR", "message": "groupSize must be from 1 to 10000."},
            status=400,
        )

    # 3. Use the Feature 2 function
    sizes = [b.seats for b in cinema.bundle_sizes.all()]
    result = min_bundles(sizes, group_size)

    # 4. Build the response ("not possible" is a valid answer, so it is still 200)
    if result is None:
        return Response({
            "cinema_id": cinema.id,
            "group_size": group_size,
            "possible": False,
            "total_bundles": 0,
            "bundles": [],
        })

    bundles = [{"size": size, "count": count} for size, count in sorted(result.items(), reverse=True)]
    return Response({
        "cinema_id": cinema.id,
        "group_size": group_size,
        "possible": True,
        "total_bundles": sum(result.values()),
        "bundles": bundles,
    })