import logging
from datetime import datetime, timedelta, time
from enum import Enum

import markdown
import plotly.graph_objs as go
import plotly.io as pio
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from chat.models import SleepAdvice

class PlotType(Enum):
    TIME = 'time'
    DURATION = 'duration'
    RATING = 'rating'

def time_to_float(t):
    hours = t.hour + (24 if t.hour < 4 else 0)
    return hours + t.minute / 60

def float_to_time_str(value):
    value = value - 24 if value >= 24 else value
    hours, minutes = int(value), int((value - int(value)) * 60)
    return f"{hours:02d}:{minutes:02d}"

def get_y_axis_config(plot_type, ylabel, values):
    if plot_type == PlotType.TIME:
        y_range = [20, 32] if '就寝' in ylabel else [4, 12]
        tick_vals = list(range(y_range[0], y_range[1] + 1))
        return dict(
            tickmode='array',
            tickvals=tick_vals,
            ticktext=[float_to_time_str(h) for h in tick_vals],
            range=y_range,
            gridcolor='rgba(128, 128, 128, 0.2)',
            zeroline=False
        )
    elif plot_type == PlotType.RATING:
        return dict(
            tickmode='array',
            tickvals=[1, 2, 3, 4, 5],
            range=[0.5, 5.5],
            gridcolor='rgba(128, 128, 128, 0.2)',
            zeroline=False
        )
    else:  # Duration
        max_value = max((v for v in values if v is not None), default=0)
        return dict(
            range=[0, max_value + 1],
            gridcolor='rgba(128, 128, 128, 0.2)',
            zeroline=False
        )

def format_value_labels(values, plot_type):
    if plot_type == PlotType.TIME:
        return [float_to_time_str(v) if v is not None else None for v in values]
    elif plot_type == PlotType.DURATION:
        return [f"{v:.1f}h" if v is not None else None for v in values]
    else:  # Rating
        return [str(int(v)) if v is not None else None for v in values]

def generate_plot(start_week, dates, values, ylabel, title, plot_type, use_bar=False):
    fig = go.Figure()
    all_dates = [start_week + timedelta(days=i) for i in range(7)]
    date_indices = [all_dates.index(date) if date in all_dates else None for date in dates]

    if not date_indices or all(index is None for index in date_indices):
        return pio.to_html(fig, full_html=False)

    converted_values = [time_to_float(v) if isinstance(v, time) else v for v in values]
    y_axis = get_y_axis_config(plot_type, ylabel, converted_values)
    text_labels = format_value_labels(converted_values, plot_type)

    trace_data = [converted_values[i] if i in date_indices and date_indices[i] is not None else None for i in range(7)]
    trace_text = [text_labels[i] if i in date_indices and date_indices[i] is not None else None for i in range(7)]

    if use_bar:
        trace = go.Bar(
            x=all_dates,
            y=[v if v is not None else 0 for v in trace_data],
            text=trace_text,
            textposition='outside',
            marker_color='rgba(102, 197, 204, 0.8)',
            hovertemplate='%{text}<extra></extra>'
        )
    else:
        trace = go.Scatter(
            x=all_dates,
            y=trace_data,
            mode='lines+markers+text',
            text=trace_text,
            textposition='top center',
            line=dict(color='#66C5CC', width=2),
            marker=dict(size=8, color='#66C5CC'),
            hovertemplate='%{text}<extra></extra>'
        )

    fig.add_trace(trace)

    japanese_weekdays = ['月', '火', '水', '木', '金', '土', '日']
    fig.update_layout(
        title=dict(text=title, font=dict(size=18)),
        xaxis_title='日付',
        yaxis_title=ylabel,
        yaxis=y_axis,
        xaxis=dict(
            tickmode='array',
            tickvals=all_dates,
            ticktext=[f"{d.strftime('%m/%d')} ({japanese_weekdays[d.weekday()]})" for d in all_dates],
            tickangle=-45,
            gridcolor='rgba(128, 128, 128, 0.2)'
        ),
        template="plotly_dark",
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=50, b=50, l=50, r=20),
        height=400
    )

    return pio.to_html(fig, full_html=False)

