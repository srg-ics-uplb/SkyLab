from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.views import generic
from forms import ImpiForm
import sys


class HomePageView(generic.TemplateView):
	template_name = 'home.html'
	form = ImpiForm()

def index(request):
	return HttpResponse("Hello, world. You're at the skylab index.")

def use_impi(request):
	if request.method == 'POST':
		form = ImpiForm(request.POST)

		if form.is_valid():
			print >> sys.stderr, request.POST['mpi_cluster_size']


	else:
		form = ImpiForm()

	return render(request, 'home.html', {'form': form})
