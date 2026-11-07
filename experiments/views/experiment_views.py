from django.shortcuts import render
from django.http import HttpRequest
from django.views.generic import *
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from ..forms.project_forms import *