@login_required
def sleep_data(request):
    user = request.user
    today = datetime.now().date()
    week_start_str = request.GET.get('week_start')
    start_week = datetime.strptime(week_start_str, '%Y-%m-%d').date() if week_start_str else today - timedelta(days=today.weekday())
    end_week = start_week + timedelta(days=6)
    week_dates = [start_week + timedelta(days=i) for i in range(7)]

    sleep_data = SleepAdvice.objects.filter(
        user=user, created_at__date__range=[start_week, end_week]
    ).order_by('created_at')
    sleep_data_dict = {timezone.localtime(data.created_at).date(): data for data in sleep_data}

    # Prepare data arrays
    data_arrays = {
        'sleep_times': [],
        'wake_times': [],
        'durations': [],
        'sleep_quality': [],
        'mission_achievement': []
    }

    for date in week_dates:
        if date in sleep_data_dict:
            data = sleep_data_dict[date]
            data_arrays['sleep_times'].append(data.sleep_time)
            data_arrays['wake_times'].append(data.wake_time)
            data_arrays['durations'].append(data.sleep_duration.total_seconds() / 3600 if data.sleep_duration else None)
            data_arrays['sleep_quality'].append(data.sleep_quality)
            data_arrays['mission_achievement'].append(data.mission_achievement)
        else:
            for key in data_arrays:
                data_arrays[key].append(None)

    show = request.GET.get('show', 'duration')
    context = {
        'show': show,
        'start_week': start_week.strftime('%Y-%m-%d'),
        'prev_week': (start_week - timedelta(weeks=1)).strftime('%Y-%m-%d'),
        'next_week': (start_week + timedelta(weeks=1)).strftime('%Y-%m-%d'),
    }

    if show == 'times':
        context.update({
            'sleep_time_plot': generate_plot(start_week, week_dates, data_arrays['sleep_times'], '就寝時刻', '就寝時刻のグラフ', PlotType.TIME),
            'wake_time_plot': generate_plot(start_week, week_dates, data_arrays['wake_times'], '起床時刻', '起床時刻のグラフ', PlotType.TIME)
        })
    elif show == 'quality':
        context.update({
            'sleep_quality_plot': generate_plot(start_week, week_dates, data_arrays['sleep_quality'], '睡眠の質', '睡眠の質のグラフ', PlotType.RATING),
            'mission_achievement_plot': generate_plot(start_week, week_dates, data_arrays['mission_achievement'], 'ミッション達成度', 'ミッション達成度のグラフ', PlotType.RATING)
        })
    else:  # duration
        context.update({
            'duration_plot': generate_plot(start_week, week_dates, data_arrays['durations'], '睡眠時間', '睡眠時間のグラフ', PlotType.DURATION, use_bar=True)
        })

    # Add advice cards
    context['advice_cards'] = []
    for advice in sleep_data.order_by('-created_at'):
        hours = int(advice.sleep_duration.total_seconds() // 3600) if advice.sleep_duration else 0
        minutes = int((advice.sleep_duration.total_seconds() % 3600) // 60) if advice.sleep_duration else 0

        advice_text = (
            f"- 就寝時刻: {advice.sleep_time.strftime('%H:%M')}\n"
            f"- 起床時刻: {advice.wake_time.strftime('%H:%M')}\n"
            f"- 睡眠時間: {hours}時間{minutes}分\n"
            f"- 睡眠休養感: {advice.get_sleep_quality_display()}\n"
            f"- ミッション達成度: {'なし' if advice.mission_achievement is None else advice.get_mission_achievement_display()}\n"
            f"- 寝る前にやったこと: {advice.pre_sleep_activities}\n\n"
            f"{advice.advice}"
        )

        context['advice_cards'].append({
            'date': timezone.localtime(advice.created_at).strftime('%Y-%m-%d %H:%M:%S'),
            'advice': markdown.markdown(advice_text)
        })

    return render(request, 'progress/sleep_data.html', context)
