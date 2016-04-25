import sys

from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic.edit import CreateView

from forms import Create_MPI_Cluster_Form


class CreateMPIView(CreateView):
	template_name = 'create_mpi_cluster.html'
	form_class = Create_MPI_Cluster_Form
	success_url = '/'

	# def form_valid(self, form):
	# 	# This method is called when valid form data has been POSTed.
	# 	# It should return an HttpResponse.
	# 	# form.send_email()
	# 	# print self.object.cluster_name
	# 	return super(CreateMPIView, self).form_valid(form)

	def get_form_kwargs(self):
		# pass "user" keyword argument with the current user to your form
		kwargs = super(CreateMPIView, self).get_form_kwargs()
		kwargs['user'] = self.request.user
		return kwargs

def index(request):
	return HttpResponse("Hello, world. You're at the skylab index.")

def use_impi(request):
	if request.method == 'POST':
		form = ImpiForm(request.POST)

		if form.is_valid():
			print >> sys.stderr, request.POST['mpi_cluster_size']


	else:
		form = ImpiForm()

	return render(request, 'skylab/templates/home.html', {'form': form})
