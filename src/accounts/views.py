from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
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
            return redirect('login_signup')  # サインアップ成功後にログインページへリダイレクト
        else:
            return render(request, 'accounts/signup.html', {'error_message': 'パスワードが一致しません。'})
    return render(request, 'accounts/signup.html')

# サインアップのビューです。POSTリクエストを受け取った際に、
# ユーザー名、パスワード、パスワード確認、プライバシーポリシーの同意チェックを処理します。
# パスワードが一致し、プライバシーポリシーが同意されていればユーザーを作成し、
# ログインページにリダイレクトします。エラーがあれば、再度サインアップページを表示します。

def dashboard(request):
    return render(request, 'accounts/dashboard.html')

# ダッシュボードページのビューです。特に追加の処理はなく、
# 単に`accounts/dashboard.html`テンプレートを表示します。

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

# ログインとサインアップのページに対応するビューです。
# POSTリクエストの場合、認証を試み、成功すればプロフィールページにリダイレクト、
# 失敗すればエラーメッセージを表示します。

def privacy_policy(request):
    return render(request, 'accounts/privacy_policy.html')

# プライバシーポリシーページのビューです。単に`accounts/privacy_policy.html`テンプレートを表示します。

def profile(request):
    return render(request, 'accounts/profile.html')

# プロフィールページのビューです。特に追加の処理はなく、
# 単に`accounts/profile.html`テンプレートを表示します。
