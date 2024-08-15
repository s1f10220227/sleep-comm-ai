from django.shortcuts import render

def login_signup(request):
    return render(request, 'accounts/login_signup.html')

def privacy_policy(request):
    return render(request, 'accounts/privacy_policy.html')
