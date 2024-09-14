from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from groups.models import Group, GroupMember
from .models import Message

@login_required
def room(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    group_members = GroupMember.objects.filter(group=group)
    messages = Message.objects.filter(group=group).order_by('-timestamp')[:50]

    return render(request, 'chat/room.html', {
        'group': group,
        'group_members': group_members,
        'messages': reversed(messages),
    })
