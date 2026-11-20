from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models.functions import Lower


class Movie(models.Model):
    title = models.CharField(max_length=255, unique=True)
    release_year = models.IntegerField()
    runtime = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(300)],)
    watched = models.BooleanField(default=False)
    prerequisites = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="required_by",
    )

    class Meta:
        ordering = ["id"]
        constraints = [models.UniqueConstraint(Lower("title"), name="unique_movie_title_ci"),]

    def __str__(self):
        return self.title




class Cinema(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ["id"]
        constraints = [models.UniqueConstraint(Lower("name"), name="unique_cinema_name_ci"),]

    def __str__(self):
        return self.name


class BundleSize(models.Model):
    cinema = models.ForeignKey(Cinema, on_delete=models.CASCADE, related_name="bundle_sizes",)
    seats = models.IntegerField( validators=[MinValueValidator(1), MaxValueValidator(500)],)

    class Meta:
        ordering = ["seats"]
        constraints = [models.UniqueConstraint(fields=["cinema", "seats"], name="unique_bundle_size_per_cinema",),]

    def __str__(self):
        return f"{self.cinema.name}: {self.seats} seats"