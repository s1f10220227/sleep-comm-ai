import plotly.graph_objs as go
import plotly.io as pio
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta, time
from django.utils import timezone
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
    if sleep_time is None or wake_time is None:
        logger.warning(f"Sleep time or wake time is None for date: {date}")
        return 0

    sleep_datetime = datetime.combine(date, sleep_time)
    wake_datetime = datetime.combine(date, wake_time)
    if wake_datetime < sleep_datetime:
        wake_datetime += timedelta(days=1)
    
    duration = wake_datetime - sleep_datetime
    duration_hours = duration.total_seconds() / 3600
    
    if duration_hours < 0:
        logger.error(f"Negative duration calculated for date: {date}, sleep_time: {sleep_time}, wake_time: {wake_time}")
        return 0

    logger.debug(f"Calculated sleep duration: {duration_hours} hours for date: {date}")
    return duration_hours

def generate_plot(start_week, dates, values, ylabel, title, plot_type='scatter', special_case=None):
    logger.debug(f"Generating plot: {title}, with dates: {dates} and values: {values}")
    fig = go.Figure()
    all_dates = [start_week + timedelta(days=i) for i in range(7)]
    date_indices = [all_dates.index(date) if date in all_dates else None for date in dates]
    logger.debug(f"All dates for the week: {all_dates}, Date indices: {date_indices}")

    if not date_indices or all(index is None for index in date_indices):
        logger.debug("No valid dates found in the selected week.")
        return pio.to_html(fig, full_html=False)

    converted_values = [time_to_float(v) if isinstance(v, time) else v for v in values]
    
    max_value = max((v for v in converted_values if v is not None), default=0)

    if ylabel == '就寝時刻' or special_case == 'bedtime':
        y_axis = dict(tickmode='array', tickvals=list(range(0, 25)), ticktext=[f"{h:02d}:00" for h in range(0, 25)])
        text_labels = [float_to_time_str(v) if v is not None else None for v in converted_values]
    elif ylabel == '睡眠時間 (時間)':
        y_axis = dict(tickmode='array', tickvals=list(range(int(max_value) + 1)), ticktext=[f"{h:02d}:00" for h in range(int(max_value) + 1)])
        text_labels = [float_to_time_str(v) if v is not None else None for v in converted_values]  # 修正部分
    else:
        y_axis = dict(range=[0, max_value + 1])
        text_labels = [None] * len(converted_values)

    if special_case == 'bedtime':
        fig.add_trace(go.Scatter(
            x=all_dates,
            y=[converted_values[i] if i in date_indices and date_indices[i] is not None else None for i in range(7)],
            mode='markers+text',
            text=[text_labels[i] if i in date_indices and date_indices[i] is not None else None for i in range(7)],
            textposition='top center',
            hoverinfo='text',
            hovertext=[text_labels[i] if i in date_indices and date_indices[i] is not None else None for i in range(7)]
        ))
    elif plot_type == 'bar':
        fig.add_trace(go.Bar(
            x=all_dates,
            y=[converted_values[i] if i in date_indices and date_indices[i] is not None else 0 for i in range(7)],
            text=[text_labels[i] if i in date_indices and date_indices[i] is not None else None for i in range(7)],
            textposition='auto',
            textangle=-90,
            hoverinfo='text',
            hovertext=[text_labels[i] if i in date_indices and date_indices[i] is not None else None for i in range(7)]
        ))
    else:
        fig.add_trace(go.Scatter(
            x=all_dates,
            y=[converted_values[i] if i in date_indices and date_indices[i] is not None else None for i in range(7)],
            mode='lines+markers+text',
            text=[text_labels[i] if i in date_indices and date_indices[i] is not None else None for i in range(7)],
            textposition='top center',
            hoverinfo='text',
            hovertext=[text_labels[i] if i in date_indices and date_indices[i] is not None else None for i in range(7)]
        ))

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

    if week_start_str:
        start_week = datetime.strptime(week_start_str, '%Y-%m-%d').date()
        logger.debug(f"Parsed start_week from request: {start_week}")
    else:
        start_week = today - timedelta(days=today.weekday())
        logger.debug(f"Calculated start_week from today: {start_week}")

    end_week = start_week + timedelta(days=6)
    logger.debug(f"End of the week: {end_week}")

    prev_week = start_week - timedelta(weeks=1)
    next_week = start_week + timedelta(weeks=1)
    week_dates = [start_week + timedelta(days=i) for i in range(7)]
    logger.debug(f"Week dates (Monday to Sunday): {week_dates}")

    sleep_data = SleepAdvice.objects.filter(
        user=user, created_at__date__range=[start_week, end_week]
    ).order_by('created_at')
    logger.debug(f"Sleep data for the week: {list(sleep_data)}")

    sleep_data_dict = {data.created_at.date(): data for data in sleep_data}
    logger.debug(f"Sleep data dictionary: {sleep_data_dict}")

    sleep_times = []
    wake_times = []
    durations = []

    for date in week_dates:
        if date in sleep_data_dict:
            data = sleep_data_dict[date]
            sleep_times.append(data.sleep_time)
            wake_times.append(data.wake_time)
            duration = calculate_sleep_duration(data.sleep_time, data.wake_time, date)
            durations.append(duration)
        else:
            sleep_times.append(None)
            wake_times.append(None)
            durations.append(None)

    logger.debug(f"Processed sleep times: {sleep_times}")
    logger.debug(f"Processed wake times: {wake_times}")
    logger.debug(f"Processed durations: {durations}")

    show = request.GET.get('show', 'duration')
    logger.debug(f"Show mode: {show}")
    context = {}

    if show == 'times':
        sleep_time_plot = generate_plot(
            start_week, week_dates, sleep_times, '就寝時刻', '就寝時刻のグラフ', special_case='bedtime'
        )
        wake_time_plot = generate_plot(
            start_week, week_dates, wake_times, '起床時刻', '起床時刻のグラフ', special_case='bedtime'
        )
        context.update({
            'sleep_time_plot': sleep_time_plot,
            'wake_time_plot': wake_time_plot,
            'show': 'times',
        })
    else:
        duration_plot = generate_plot(
            start_week, week_dates, durations, '睡眠時間 (時間)', '睡眠時間のグラフ', plot_type='bar'
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
        {'date': timezone.localtime(advice.created_at).strftime('%Y-%m-%d %H:%M:%S'), 'advice': advice.advice}
        for advice in sleep_advice
    ]

    context.update({
        'advice_cards': advice_cards,
        'start_week': start_week.strftime('%Y-%m-%d'),
        'prev_week': prev_week.strftime('%Y-%m-%d'),
        'next_week': next_week.strftime('%Y-%m-%d'),
    })

    logger.debug("Rendering progress_check.html template with context.")
    return render(request, 'progress/progress_check.html', context)
