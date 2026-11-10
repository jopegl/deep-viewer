from django.shortcuts import render
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.views import redirect_to_login
from django.http import Http404
from django.shortcuts import redirect
from .forms import SignUpForm, ProfileForm
from django.shortcuts import render

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .services.institutions import search_institutions

@login_not_required
def landing(request):
    if request.user.is_authenticated:
        return redirect("project_list")
    return render(request, "landing.html")


@login_not_required
def admin_redirect(request):
    if not request.user.is_authenticated:
        return redirect_to_login(request.GET.get("next", "/admin/"))
    if request.user.is_staff:
        return redirect("admin:index")
    raise Http404



@login_not_required
def admin_login(request):
    if not request.user.is_authenticated:
        return redirect_to_login(request.GET.get("next", "/admin/"))
    if request.user.is_staff:
        return redirect("admin:index")
    raise Http404

@login_not_required
@require_GET
def institution_search(request):
    return JsonResponse({"results": search_institutions(request.GET.get("q", ""))})


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')

class ProfileView(LoginRequiredMixin, UpdateView):
    form_class = ProfileForm
    template_name = "accounts/profile.html"
    success_url = reverse_lazy("profile")

    def get_object(self):
        return self.request.user
