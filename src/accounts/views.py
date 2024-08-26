from django.shortcuts import render

def dashboard(request):
    return render(request, 'accounts/dashboard.html')

def login_signup(request):
    return render(request, 'accounts/login_signup.html')

def privacy_policy(request):
    return render(request, 'accounts/privacy_policy.html')

def profile(request):
    return render(request, 'accounts/profile.html')

def profile_edit(request):
    return render(request, 'accounts/profile_edit.html')