import logging

from django.conf import settings
from django.utils import timezone
from django.utils.timezone import localtime
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from celery import shared_task

import openai

from .models import Message, SleepAdvice, Mission
from groups.models import Group, GroupMember
from accounts.models import CustomUser

logger = logging.getLogger(__name__)

# settings.pyで定義した環境変数OPENAI_API_KEY, OPENAI_API_BASEを参照する
OPENAI_API_KEY = settings.OPENAI_API_KEY
OPENAI_API_BASE = settings.OPENAI_API_BASE

# AIモデルの初期化
chat = openai.ChatCompletion

# グループの初期メッセージを送信
@shared_task
def send_init_message(group_id):
    try:
        channel_layer = get_channel_layer()
        group = Group.objects.get(id=group_id)
        room_group_name = f'chat_{group.id}'
        ai_user = CustomUser.objects.get(username='AI Assistant')

        # グループの種類に応じたプロンプトを準備
        base_prompt = (
            "以下の内容を含む初期メッセージを作成してください：\n"
            "1. グループへの歓迎の挨拶\n"
            "2. AIアシスタントの自己紹介\n"
            "3. 3日間かけて睡眠改善ミッションに挑戦することの説明\n"
        )

        # プライベートグループの場合
        if group.is_private:
            specific_prompt = (
                "4. 一緒にグループに参加したい人に招待コードを共有し、その人もグループ参加後に左側の「準備完了」ボタンを押すよう案内\n"
                "5. グループメンバー全員が準備完了となり次第、事前の睡眠アンケートをもとにミッション案が5つ生成されることを説明\n"
                "6. 誤って「準備完了」ボタンを押してしまった場合は、一度グループを抜けて作り直すか再度参加する必要があることを説明\n"
                "7. 励ましの締めの言葉\n\n"
                "※絵文字を適度に使用してください。\n"
                "※重要な部分は強調してください。\n"
                "※内容は簡潔に、全体で400字程度に収めてください。"
            )
        # パブリックグループの場合
        else:
            specific_prompt = (
                "4. 参加希望者は左側の「準備完了」ボタンを押すよう案内\n"
                "5. グループメンバー全員が準備完了となり次第、事前の睡眠アンケートをもとにミッション案が5つ生成されることを説明\n"
                "6. 誤って「準備完了」ボタンを押してしまった場合は、一度グループを抜けて作り直すか再度参加する必要があることを説明\n"
                "7. 励ましの締めの言葉\n\n"
                "※絵文字を適度に使用してください。\n"
                "※重要な部分は強調してください。\n"
                "※内容は簡潔に、全体で400字程度に収めてください。"
            )

        prompt = base_prompt + specific_prompt

        response = chat.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a friendly AI assistant that supports group members in improving their sleep."},
                {"role": "user", "content": prompt}
            ],
            api_key=OPENAI_API_KEY,
            api_base=OPENAI_API_BASE
        )

        message = response['choices'][0]['message']['content'].strip()

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': 'AI Assistant'
            }
        )

        Message.objects.create(
            sender=ai_user,
            group=group,
            content=message
        )

        logger.info(f"Initial messages sent successfully to group {group_id}")
        return "Initial messages sent successfully"

    except Exception as e:
        logger.error(f"Error sending initial messages to group {group_id}: {str(e)}")
        return f"Error sending initial messages: {str(e)}"


