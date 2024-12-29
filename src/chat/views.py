# 標準ライブラリ
import logging
from datetime import datetime, date, timedelta

# サードパーティライブラリ
import markdown
import openai

# Django関連モジュール
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import localtime
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

# アプリケーション固有のモジュール
from .models import Message, Mission, MissionOption, SleepAdvice, Vote
from groups.models import Group, GroupMember

# ロガー設定
logger = logging.getLogger(__name__)

# settings.pyで定義した環境変数OPENAI_API_KEY, OPENAI_API_BASEを参照する
OPENAI_API_KEY = settings.OPENAI_API_KEY
OPENAI_API_BASE = settings.OPENAI_API_BASE

# AIモデルの初期化
chat = openai.ChatCompletion

@login_required
def room(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    group_members = GroupMember.objects.filter(group=group)
    chat_messages = Message.objects.filter(group=group).order_by('-timestamp')[:50]
    
    # AIアシスタントユーザーの取得または作成
    User = get_user_model()
    ai_user, created = User.objects.get_or_create(username='AI Assistant')

    # AIアシスタントがグループのメンバーか確認し、いなければ追加
    if not group_members.filter(user=ai_user).exists():
        GroupMember.objects.create(group=group, user=ai_user)

    # 最新のミッションを取得
    latest_mission = Mission.objects.filter(group=group).order_by('-created_at').first()
    mission_options = MissionOption.objects.filter(group=group).order_by('-votes', 'id')
    for option in mission_options:
        logger.debug(f"generated mission option: {option.text}")
    has_mission_options = mission_options.exists()
    mission_confirmed = latest_mission.confirmed if latest_mission else False

    # ユーザーの最新の投票データを取得
    user_vote = Vote.objects.filter(user=request.user, group=group).first()

    # 投票締め切りを過ぎているかどうかを計算
    if group.vote_deadline:
        is_vote_deadline_passed = timezone.now() > group.vote_deadline
    else:
        is_vote_deadline_passed = False # 投票開始前

    # ミッション生成からの日数を計算
    if latest_mission:
        days_since_creation = (localtime(timezone.now()).date() - localtime(latest_mission.created_at).date()).days
        logger.debug(f"localtime(timezone.now()).date() {localtime(timezone.now()).date()}")
        logger.debug(f"localtime(latest_mission.created_at).date() {localtime(latest_mission.created_at).date()}")
        logger.debug(f"localtime(timezone.now()).date() - localtime(latest_mission.created_at).date() = {localtime(timezone.now()).date() - localtime(latest_mission.created_at).date()}")
        logger.debug(f"生成日計算: {days_since_creation}")
    else:
        days_since_creation = '?'  # ミッションが存在しない場合は?日
        logger.debug(f"生成日計算: {days_since_creation}")

    return render(request, 'chat/room.html', {
        'mission_options': mission_options,
        'has_mission_options': has_mission_options,
        'group': group,
        'mission': latest_mission,
        'mission_confirmed': mission_confirmed,
        'group_members': group_members,
        'chat_messages': reversed(chat_messages),
        'days_since_creation': days_since_creation,
        'user_vote': user_vote,
        'is_vote_deadline_passed': is_vote_deadline_passed,
})

# AIモデルの初期化
chat = openai.ChatCompletion

# 今日のデータが既に存在するか確認
def check_today_data(user):
    today = localtime(timezone.now()).date()  # 日本時間で今日の日付を取得
    return SleepAdvice.objects.filter(user=user, created_at__date=today).exists()

# ビュー関数
@login_required
def sleep_q(request):
    if GroupMember.objects.filter(user=request.user).exists():
        # グループに加入している場合
        group_member = GroupMember.objects.get(user=request.user)
        group = group_member.group

        # 最新のミッションを取得
        latest_mission = Mission.objects.filter(group=group).order_by('-created_at').first()
        mission_text = latest_mission.mission if latest_mission else "設定されていません"

        advice = None

        if check_today_data(request.user):
            # 今日のデータが既にある場合
            return render(request, 'chat/sleep_q.html', {'advice': '今日は回答済みです'})

        if request.method == 'POST':
            sleep_time = request.POST.get('sleep_time')
            wake_time = request.POST.get('wake_time')
            sleep_quality = request.POST.get('sleep_quality')
            pre_sleep_activities = request.POST.get('pre_sleep_activities')
            mission_achievement = request.POST.get('mission_achievement')

            # ミッション作成以来の履歴データを取得
            mission_creation_date = latest_mission.created_at if latest_mission else None
            historical_data = SleepAdvice.objects.filter(
                user=request.user,
                created_at__gte=mission_creation_date
            ).order_by('created_at')

            # 睡眠時間をdatetime.timeオブジェクトに変換
            sleep_time_obj = datetime.strptime(sleep_time, '%H:%M').time()
            wake_time_obj = datetime.strptime(wake_time, '%H:%M').time()

            # 今日の睡眠時間を計算
            sleep_datetime = datetime.combine(date.today(), sleep_time_obj)
            wake_datetime = datetime.combine(date.today(), wake_time_obj)
            if wake_datetime < sleep_datetime:
                wake_datetime += timedelta(days=1)
            today_sleep_duration = wake_datetime - sleep_datetime

            # トレンドメッセージを初期化
            sleep_duration_trend = "データなし"
            sleep_quality_trend = "データなし"
            mission_achievement_trend = "データなし"
            trend_analysis = "まだ十分なデータがないため、傾向分析はできません。"

            # 傾向分析を行うための履歴データがある場合のみ
            sleep_durations = [entry.sleep_duration for entry in historical_data if entry.sleep_duration]
            sleep_qualities = [entry.sleep_quality for entry in historical_data if entry.sleep_quality]
            mission_achievements = [entry.mission_achievement for entry in historical_data if entry.mission_achievement]

            # 睡眠時間の傾向を計算
            if sleep_durations:
                sleep_duration_trend = "増加傾向" if today_sleep_duration > sleep_durations[-1] else "減少傾向"
                trend_analysis = f"過去{len(sleep_durations)}日間のデータに基づく分析："

            # 睡眠休養感の傾向を計算
            if sleep_qualities:
                sleep_quality_trend = "改善傾向" if int(sleep_quality) > sleep_qualities[-1] else "悪化傾向"

            # ミッション達成度の傾向を計算
            if mission_achievements:
                mission_achievement_trend = "向上傾向" if int(mission_achievement) > mission_achievements[-1] else "低下傾向"

            user_input = (
                f"以下の情報に基づいて睡眠アドバイスを簡潔に提供してください：\n\n"
                f"1. 本日の睡眠状況：\n"
                f"- 就寝時刻：{sleep_time}\n"
                f"- 起床時刻：{wake_time}\n"
                f"- 睡眠時間：{today_sleep_duration.total_seconds() / 3600:.1f}時間\n"
                f"- 睡眠休養感：{dict(SleepAdvice.SLEEP_QUALITY_CHOICES)[int(sleep_quality)]}\n"
                f"- 就寝前の活動：{pre_sleep_activities}\n"
                f"- 現在のミッション：{mission_text}\n\n"
                f"2. {trend_analysis}\n"
            )

            # 履歴データがある場合のみ傾向情報を追加
            if len(historical_data) > 0:
                user_input += (
                    f"- 睡眠時間の傾向：{sleep_duration_trend}\n"
                    f"- 睡眠休養感の傾向：{sleep_quality_trend}\n"
                    f"- ミッション達成度の傾向：{mission_achievement_trend}\n"
                )
            else:
                user_input += "※ まだ過去のデータがないため、傾向分析はできません。本日のデータのみに基づいてアドバイスを簡潔に提供してください。\n"

            user_input += (
                f"- 本日のミッション達成度：{dict(SleepAdvice.MISSION_ACHIEVEMENT_CHOICES)[int(mission_achievement)]}\n\n"
                f"これらの情報を総合的に分析し、以下の構成でアドバイスを簡潔に提供してください：\n"
                f"1. 現状の睡眠パターンの評価\n"
                f"2. 改善が必要な点\n"
                f"3. 上記の改善点に対して、ミッション「{mission_text}」を活用した1つのアクションプラン\n\n"
                f"※ アクションプランは、特定された改善点に対して、現在のミッションをどのように活用できるかという観点で簡潔に提案してください。\n"
                f"※ トレンドデータがない場合は、本日のデータのみに基づいてアドバイスを簡潔に提供してください。"
            )

            # OpenAI APIでアドバイスを取得
            response = chat.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a sleep expert who provides advice on healthy sleep habits."},
                    {"role": "user", "content": user_input}
                ],
                api_key=OPENAI_API_KEY,
                api_base=OPENAI_API_BASE
            )

            advice = response['choices'][0]['message']['content']
            html_advice = markdown.markdown(advice)  # markdownをHTMLに変換

            # 睡眠データをデータベースに保存
            SleepAdvice.objects.create(
                user=request.user,
                sleep_time=sleep_time_obj,
                wake_time=wake_time_obj,
                sleep_quality=sleep_quality,
                pre_sleep_activities=pre_sleep_activities,
                advice=advice,
                topic_question=None,
                mission_achievement=mission_achievement,
            )

            return redirect('/progress/progress_check/')

        return render(request, 'chat/sleep_q.html', {
            'advice': advice,
            'mission_text': mission_text})

    else:
        # グループに加入していない場合
        advice = None

        if check_today_data(request.user):
            # 今日のデータが既にある場合
            return render(request, 'chat/pre_sleep_q.html', {'advice': '今日は回答済みです'})

        if request.method == 'POST':
            sleep_time = request.POST.get('sleep_time')
            wake_time = request.POST.get('wake_time')
            sleep_quality = request.POST.get('sleep_quality')
            pre_sleep_activities = request.POST.get('pre_sleep_activities')
            topic_question = request.POST.get('topic_question')

            # 睡眠時間をdatetime.timeオブジェクトに変換
            sleep_time_obj = datetime.strptime(sleep_time, '%H:%M').time()
            wake_time_obj = datetime.strptime(wake_time, '%H:%M').time()

            # 今日の睡眠時間を計算
            sleep_datetime = datetime.combine(date.today(), sleep_time_obj)
            wake_datetime = datetime.combine(date.today(), wake_time_obj)
            if wake_datetime < sleep_datetime:
                wake_datetime += timedelta(days=1)
            today_sleep_duration = wake_datetime - sleep_datetime

            # 過去1週間のデータを取得
            week_ago = datetime.now() - timedelta(days=7)
            historical_data = SleepAdvice.objects.filter(
                user=request.user,
                created_at__gte=week_ago
            ).order_by('created_at')

            # トレンドメッセージを初期化
            sleep_duration_trend = "データなし"
            sleep_quality_trend = "データなし"
            trend_analysis = "まだ十分なデータがないため、傾向分析はできません。"

            # 傾向分析を行うための履歴データがある場合のみ
            sleep_durations = [entry.sleep_duration for entry in historical_data if entry.sleep_duration]
            sleep_qualities = [entry.sleep_quality for entry in historical_data if entry.sleep_quality]

            # 睡眠時間の傾向を計算
            if sleep_durations:
                sleep_duration_trend = "増加傾向" if today_sleep_duration > sleep_durations[-1] else "減少傾向"
                trend_analysis = f"過去{len(sleep_durations)}日間のデータに基づく分析："

            # 睡眠休養感の傾向を計算
            if sleep_qualities:
                sleep_quality_trend = "改善傾向" if int(sleep_quality) > sleep_qualities[-1] else "悪化傾向"

            user_input = (
                f"以下の情報に基づいて睡眠アドバイスを簡潔に提供してください：\n\n"
                f"1. 本日の睡眠状況：\n"
                f"- 就寝時刻：{sleep_time}\n"
                f"- 起床時刻：{wake_time}\n"
                f"- 睡眠時間：{today_sleep_duration.total_seconds() / 3600:.1f}時間\n"
                f"- 睡眠休養感：{dict(SleepAdvice.SLEEP_QUALITY_CHOICES)[int(sleep_quality)]}\n"
                f"- 就寝前の活動：{pre_sleep_activities}\n"
                f"- 睡眠改善のために取り組みたいこと：{topic_question}\n\n"
                f"2. {trend_analysis}\n"
            )

            # 履歴データがある場合のみ傾向情報を追加
            if len(historical_data) > 0:
                user_input += (
                    f"- 睡眠時間の傾向：{sleep_duration_trend}\n"
                    f"- 睡眠休養感の傾向：{sleep_quality_trend}\n"
                )
            else:
                user_input += "※ まだ過去のデータがないため、傾向分析はできません。本日のデータのみに基づいてアドバイスを簡潔に提供してください。\n"

            user_input += (
                f"\nこれらの情報を総合的に分析し、以下の構成でアドバイスを簡潔に提供してください：\n"
                f"1. 現状の睡眠パターンの評価\n"
                f"2. 改善が必要な点\n"
                f"3. 具体的な改善のための1つのアクションプラン\n"
            )

            # OpenAI APIでアドバイスを取得
            response = chat.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a sleep expert who provides advice on healthy sleep habits."},
                    {"role": "user", "content": user_input}
                ],
                api_key=OPENAI_API_KEY,
                api_base=OPENAI_API_BASE
            )

            advice = response['choices'][0]['message']['content']
            html_advice = markdown.markdown(advice)  # markdownをHTMLに変換

            # 睡眠データをデータベースに保存
            SleepAdvice.objects.create(
                user=request.user,
                sleep_time=sleep_time_obj,
                wake_time=wake_time_obj,
                sleep_quality=sleep_quality,
                pre_sleep_activities=pre_sleep_activities,
                advice=advice,
                topic_question=topic_question,
            )

            return redirect('/progress/progress_check/')

        return render(request, 'chat/pre_sleep_q.html', {'advice': advice})

