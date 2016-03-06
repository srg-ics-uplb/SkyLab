from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.views import generic


class HomePageView(generic.TemplateView):
	template_name = 'home.html'

def index(request):
	return HttpResponse("Hello, world. You're at the skylab index.")
