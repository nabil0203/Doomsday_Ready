from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.health),
    path("movies", views.movie_list),
    path("movies/<int:movie_id>", views.movie_detail),
    path("movies/<int:movie_id>/rewatch-order", views.movie_rewatch_order),
    path("cinemas", views.cinema_list),
    path("cinemas/<int:cinema_id>/booking", views.cinema_booking),
]