@login_required
def create_missions(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    group_members = GroupMember.objects.filter(group=group)
    latest_topics = []
    for member in group_members:
        latest_advice = SleepAdvice.objects.filter(user=member.user, topic_question__isnull=False).order_by('-created_at').first()
        if latest_advice:
            latest_topics.append(latest_advice.topic_question)

    combined_topics = "。".join(latest_topics)
    prompt = (
        f"以下は、これから取り組みたい睡眠に関するトピックです：{combined_topics}。\n\n"
        "これらを元に、全員に共通する改善点や挑戦できるミッションを5つ、生成してください。\n"
        "ミッションは以下の条件を満たすようにしてください：\n"
        "1. 全員が実行可能であること。\n"
        "2. 睡眠に関する具体的な内容であること。\n"
        "3. 各ミッションは20文字程度で簡潔に表現すること。\n\n"
        "以下のフォーマットに従って、改行で区切ったリスト形式で出力してください：\n"
        "ミッション1\n"
        "ミッション2\n"
        "ミッション3\n"
        "ミッション4\n"
        "ミッション5\n\n"
        "フォーマットを厳守し、必ず改行区切りで出力してください。"
    )

    try:
        response = chat.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a sleep expert who generates collaborative missions based on multiple user inputs."},
                {"role": "user", "content": prompt}
            ],
            api_key=OPENAI_API_KEY,
            api_base=OPENAI_API_BASE
        )
        mission_texts = response['choices'][0]['message']['content'].split("\n")  # 複数行で返されると仮定

        for mission_text in mission_texts:
            if mission_text.strip():  # 空白行を除外
                MissionOption.objects.create(
                    group=group,
                    text=mission_text.strip()
                )

        # 投票締切時刻を現在時刻 + 2時間に設定
        group.vote_deadline = localtime(timezone.now()) + timezone.timedelta(hours=2)
        group.save()

    except Exception as e:
        logger.error(f"Error generating missions: {e}")
        return redirect(reverse('room', args=[group_id]))

    return redirect(reverse('room', args=[group_id]))

