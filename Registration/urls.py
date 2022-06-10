from os import name
from django.shortcuts import render
from django.urls import path
from .views import submit, recognize_face

urlpatterns = [
    path("", lambda request: render(request, "register.html"), name="registration_index"),
    path("recognition", lambda request: render(request, "recognition.html"), name="recognition_page"),
    path("submit", submit, name="register_submit"),
    path("recognize", recognize_face, name="recognize_face"),
]
