from django import template
from groups.models import Group, GroupMember

register = template.Library()

@register.simple_tag
def get_user_group(user):
    if user.is_authenticated:
        try:
            # ユーザーが属するグループを取得
            member = GroupMember.objects.get(user=user)
            return member.group
        except GroupMember.DoesNotExist:
            return None
    return None
