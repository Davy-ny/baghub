from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import CustomUserCreationForm
from .models import User
from django.contrib.auth.decorators import login_required

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('login')

class RegisterView(CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('products:product_list')   # <-- add this line

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response
    
@login_required
def profile(request):
    if request.method == 'POST':
        request.user.phone_number = request.POST.get('phone_number')
        request.user.save()
        messages.success(request, 'Profile updated.')
        return redirect('accounts:profile')
    return render(request, 'accounts/profile.html', {'user': request.user})