# ミッションの説明を送信
@shared_task
def send_mission_explanation(group_id, mission_text):
    try:
        prompt = (
            f"以下のミッションが睡眠にどのように良い影響を与えるか、その理由と効果を100文字程度で説明してください：\n"
            f"ミッション：{mission_text}\n"
            f"※専門的な説明を避け、わかりやすく具体的に説明してください。"
        )

        response = chat.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a sleep expert who explains the benefits of sleep-related activities."},
                {"role": "user", "content": prompt}
            ],
            api_key=OPENAI_API_KEY,
            api_base=OPENAI_API_BASE
        )

        benefits_explanation = response['choices'][0]['message']['content'].strip()

        message = (
            f"🎯 新しいミッションが確定されました！『{mission_text}』\n\n"
            f"✨ このミッションの効果：\n"
            f"{benefits_explanation}\n\n"
            f"📋 明日朝7時に、睡眠状況とミッションの達成度についてのアンケートが送信されます。"
            f"皆さんの回答をお待ちしています！"
        )

        group = Group.objects.get(id=group_id)
        ai_user = CustomUser.objects.get(username='AI Assistant')

        Message.objects.create(
            sender=ai_user,
            group=group,
            content=message
        )

        channel_layer = get_channel_layer()
        room_group_name = f'chat_{group_id}'

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': 'AI Assistant'
            }
        )

        # ミッション説明送信後、全メンバーの睡眠レポートをグループに送信
        group_members = GroupMember.objects.filter(group_id=group_id).exclude(user__username='AI Assistant')  # AI Assistantは除外
        for member in group_members:
            send_sleep_report.delay(member.user.username, group_id)

        logger.info(f"Mission explanation sent successfully for group {group_id}")
        return "Mission explanation sent successfully"

    except Exception as e:
        logger.error(f"Error sending mission explanation: {str(e)}")
        return f"Error sending mission explanation: {str(e)}"


# グループに睡眠レポートを送信
@shared_task
def send_sleep_report(username, group_id):
    try:
        user = CustomUser.objects.get(username=username)
        group = Group.objects.get(id=group_id)

        # 最新の睡眠アドバイスを取得
        latest_advice = SleepAdvice.objects.filter(user=user).latest('created_at')

        # 睡眠時間を時間と分に変換
        hours = int(latest_advice.sleep_duration.total_seconds() // 3600)
        minutes = int((latest_advice.sleep_duration.total_seconds() % 3600) // 60)

        # レポートメッセージの作成
        report = (
            f"{user.username}さんの{latest_advice.created_at.strftime('%m月%d日')}の睡眠レポート\n"
            f"- 就寝時刻: {latest_advice.sleep_time.strftime('%H:%M')}\n"
            f"- 起床時刻: {latest_advice.wake_time.strftime('%H:%M')}\n"
            f"- 睡眠時間: {hours}時間{minutes}分\n"
            f"- 睡眠休養感: {latest_advice.get_sleep_quality_display()}\n"
            f"- ミッション達成度: {'なし' if latest_advice.mission_achievement is None else latest_advice.get_mission_achievement_display()}\n"
            f"- 寝る前にやったこと: {latest_advice.pre_sleep_activities}\n"
        )

        # アドバイスの要約を生成
        prompt = (
            f"以下の睡眠アドバイスを1文で要約してください：\n"
            f"{latest_advice.advice}"
        )

        response = chat.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a sleep expert who summarizes sleep advice concisely."},
                {"role": "user", "content": prompt}
            ],
            api_key=OPENAI_API_KEY,
            api_base=OPENAI_API_BASE
        )

        summary = response['choices'][0]['message']['content'].strip()
        report += f"一言アドバイス: {summary}"

        # メッセージの作成と送信
        ai_user = CustomUser.objects.get(username='AI Assistant')
        Message.objects.create(
            sender=ai_user,
            group=group,
            content=report
        )

        # WebSocket経由でメッセージを送信
        channel_layer = get_channel_layer()
        room_group_name = f'chat_{group_id}'
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'chat_message',
                'message': report,
                'username': 'AI Assistant'
            }
        )

        logger.info(f"Sleep report sent successfully for user {username}")
        return "Sleep report sent successfully"

    except Exception as e:
        logger.error(f"Error sending sleep report: {str(e)}")
        return f"Error sending sleep report: {str(e)}"


