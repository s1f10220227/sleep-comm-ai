from django.shortcuts import render

def group_menu(request):
    return render(request, 'groups/group_menu.html')

def group_management(request):
    return render(request, 'groups/group_management.html')