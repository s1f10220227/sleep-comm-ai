import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.io as pio
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta, time
from chat.models import SleepAdvice
import logging

logger = logging.getLogger(__name__)

def time_to_float(t):
    return t.hour + t.minute / 60

def calculate_sleep_duration(sleep_time, wake_time, date):
    sleep_datetime = datetime.combine(date, sleep_time)
    wake_datetime = datetime.combine(date, wake_time)
    if wake_datetime < sleep_datetime:
        wake_datetime += timedelta(days=1)
    duration = wake_datetime - sleep_datetime
    return duration.total_seconds() / 3600

def generate_plot(dates, values, ylabel, title, plot_type='scatter'):
    fig = go.Figure()
    
    # 月曜から日曜までの日付リストを作成
    start_date = min(dates) - timedelta(days=min(dates).weekday())
    end_date = start_date + timedelta(days=6)
    all_dates = [start_date + timedelta(days=i) for i in range(7)]
    
    # データがある日付のインデックスを取得
    date_indices = [all_dates.index(date) for date in dates]
    
    if values and isinstance(values[0], time):
        values = [time_to_float(v) for v in values]
        y_axis = dict(
            tickmode='array',
            tickvals=list(range(25)),
            ticktext=[f"{h:02d}:00" for h in range(25)]
        )
    else:
        y_axis = dict(range=[0, max(values or [0]) + 1])

    if plot_type == 'bar':
        fig.add_trace(go.Bar(x=all_dates, y=[0]*7, marker_color='rgba(0,0,0,0)'))  # 透明なバーを追加
        fig.add_trace(go.Bar(x=[all_dates[i] for i in date_indices], y=values))
    else:
        fig.add_trace(go.Scatter(x=all_dates, y=[None]*7, mode='lines+markers'))  # 空のラインを追加
        fig.add_trace(go.Scatter(x=[all_dates[i] for i in date_indices], y=values, mode='lines+markers'))

    fig.update_layout(
        title=title,
        xaxis_title='日付',
        yaxis_title=ylabel,
        yaxis=y_axis,
        xaxis=dict(
            tickmode='array',
            tickvals=all_dates,
            ticktext=[d.strftime('%a') for d in all_dates],  # 曜日を表示
            tickangle=0
        ),
        showlegend=False
    )

    return pio.to_html(fig, full_html=False)

@login_required
def progress_check(request):
    user = request.user
    today = datetime.now().date()
    start_week = today - timedelta(days=today.weekday())
    end_week = start_week + timedelta(days=6)
    
    sleep_data = SleepAdvice.objects.filter(
        user=user, created_at__date__range=[start_week, end_week]
    ).order_by('created_at')
    
    dates = [data.created_at.date() for data in sleep_data]
    show = request.GET.get('show', 'duration')
    context = {}
    
    if show == 'times':
        sleep_times = [data.sleep_time for data in sleep_data]
        wake_times = [data.wake_time for data in sleep_data]
        sleep_time_plot = generate_plot(
            dates, sleep_times, '就寝時刻', '就寝時刻のグラフ'
        )
        wake_time_plot = generate_plot(
            dates, wake_times, '起床時刻', '起床時刻のグラフ'
        )
        context.update({
            'sleep_time_plot': sleep_time_plot,
            'wake_time_plot': wake_time_plot,
            'show': 'times',
        })
    else:
        durations = [
            calculate_sleep_duration(data.sleep_time, data.wake_time, data.created_at.date())
            for data in sleep_data
        ]
        duration_plot = generate_plot(
            dates, durations, '睡眠時間 (時間)', '睡眠時間のグラフ', plot_type='bar'
        )
        context.update({
            'duration_plot': duration_plot,
            'show': 'duration',
        })
    
    sleep_advice = SleepAdvice.objects.filter(
        user=user, created_at__date__range=[start_week, end_week]
    ).order_by('-created_at')
    
    advice_cards = [
        {'date': advice.created_at.date(), 'advice': advice.advice}
        for advice in sleep_advice
    ]
    context['advice_cards'] = advice_cards
    return render(request, 'progress/progress_check.html', context)