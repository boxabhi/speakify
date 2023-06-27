from django.shortcuts import render
from accounts.models import Interests
from django.http import JsonResponse
from .thread import *

def home(request):
    
    return render(request , 'login.html')

def register(request):
    
    return render(request , 'register.html',
                  context = {
                      "interests" : Interests.objects.all()
                  })

def dashboard(request):
    return render(request , "dashboard.html")


def chat(request, chat_room_id):

    return render(request, "chat.html", context={
        "chat_room_id" : chat_room_id
    } )


def generate_student_data(request):
    total = request.GET.get('total')
    CreateStudentsThread(int(total)).start()
    return JsonResponse({'status' : 200})