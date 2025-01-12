import string
import random
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.core.exceptions import ValidationError
from .models import Group, GroupMember
from chat.models import Message, Mission, SleepAdvice, Vote
from chat.views import check_today_data

# HTMLテンプレートをレンダリングするビュー
def home(request):
    # ユーザーが認証されているか確認
    if request.user.is_authenticated:
        # ユーザーが既にグループに参加しているか確認
        if GroupMember.objects.filter(user=request.user).exists():
            # 参加しているグループの情報を取得
            group_member = GroupMember.objects.get(user=request.user)
            group = group_member.group
            members = GroupMember.objects.filter(group=group)
            mission = Mission.objects.filter(group=group).order_by('-created_at').first()
            # 最新のメッセージを取得
            latest_message = Message.objects.filter(group=group).order_by('-timestamp').first()
            # パブリックグループとメンバーの一覧を取得（最大10件）
            groups = Group.objects.filter(is_private=False).exclude(id=group.id)[:10]
            group_members = {g.id: GroupMember.objects.filter(group=g) for g in groups}
            group_missions = {g.id: Mission.objects.filter(group=g).order_by('-created_at').first() for g in groups}
            has_answered_today = check_today_data(request.user)

            response_data = {
                'group': group,
                'members': members,
                'mission': mission,
                'is_member': True,
                'latest_message': latest_message,
                'groups': groups,
                'group_members': group_members,
                'group_missions': group_missions,
                'has_answered_today': has_answered_today
            }

            # 今日の質問に回答済みの場合、回答を取得
            if has_answered_today:
                answer = SleepAdvice.objects.filter(user=request.user).order_by('-created_at').first()

                # 睡眠時間を時間と分に変換
                total_seconds = answer.sleep_duration.total_seconds()
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)

                # 時間計算の結果を追加
                answer.hours = hours
                answer.minutes = minutes

                response_data['answer'] = answer

            # グループ情報と最新のメッセージ、他のグループとメンバーの一覧を含むテンプレートをレンダリング
            return render(request, 'groups/home.html', response_data)
        else:
            # パブリックグループとメンバーの一覧を取得（最大10件）
            groups = Group.objects.filter(is_private=False)[:10]
            group_members = {g.id: GroupMember.objects.filter(group=g) for g in groups}
            group_missions = {g.id: Mission.objects.filter(group=g).order_by('-created_at').first() for g in groups}
            has_answered_today = check_today_data(request.user)

            response_data = {
                'is_member': False,
                'groups': groups,
                'group_members': group_members,
                'group_missions': group_missions,
                'has_answered_today': has_answered_today
            }

            # 今日の質問に回答済みの場合、回答を取得
            if has_answered_today:
                answer = SleepAdvice.objects.filter(user=request.user).order_by('-created_at').first()
                response_data['answer'] = answer

            # グループメニューのテンプレートをレンダリング
            return render(request, 'groups/home.html', response_data)
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
        # 既に参加前の質問に回答しているかどうか確認
        if not check_today_data(request.user):
            return redirect('sleep_q')
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
        # 既に参加前の質問に回答しているかどうか確認
        if not check_today_data(request.user):
            return redirect('sleep_q')
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
                if group.is_join_closed:
                    # 参加締め切りの場合の処理
                    return redirect('home')
                try:
                    # 現在のユーザーをグループメンバーとして追加
                    GroupMember.objects.create(group=group, user=request.user)
                except ValidationError:
                    # 既にメンバーが5人いる場合の処理
                    pass
            except Group.DoesNotExist:
                # グループが存在しない場合の処理
                pass
        else:
            # メンバーが5人未満のグループにランダム参加
            group = Group.objects.filter(is_private=False, is_join_closed=False).annotate(member_count=Count('members')).filter(member_count__lt=6).order_by('?').first()
            if group and group.member_count < 6:
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

            # ユーザーの投票を取得
            existing_vote = Vote.objects.filter(user=request.user, group=group).first()

            if existing_vote:
                # 投票されている選択肢の票数を減らす
                existing_vote.mission_option.votes -= 1
                existing_vote.mission_option.save()

                # ユーザーの投票を削除
                existing_vote.delete()

            # グループメンバーシップを削除
            group_member.delete()

            # グループの人数をチェックし、1人以下ならグループを削除
            if GroupMember.objects.filter(group=group).count() <= 1:
                group.delete()
        except GroupMember.DoesNotExist:
            # ユーザーがグループに参加していない場合の処理
            pass
        # ホームにリダイレクト
        return redirect('home')
    # グループメニューのテンプレートをレンダリング
    return render(request, 'groups/home.html')