# 睡眠アンケートを送信
@shared_task
def send_sleep_questionnaire():
    try:
        prompt = (
            "睡眠アンケートの依頼メッセージを以下の3つのパートで作成してください：\n"
            "1. 明るい朝の挨拶\n"
            "2. 睡眠アンケートへの回答依頼\n"
            "3. 励ましの締めの言葉\n"
            "※各パートは簡潔に作成してください。\n"
            "※適度に絵文字を使用してください。\n"
            "※全体で100字程度に収めてください。"
        )

        response = chat.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a friendly sleep coach helping users track their sleep habits."},
                {"role": "user", "content": prompt}
            ],
            api_key=OPENAI_API_KEY,
            api_base=OPENAI_API_BASE
        )

        ai_message = response['choices'][0]['message']['content'].strip()

        # アンケートURLを含めた完全なメッセージを構築
        questionnaire_url = "http://127.0.0.1:8080/chat/sleep_q/"
        message = (
            f"{ai_message}\n\n"
            f"📋 アンケートURL: {questionnaire_url}"
        )

        # 全グループにメッセージを送信
        channel_layer = get_channel_layer()
        groups = Group.objects.all()
        ai_user = CustomUser.objects.get(username='AI Assistant')

        for group in groups:
            room_group_name = f'chat_{group.id}'

            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': 'AI Assistant'
                }
            )

            Message.objects.create(sender=ai_user, group=group, content=message)

        logger.info("Sleep questionnaire sent successfully")
        return "Sleep questionnaire sent successfully"

    except Exception as e:
        logger.error(f"Error sending sleep questionnaire: {str(e)}")
        return f"Error sending sleep questionnaire: {str(e)}"


@shared_task
def send_daily_tips():
    try:
        input_message = "睡眠の質を高めるための簡単なTipsや雑学などを教えてください。50字以内でお願いします。"
        response = chat.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a sleep expert who provides advice on healthy sleep habits."},
                {"role": "user", "content": input_message}
            ],
            api_key=OPENAI_API_KEY,
            api_base=OPENAI_API_BASE,
            temperature=0.7,
        )
        ai_response = response['choices'][0]['message']['content'].strip()
        message = "今日の睡眠豆知識\n" + ai_response if ai_response else "睡眠に関するTipsを取得できませんでした。"

        ai_user = CustomUser.objects.get(username='AI Assistant')
        groups = Group.objects.all()
        channel_layer = get_channel_layer()

        for group in groups:
            room_group_name = f'chat_{group.id}'

            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': 'AI Assistant'
                }
            )

            Message.objects.create(sender=ai_user, group=group, content=message)

        logger.info("Daily sleep tips sent successfully")
        return "Daily sleep tips sent successfully"

    except Exception as e:
        logger.error(f"Error sending daily tips: {str(e)}")
        return f"Error sending daily tips: {str(e)}"


@shared_task
def send_mission_complete_message():
    try:
        channel_layer = get_channel_layer()
        groups = Group.objects.all()
        message = "ミッション達成おめでとうございます"
        ai_user = CustomUser.objects.get(username='AI Assistant')

        for group in groups:
            # 最新のミッションを取得
            latest_mission = Mission.objects.filter(group=group).order_by('-created_at').first()

            if latest_mission:
                days_since_creation = (localtime(timezone.now()).date() - localtime(latest_mission.created_at).date()).days + 1

                if days_since_creation == 2:  # ミッション作成から3日経過
                    room_group_name = f'chat_{group.id}'

                    async_to_sync(channel_layer.group_send)(
                        room_group_name,
                        {
                            'type': 'chat_message',
                            'message': message,
                            'username': 'AI Assistant'
                        }
                    )

                    Message.objects.create(sender=ai_user, group=group, content=message)

        logger.info("Mission complete messages sent successfully")
        return "Mission complete messages sent successfully"

    except Exception as e:
        logger.error(f"Error sending mission complete messages: {str(e)}")
        return f"Error sending mission complete messages: {str(e)}"
