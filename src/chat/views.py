import os

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from groups.models import Group, GroupMember
from .models import Message

import json
from django.http import JsonResponse
import openai
import requests
from bs4 import BeautifulSoup
from django.utils import timezone
from django.utils.timezone import localtime
from .models import SleepAdvice

from .models import Mission
from datetime import datetime

@login_required
def room(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    group_members = GroupMember.objects.filter(group=group)
    messages = Message.objects.filter(group=group).order_by('-timestamp')[:50]
     # 最新のミッションを取得
    latest_mission = Mission.objects.order_by('-mission_time').first()
    no_mission_text = "ミッションを生成しましょう"

    return render(request, 'chat/room.html', {
        'mission': latest_mission.mission if latest_mission else no_mission_text,
        'group': group,
        'group_members': group_members,
        'messages': reversed(messages),
})

# APIキーとベースURLを設定
OPENAI_API_BASE = 'https://api.openai.iniad.org/api/v1'

# AIモデルの初期化
chat = openai.ChatCompletion

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
            # 睡眠データをデータベースに保存
            SleepAdvice.objects.create(
                user=request.user,
                sleep_time=sleep_time,
                wake_time=wake_time,
                pre_sleep_activities=pre_sleep_activities,
                advice=advice,
                topic_question = None,
            )

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

            SleepAdvice.objects.create(
                user=request.user,
                sleep_time=sleep_time,
                wake_time=wake_time,
                pre_sleep_activities=pre_sleep_activities,
                advice=advice,
                topic_question = topic_question,
            )

        return render(request, 'chat/pre_group_questions.html', {'advice': advice})

@login_required
def create_mission(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    group_members = GroupMember.objects.filter(group=group)
    messages = Message.objects.filter(group=group).order_by('-timestamp')[:50]
    
    # 各メンバーの最新のトピック質問を取得
    latest_topics = []
    for member in group_members:
        latest_advice = SleepAdvice.objects.filter(user=member.user, topic_question__isnull=False).order_by('-created_at').first()
        if latest_advice:
            latest_topics.append(latest_advice.topic_question)

    # ChatGPTに送信するためのプロンプトを作成
    combined_topics = "。".join(latest_topics)
    prompt = (
        f"以下は、これから取り組みたい睡眠に関するトピックです：{combined_topics}。"
        "これらを元に、全員に共通する改善点や挑戦できるミッションを1つ生成してください。"
        "ミッションは、全員が実行可能で協力して取り組む内容にしてください。20文字程度で出力してください。"
    )

    # OpenAI APIにリクエストを送信してミッションを生成
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
        mission_text = response['choices'][0]['message']['content']

         # ミッションをMissionモデルに保存
        Mission.objects.create(
            mission_time=datetime.now().time(),  # 現在時刻をmission_timeに保存
            mission=mission_text
        )

        # 日数をカウントするためにミッションの作成日時を保存
        mission.created_at = timezone.now()  # 現在時刻をcreated_atに保存
        mission.save()

    except Exception as e:
        return render(request, 'chat/room.html', {
            'mission': "もう一回お願いします。" ,
            'group': group,
            'group_members': group_members,
            'messages': reversed(messages),})
    
     # 最新のミッションを取得
    latest_mission = Mission.objects.order_by('-mission_time').first()

    # ミッション生成からの日数を計算
    if latest_mission:
        days_since_creation = (timezone.now() - latest_mission.created_at).days  # 日数を計算
    else:
        days_since_creation = 0  # ミッションが存在しない場合は0日

    # 生成されたミッションと最新のミッションを画面に表示
    return render(request, 'chat/room.html', {
        'mission': latest_mission.mission if latest_mission else mission_text,
        'group': group,
        'group_members': group_members,
        'messages': reversed(messages),
    })
