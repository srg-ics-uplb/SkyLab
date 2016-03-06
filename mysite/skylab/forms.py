from registration.forms import RegistrationForm
from django import forms
from registration.signals import user_registered

class MyRegistrationForm(RegistrationForm):
	first_name = forms.CharField(widget=forms.TextInput(label="first_name"))
	last_name = forms.CharField(widget=forms.TextInput(label="last_name"))

	def user_created(sender, user, request, **kwargs):
		"""
		Called when user registers
		"""
		form = MyRegistrationForm(request.Post)
		user.first_name=form.data['first_name']
		user.last_name=form.data['last_name']
		user.save()

	user_registered.connect(user_created)