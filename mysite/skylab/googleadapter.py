from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import render_to_response

from allauth.account.utils import user_email


class UniversityAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        email = sociallogin.account.extra_data['email'].lower()
        # print user_email(u)
        if not email.split('@')[1] == "up.edu.ph":
            raise ImmediateHttpResponse(render_to_response('auth/invalid_email.html'))
