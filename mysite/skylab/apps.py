from __future__ import unicode_literals

from django.apps import AppConfig


class SkylabConfig(AppConfig):
    name = 'skylab'

    def ready(self):
        import skylab.signals
