# 標準ライブラリ
import json
import logging
import os
from datetime import datetime

# サードパーティライブラリ
import markdown
import openai
import requests
from bs4 import BeautifulSoup

# Django関連モジュール
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
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
    messages = Message.objects.filter(group=group).order_by('-timestamp')[:50]
    
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
        'messages': reversed(messages),
        'days_since_creation': days_since_creation,
        'user_vote': user_vote,
        'is_vote_deadline_passed': is_vote_deadline_passed,
})

# URLから情報を取得する関数
def scrape_sleep_advice(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    advice_elements = soup.find_all('p')
    advice_texts = [element.get_text() for element in advice_elements if element.get_text()]
    return ' '.join(advice_texts)

# スクレイピング結果をファイルに保存
def save_advice_to_file(url, advice, filename='sleep_advice.json'):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            data = json.load(file)
    else:
        data = {}
    data[url] = advice
    with open(filename, 'w') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

# スクレイピング結果をファイルから読み込み
def load_advice_from_file(filename='sleep_advice.json'):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return json.load(file)
    return {}

# 今日のデータが既に存在するか確認
def check_today_data(user):
    today = localtime(timezone.now()).date()  # 日本時間で今日の日付を取得
    return SleepAdvice.objects.filter(user=user, created_at__date=today).exists()

# ビュー関数
@login_required
def feedback_chat(request):
    if GroupMember.objects.filter(user=request.user).exists():
        # グループに加入している場合
        advice = None

        if check_today_data(request.user):
            # 今日のデータが既にある場合
            return render(request, 'chat/feedback_chat.html', {'advice': '今日は回答済みです。'})

        if request.method == 'POST':
            url = request.POST.get('url')
            sleep_time = request.POST.get('sleep_time')
            wake_time = request.POST.get('wake_time')
            pre_sleep_activities = request.POST.get('pre_sleep_activities')

            # ローカルに保存されたアドバイスを確認
            saved_advice = load_advice_from_file()
            if url in saved_advice:
                scraped_info = saved_advice[url]
            else:
                scraped_info = scrape_sleep_advice(url)
                save_advice_to_file(url, scraped_info)
                saved_advice = load_advice_from_file()  # 再読み込み

            all_advice = " ".join([str(value) for value in saved_advice.values()])
            user_input = (
                f"ユーザーは{sleep_time}に寝て、{wake_time}に起きました。"
                f"寝る前は{pre_sleep_activities}をしていました。"
                f"以下の情報も評価やアドバイスの参考にしてください: {all_advice}"
                f"まず、これらの情報に基づいてユーザーの睡眠習慣に対する評価を簡潔に行ってください。"
                f"その後、その評価に基づいて、ユーザーにとって最も重要で実行可能なアドバイス3つを簡潔に提供してください。"
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
                sleep_time=sleep_time,
                wake_time=wake_time,
                pre_sleep_activities=pre_sleep_activities,
                advice=advice,
                topic_question = None,
            )

            return render(request, 'chat/feedback_chat.html', {'advice': html_advice})

        return render(request, 'chat/feedback_chat.html', {'advice': advice})

    else:
        # グループに加入していない場合
        advice = None
        
        if check_today_data(request.user):
            # 今日のデータが既にある場合
            return render(request, 'chat/pre_group_questions.html', {'advice': '今日は回答済みです。'})
        
        if request.method == 'POST':
            url = request.POST.get('url')
            sleep_time = request.POST.get('sleep_time')
            wake_time = request.POST.get('wake_time')
            pre_sleep_activities = request.POST.get('pre_sleep_activities')
            topic_question = request.POST.get('topic_question')  # トピック用の質問

            # ローカルに保存されたアドバイスを確認
            saved_advice = load_advice_from_file()
            if url in saved_advice:
                scraped_info = saved_advice[url]
            else:
                scraped_info = scrape_sleep_advice(url)
                save_advice_to_file(url, scraped_info)
                saved_advice = load_advice_from_file()  # 再読み込み

            all_advice = " ".join([str(value) for value in saved_advice.values()])
            user_input = (
                f"ユーザーは{sleep_time}に寝て、{wake_time}に起きました。"
                f"寝る前は{pre_sleep_activities}をしていました。"
                f"最近睡眠に関して取り組んだこと、取り組んでみたいことは{topic_question}です。"
                f"以下の情報も評価やアドバイスの参考にしてください: {all_advice}"
                f"まず、これらの情報に基づいてユーザーの睡眠習慣に対する評価を簡潔に行ってください。"
                f"その後、その評価に基づいて、ユーザーにとって最も重要で実行可能なアドバイス3つを簡潔に提供してください。"
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


            SleepAdvice.objects.create(
                user=request.user,
                sleep_time=sleep_time,
                wake_time=wake_time,
                pre_sleep_activities=pre_sleep_activities,
                advice=advice,
                topic_question = topic_question,
            )

            return render(request, 'chat/feedback_chat.html', {'advice': html_advice})

        return render(request, 'chat/pre_group_questions.html', {'advice': advice})

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

