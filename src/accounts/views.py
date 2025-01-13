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
        gender = request.POST.get('gender')
        age = request.POST.get('age')

        # プライバシーポリシーの確認
        if not privacy_policy_checked:
            return render(request, 'accounts/signup.html', {
                'error_message': 'プライバシーポリシーへの同意が必要です。サービスをご利用いただくために、プライバシーポリシーをご確認の上、チェックボックスにチェックを入れてください。',
                'username': username,
                'gender': gender,
                'age': age
            })

        if CustomUser.objects.filter(username=username).exists():
            return render(request, 'accounts/signup.html', {
                'error_message': 'このユーザー名は既に使用されています。別のユーザー名を選択してください。',
                'username': username,
                'gender': gender,
                'age': age
            })

        if password != password_confirm:
            return render(request, 'accounts/signup.html', {
                'error_message': 'パスワードが一致しません。パスワードをもう一度入力してください。',
                'username': username,
                'gender': gender,
                'age': age
            })

        try:
            # 年齢が未回答の場合は None として扱う
            age = age if age else None
            # ユーザーを作成
            user = CustomUser.objects.create_user(
                username=username,
                password=password,
                gender=gender,
                age=age
            )
            user.save()
            return redirect('login')
        except Exception as e:
            return render(request, 'accounts/signup.html', {
                'error_message': 'アカウント作成中にエラーが発生しました。もう一度お試しください。',
                'username': username,
                'gender': gender,
                'age': age
            })

    return render(request, 'accounts/signup.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            return render(request, 'accounts/login.html', {
                'error_message': 'ユーザー名とパスワードを入力してください。'
            })

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'accounts/login.html', {
                'error_message': 'ユーザー名またはパスワードが正しくありません。もう一度確認してください。'
            })
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

def privacy_policy(request):
    return render(request, 'accounts/privacy_policy.html')
