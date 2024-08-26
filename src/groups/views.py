import string
import random
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Group, GroupMember

# HTMLテンプレートをレンダリングするビュー
@login_required
def group_menu(request):
    # グループメニューのテンプレートをレンダリング
    return render(request, 'groups/group_menu.html')

@login_required
def group_management(request):
    # グループ管理のテンプレートをレンダリング
    return render(request, 'groups/group_management.html')

def generate_invite_code(length=8):
    # 招待コードを生成する関数
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

@login_required
def group_create(request):
    if request.method == 'POST':
        # グループ作成のリクエストを処理
        is_private = request.POST.get('is_private', False)
        invite_code = generate_invite_code() if is_private else None
        # 新しいグループを作成
        group = Group.objects.create(name='', is_private=is_private, invite_code=invite_code)
        # 現在のユーザーをグループメンバーとして追加
        GroupMember.objects.create(group=group, user=request.user)
        # グループメニューにリダイレクト
        return redirect('group_menu')
    # グループメニューのテンプレートをレンダリング
    return render(request, 'groups/group_menu.html')

@login_required
def group_join(request):
    if request.method == 'POST':
        # グループ参加のリクエストを処理
        invite_code = request.POST.get('invite_code', None)
        if invite_code:
            try:
                # 招待コードでグループを検索
                group = Group.objects.get(invite_code=invite_code)
                # 現在のユーザーをグループメンバーとして追加
                GroupMember.objects.create(group=group, user=request.user)
            except Group.DoesNotExist:
                # グループが存在しない場合の処理
                pass
        else:
            # ランダムで参加待ちのグループに参加
            group = Group.objects.filter(is_private=False).order_by('?').first()
            if group:
                # 現在のユーザーをグループメンバーとして追加
                GroupMember.objects.create(group=group, user=request.user)
        # グループメニューにリダイレクト
        return redirect('group_menu')
    # グループメニューのテンプレートをレンダリング
    return render(request, 'groups/group_menu.html')
