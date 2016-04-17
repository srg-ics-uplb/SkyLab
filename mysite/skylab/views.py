import sys

from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic.edit import FormView

from forms import Create_MPI_Cluster_Form


class HomePageView(FormView):
	template_name = 'home.html'
	form_class = Create_MPI_Cluster_Form
	success_url = ''

	def form_valid(self, form):
		# This method is called when valid form data has been POSTed.
		# It should return an HttpResponse.
		# form.send_email()
		print >> sys.stderr, form.mpi_cluster_size
		return super(HomePageView, self).form_valid(form)

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
