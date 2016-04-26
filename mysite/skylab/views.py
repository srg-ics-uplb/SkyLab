import sys

from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import FormView
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView

from forms import Create_MPI_Cluster_Form, Use_Gamess_Form
from skylab.models import ToolActivity, SkyLabFile

class HomeView(TemplateView):
	template_name = "home.html"

class CreateMPIView(CreateView):
	template_name = 'create_mpi_cluster.html'
	form_class = Create_MPI_Cluster_Form
	success_url = 'create-mpi-cluster'

	def get_form_kwargs(self):
		# pass "user" keyword argument with the current user to your form
		kwargs = super(CreateMPIView, self).get_form_kwargs()
		kwargs['user'] = self.request.user
		return kwargs

class Use_Gamess_View(FormView):
	template_name = "use_gamess.html"
	form_class = Use_Gamess_Form
	success_url = "use-gamess"

	def get_form_kwargs(self):
		# pass "user" keyword argument with the current user to your form
		kwargs = super(Use_Gamess_View, self).get_form_kwargs()
		return kwargs

	def form_valid(self, form):
		tool = ToolActivity.objects.create(
			tool_name="gamess", user=self.request.user
		)
		new_file = SkyLabFile.objects.create(file=self.request.FILES['inp_file'])
		tool.input_files.add(new_file)
		print self.request.FILES['inp_file'].name
		return super(Use_Gamess_View, self).form_valid(form)

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
