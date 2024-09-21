import string
import random
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Group, GroupMember

# HTMLテンプレートをレンダリングするビュー
def home(request):
    # ユーザーが認証されているか確認
    if request.user.is_authenticated:
        # ユーザーが既にグループに参加しているか確認
        if GroupMember.objects.filter(user=request.user).exists():
            # 参加しているグループの情報を取得
            group_member = GroupMember.objects.get(user=request.user)
            group = group_member.group
            # グループ情報を含むテンプレートをレンダリング
            return render(request, 'groups/home.html', {'group': group, 'is_member': True})
        else:
            # グループメニューのテンプレートをレンダリング
            return render(request, 'groups/home.html', {'is_member': False})
    else:
        # ユーザーが認証されていない場合
        return render(request, 'groups/home.html')

# 招待コードを生成する関数
def generate_invite_code(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

# グループ作成のビュー
@login_required
def group_create(request):
    if request.method == 'POST':
        # ユーザーが既にグループに参加しているか確認
        if GroupMember.objects.filter(user=request.user).exists():
            # 既に参加している場合はグループメニューにリダイレクト
            return redirect('home')

        # グループ作成のリクエストを処理
        is_private = request.POST.get('is_private') == "on"
        invite_code = generate_invite_code() if is_private else None
        # 新しいグループを作成
        group = Group.objects.create(is_private=is_private, invite_code=invite_code)
        # 現在のユーザーをグループメンバーとして追加
        GroupMember.objects.create(group=group, user=request.user)
        # ホームにリダイレクト
        return redirect('home')
    # ホームのテンプレートをレンダリング
    return render(request, 'groups/home.html')

# グループ参加のビュー
@login_required
def group_join(request):
    if request.method == 'POST':
        # ユーザーが既にグループに参加しているか確認
        if GroupMember.objects.filter(user=request.user).exists():
            # 既に参加している場合はホームにリダイレクト
            return redirect('home')

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
        # ホームにリダイレクト
        return redirect('home')
    # グループメニューのテンプレートをレンダリング
    return render(request, 'groups/home.html')


# グループ離脱のビュー
@login_required
def group_leave(request):
    if request.method == 'POST':
        try:
            # 現在のユーザーのグループメンバーシップを取得
            group_member = GroupMember.objects.get(user=request.user)
            group = group_member.group
            # グループメンバーシップを削除
            group_member.delete()
            # グループの人数をチェックし、0人ならグループを削除
            if not GroupMember.objects.filter(group=group).exists():
                group.delete()
        except GroupMember.DoesNotExist:
            # ユーザーがグループに参加していない場合の処理
            pass
        # ホームにリダイレクト
        return redirect('home')
    # グループメニューのテンプレートをレンダリング
    return render(request, 'groups/home.html')
