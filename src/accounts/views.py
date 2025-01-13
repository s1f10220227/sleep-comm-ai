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

        # プライバシーポリシーに同意しているか確認
        if not privacy_policy_checked:
            return render(request, 'accounts/signup.html', {
                'error_message': 'プライバシーポリシーに同意する必要があります。',
                'username': username, 'gender': gender, 'age': age
            })

        # ユーザーネームがすでに存在するか確認
        if CustomUser.objects.filter(username=username).exists():
            return render(request, 'accounts/signup.html', {
                'error_message': 'このユーザー名はすでに使用されています。',
                'username': username, 'gender': gender, 'age': age
            })

        if password == password_confirm:
            # 年齢が未回答の場合は None として扱う
            age = age if age else None
            # ユーザーを作成
            user = CustomUser.objects.create_user(
                username=username, password=password, gender=gender, age=age
            )
            user.save()
            return redirect('login')  # サインアップ成功後にログインページへリダイレクト
        else:
            return render(request, 'accounts/signup.html', {
                'error_message': 'パスワードが一致しません。',
                'username': username, 'gender': gender, 'age': age
            })
    return render(request, 'accounts/signup.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')  # ログイン成功後にホームへリダイレクト
        else:
            return render(request, 'accounts/login_signup.html', {
                'error_message': 'ログインに失敗しました。'
            })
    return render(request, 'accounts/login_signup.html')

def logout_view(request):
    logout(request)
    return redirect('home')

def privacy_policy(request):
    return render(request, 'accounts/privacy_policy.html')