@login_required
def vote_mission(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    selected_option_id = request.POST.get("selected_mission")

    # 選択肢が選ばれていない、または無効な場合の処理
    if not selected_option_id:
        messages.error(request, "ミッションを選択してください。")
        return redirect(reverse('room', args=[group_id]))

    try:
        selected_option = MissionOption.objects.get(id=selected_option_id, group=group)
    except MissionOption.DoesNotExist:
        messages.error(request, "選択したミッションが無効です。")
        return redirect(reverse('room', args=[group_id]))

    # ユーザーの現在の投票を確認
    existing_vote = Vote.objects.filter(user=request.user, group=group).first()

    if existing_vote:
        current_option = existing_vote.mission_option
        if current_option != selected_option:
            # 現在の投票を取り消し
            current_option.votes -= 1
            current_option.save()

            # 新たな投票に変更
            existing_vote.mission_option = selected_option
            existing_vote.save()

            # 新しい投票先の票数を更新
            selected_option.votes += 1
            selected_option.save()
    else:
        # 新しい投票を登録
        Vote.objects.create(user=request.user, mission_option=selected_option, group=group)

        # 新しい投票先の票数を更新
        selected_option.votes += 1
        selected_option.save()

    # 全員が投票を完了したか確認
    if check_all_votes_completed(group):
        # 最も多い票数の選択肢を取得
        top_voted_option = MissionOption.objects.filter(group=group).order_by('-votes', '?').first()

        # ミッションを確定
        if top_voted_option and not Mission.objects.filter(group=group, confirmed=True).exists():
            Mission.objects.create(
                mission=top_voted_option.text,
                group=group,
                confirmed=True
            )

            MissionOption.objects.filter(group=group).delete()

    return redirect(reverse('room', args=[group_id]))

@login_required
def confirm_mission(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.method == 'POST':
        # 最新のミッションを取得
        latest_mission = Mission.objects.filter(group=group).order_by('-created_at').first()

        if latest_mission:
            latest_mission.confirmed = True
            latest_mission.save()
        # 確認後、同じページへリダイレクト
        return redirect(reverse('room', args=[group_id]))

def check_all_votes_completed(group):
    total_members = group.members.count()
    total_votes = Vote.objects.filter(group=group).count()
    return total_votes == total_members - 1 # AI Assistantは投票しないため-1

@login_required
def finalize_mission(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    top_voted_option = MissionOption.objects.filter(group=group).order_by('-votes', '?').first()
    # ミッションを確定
    if top_voted_option and not Mission.objects.filter(group=group, confirmed=True).exists():
        Mission.objects.create(
            mission=top_voted_option.text,
            group=group,
            confirmed=True
        )
        MissionOption.objects.filter(group=group).delete()
    return redirect(reverse('room', args=[group_id]))

@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def save_mission(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    group_members = GroupMember.objects.filter(group=group)
    messages = Message.objects.filter(group=group).order_by('-timestamp')[:50]
    # 最新のミッションを取得
    latest_mission = Mission.objects.filter(group=group).order_by('-created_at').first()
    no_mission_text = "ミッションを生成しましょう"
    mission_confirmed = latest_mission.confirmed if latest_mission else False

    if request.method == 'POST':
        # ユーザーがテキストボックスを含むフォームを提出した場合の処理
        mission_text = request.POST.get('mission')
        if mission_text: #ミッションテキストがある場合の処理
            Mission.objects.create(mission=mission_text, group=group)
            return redirect(reverse('room', args=[group_id]))
        else:
            # show_textbox=Trueにしてテキストボックスを表示
            return render(request, 'chat/room.html', {
                'mission': latest_mission.mission if latest_mission else no_mission_text,
                'group': group,
                'mission_confirmed': mission_confirmed,
                'group_members': group_members,
                'messages': reversed(messages),
                'show_textbox': True,
            })
    return redirect(reverse('room', args=[group_id]))
