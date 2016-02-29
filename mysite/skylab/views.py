from __future__ import absolute_import

from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse


from django.contrib.auth import authenticate, logout, login
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.models import User
from django.views import generic
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
from braces import views

from .forms import RegistrationForm, LoginForm

from .models import Question, Choice

class IndexView(generic.ListView):
    template_name = 'skylab/index.html'
    context_object_name = 'latest_question_list'

    def get_queryset(self):
	    """
	    Return the last five published questions (not including those set to be
	    published in the future).
	    """
	    return Question.objects.filter(
	        pub_date__lte=timezone.now()
	    ).order_by('-pub_date')[:5]

class DetailView(generic.DetailView):
    model = Question
    template_name = 'skylab/detail.html'

    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())

class ResultsView(generic.DetailView):
    model = Question
    template_name = 'skylab/results.html'
def vote(request, question_id):
	quesiton = get_object_or_404(Question, pk=question_id)
	try:
		selected_choice = question.choice_set.get(pk=request.POST['choice'])
	except (KeyError, Choice.DoesNotExist):
		# Redisplay the question voting form
		return render(request, 'skylab/detail.html',{
			'question':question,
			'error_message': "You didn't select a choice.",
		})
	else:
		selected_choice.votes += 1
		selected_choice.save()

		return HttpResponseRedirect(reverse('skylab:results', args=(question.id,)))