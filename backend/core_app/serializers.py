from rest_framework import serializers

from .models import Movie


class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ["id", "title", "release_year", "runtime", "watched", "prerequisites"]

    def validate_title(self, value):
        return " ".join(value.split())