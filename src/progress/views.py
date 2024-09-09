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

def float_to_time_str(value):
    hours = int(value)
    minutes = int((value - hours) * 60)
    return f"{hours:02d}:{minutes:02d}"

def calculate_sleep_duration(sleep_time, wake_time, date):
    sleep_datetime = datetime.combine(date, sleep_time)
    wake_datetime = datetime.combine(date, wake_time)
    if wake_datetime < sleep_datetime:
        wake_datetime += timedelta(days=1)
    duration = wake_datetime - sleep_datetime
    logger.debug(f"Calculated sleep duration: {duration.total_seconds() / 3600} hours for date: {date}")
    return duration.total_seconds() / 3600

def generate_plot(dates, values, ylabel, title, plot_type='scatter', special_case=None):
    logger.debug(f"Generating plot: {title}, with dates: {dates} and values: {values}")
    
    fig = go.Figure()
    # Todayの日付から週の始まりと終わりを計算
    today = datetime.today().date()
    start_of_week = today - timedelta(days=today.weekday())  # 月曜日
    end_of_week = start_of_week + timedelta(days=6)  # 日曜日
    logger.debug(f"Start of the week: {start_of_week}, End of the week: {end_of_week}")
    
    all_dates = [start_of_week + timedelta(days=i) for i in range(7)]
    date_indices = [all_dates.index(date) if date in all_dates else None for date in dates]
    logger.debug(f"All dates for the week: {all_dates}, Date indices: {date_indices}")
    
    if not date_indices or all(index is None for index in date_indices):
        logger.debug("No valid dates found in the selected week.")
        return pio.to_html(fig, full_html=False)
    
    if values and isinstance(values[0], time):
        values = [time_to_float(v) for v in values]
        logger.debug(f"Converted time values to float: {values}")
        y_axis = dict(
            tickmode='array',
            tickvals=list(range(25)),
            ticktext=[f"{h:02d}:00" for h in range(25)]
        )
        text_labels = [float_to_time_str(v) for v in values]
    elif ylabel == '睡眠時間 (時間)':
        y_axis = dict(
            tickmode='array',
            tickvals=list(range(int(max(values)) + 1)),
            ticktext=[f"{h:02d}:00" for h in range(int(max(values)) + 1)]
        )
        text_labels = [float_to_time_str(v) for v in values]
    else:
        y_axis = dict(range=[0, max(values or [0]) + 1])
        text_labels = [None] * len(values)
    
    logger.debug(f"Y-axis setup complete with labels: {y_axis}")
    
    if special_case == 'bedtime':
        fig.add_trace(go.Scatter(
            x=all_dates,
            y=[values[date_indices.index(i)] if i in date_indices and i is not None else None for i in range(7)],
            mode='markers+text',
            text=[text_labels[date_indices.index(i)] if i in date_indices and i is not None else None for i in range(7)],
            textposition='top center',
            hoverinfo='text',
            hovertext=[text_labels[date_indices.index(i)] if i in date_indices and i is not None else None for i in range(7)]
        ))
        logger.debug("Bedtime scatter plot created.")
    elif plot_type == 'bar':
        fig.add_trace(go.Bar(
            x=all_dates,
            y=[values[date_indices.index(i)] if i in date_indices and i is not None else 0 for i in range(7)],
            text=[text_labels[date_indices.index(i)] if i in date_indices and i is not None else None for i in range(7)],
            textposition='auto',
            textangle=-90,
            hoverinfo='text',
            hovertext=[text_labels[date_indices.index(i)] if i in date_indices and i is not None else None for i in range(7)]
        ))
        logger.debug("Bar plot created.")
    else:
        fig.add_trace(go.Scatter(
            x=all_dates,
            y=[None]*7,
            mode='lines+markers'
        ))
        fig.add_trace(go.Scatter(
            x=all_dates,
            y=[values[date_indices.index(i)] if i in date_indices and i is not None else None for i in range(7)],
            mode='lines+markers+text',
            text=[text_labels[date_indices.index(i)] if i in date_indices and i is not None else None for i in range(7)],
            textposition='top center',
            hoverinfo='text',
            hovertext=[text_labels[date_indices.index(i)] if i in date_indices and i is not None else None for i in range(7)]
        ))
        logger.debug("Line plot with markers created.")

    japanese_weekdays = ['月', '火', '水', '木', '金', '土', '日']
    fig.update_layout(
        title=title,
        xaxis_title='日付',
        yaxis_title=ylabel,
        yaxis=y_axis,
        xaxis=dict(
            tickmode='array',
            tickvals=all_dates,
            ticktext=[f"{d.strftime('%m/%d')} ({japanese_weekdays[d.weekday()]})" for d in all_dates],
            tickangle=-90
        ),
        showlegend=False
    )
    logger.debug("Plot layout updated.")
    return pio.to_html(fig, full_html=False)

@login_required
def progress_check(request):
    user = request.user
    logger.debug(f"User: {user}")
    today = datetime.now().date()
    logger.debug(f"Today's date: {today}")
    
    week_start_str = request.GET.get('week_start')
    logger.debug(f"Received week_start: {week_start_str}")
    
    if week_start_str:
        start_week = datetime.strptime(week_start_str, '%Y-%m-%d').date()
        logger.debug(f"Parsed start_week from request: {start_week}")
    else:
        start_week = today - timedelta(days=today.weekday())
        logger.debug(f"Calculated start_week from today: {start_week}")
    
    end_week = start_week + timedelta(days=6)
    logger.debug(f"End of the week: {end_week}")
    
    sleep_data = SleepAdvice.objects.filter(
        user=user, created_at__date__range=[start_week, end_week]
    ).order_by('created_at')
    logger.debug(f"Sleep data for the week: {list(sleep_data)}")
    
    dates = [data.created_at.date() for data in sleep_data]
    logger.debug(f"Sleep data dates: {dates}")
    
    show = request.GET.get('show', 'duration')
    logger.debug(f"Show mode: {show}")
    
    context = {}
    
    if not dates:
        logger.debug("No data available for the selected week.")
        context['message'] = 'データがありません。'
        return render(request, 'progress/progress_check.html', context)
    
    if show == 'times':
        sleep_times = [data.sleep_time for data in sleep_data]
        wake_times = [data.wake_time for data in sleep_data]
        logger.debug(f"Sleep times: {sleep_times}, Wake times: {wake_times}")
        sleep_time_plot = generate_plot(
            dates, sleep_times, '就寝時刻', '就寝時刻のグラフ', special_case='bedtime'
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
        logger.debug(f"Sleep durations: {durations}")
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
    logger.debug(f"Sleep advice: {list(sleep_advice)}")
    
    advice_cards = [
        {'date': advice.created_at.date(), 'advice': advice.advice}
        for advice in sleep_advice
    ]
    
    context['advice_cards'] = advice_cards
    context['start_week'] = start_week.strftime('%Y-%m-%d')
    logger.debug("Rendering progress_check.html template with context.")
    return render(request, 'progress/progress_check.html', context)
