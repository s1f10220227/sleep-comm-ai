from django.shortcuts import render

def group_chat(request):
    return render(request, 'chat/chat.html')
