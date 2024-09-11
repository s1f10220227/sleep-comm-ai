from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from accounts.models import CustomUser

def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        privacy_policy_checked = request.POST.get('privacy_policy')

        # チェックボックスが選択されているか確認
        if not privacy_policy_checked:
            return render(request, 'accounts/signup.html', {'error_message': 'プライバシーポリシーに同意する必要があります。'})
        
        if password == password_confirm:
            # ユーザーを作成
            user = CustomUser.objects.create_user(username=username, password=password)
            user.save()
            return redirect('login')  # サインアップ成功後にログインページへリダイレクト
        else:
            return render(request, 'accounts/signup.html', {'error_message': 'パスワードが一致しません。'})
    return render(request, 'accounts/signup.html')

def home(request):
    return render(request, 'accounts/home.html')

def login_view(request):
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

def logout_view(request):
    logout(request)
    return redirect('home')

def privacy_policy(request):
    return render(request, 'accounts/privacy_policy.html')

@login_required
def profile(request):
    return render(request, 'accounts/profile.html')
