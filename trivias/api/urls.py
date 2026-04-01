from django.urls import path

from trivias.api.views import VistaTriviaActivaAPIView

urlpatterns = [
    path("activa/", VistaTriviaActivaAPIView.as_view(), name="trivia-activa"),
]
