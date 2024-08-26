from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login

def dashboard(request):
    return render(request, 'accounts/dashboard.html')

def login_signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('privacy_policy')
        else:
            # ログイン失敗時にエラーメッセージを渡す
            return render(request, 'accounts/login_signup.html', {'error_message': 'ログインに失敗しました。'})
    return render(request, 'accounts/login_signup.html')

def privacy_policy(request):
    return render(request, 'accounts/privacy_policy.html')

def profile(request):
    return render(request, 'accounts/profile.html')