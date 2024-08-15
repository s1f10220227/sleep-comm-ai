from django.shortcuts import render

def progress_check(request):
    return render(request, 'progress/progress_check.html')
