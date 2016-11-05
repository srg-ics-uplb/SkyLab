from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib import messages
from django.shortcuts import render


class UniversityAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):  # before social auth
        email = sociallogin.account.extra_data['email'].lower()
        # print user_email(u)

        if not email.split('@')[1] == "up.edu.ph":
            messages.add_message(request, messages.ERROR, 'You need to login using an @up.edu.ph account. NOTE: Your account is still logged in with Google.',
                                 extra_tags='display_this')
            raise ImmediateHttpResponse(render(request, 'layouts/home.html'))
