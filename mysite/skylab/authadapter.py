from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class UniversityAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):  # before social auth
        email = sociallogin.account.extra_data['email'].lower()
        # print user_email(u)
        # TODO: uncomment
        # if not email.split('@')[1] == "up.edu.ph":
        #     raise ImmediateHttpResponse(render_to_response('auth/invalid_email.html'))

