from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User

def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        privacy_policy_checked = request.POST.get('privacy_policy')

        # チェックボックスが選択されているか確認
        if not privacy_policy_checked:
            return render(request, 'accounts/signup.html', {'error_message': 'プライバシーポリシーに同意する必要があります。'})
        
        if password == password_confirm:
            # ユーザーを作成
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                email=email
            )
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
