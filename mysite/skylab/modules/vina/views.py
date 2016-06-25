from django.views.generic import TemplateView, FormView
from skylab.modules.vina.forms import VinaBasicForm, VinaAdvancedForm


class VinaView(TemplateView):
    template_name = "modules/vina/use_vina.html"

    def get_context_data(self, **kwargs):
        context = super(VinaView, self).get_context_data(**kwargs)
        context['vina_basic_form'] = VinaBasicForm()
        context['vina_advanced_form'] = VinaAdvancedForm()
        context['user'] = self.request.user
        return context

    def post(self, request, *args, **kwargs):
        pass


class VinaSplitView(FormView):
    pass
