from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login

#追加
from django.contrib.auth.models import User
def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        if password == password_confirm:
            # ユーザーを作成
            user = User.objects.create_user(username=username, password=password)
            user.save()
            return redirect('login_signup')  # サインアップ成功後にログインページへリダイレクト
        else:
            return render(request, 'accounts/signup.html', {'error_message': 'パスワードが一致しません。'})
    return render(request, 'accounts/signup.html')


def dashboard(request):
    return render(request, 'accounts/dashboard.html')

def login_signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('profile')  # ログイン成功後にプロフィールページにリダイレクト
        else:
            # ログイン失敗時にエラーメッセージを渡す
            return render(request, 'accounts/login_signup.html', {'error_message': 'ログインに失敗しました。'})
    return render(request, 'accounts/login_signup.html')

def privacy_policy(request):
    return render(request, 'accounts/privacy_policy.html')

def profile(request):
    return render(request, 'accounts/profile.html')
