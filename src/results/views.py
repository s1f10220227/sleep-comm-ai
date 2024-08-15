from django.shortcuts import render

def results_and_feedback(request):
    return render(request, 'results/results_and_feedback.html')
