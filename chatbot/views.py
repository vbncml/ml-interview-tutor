from django.shortcuts import render, redirect
from django.http import JsonResponse
import openai
from django.contrib import auth
from django.contrib.auth.models import User
from .models import Chat

from django.utils import timezone
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
import os

openai_api_key = os.getenv('OPEN_API_KEY')
openai.api_key = openai_api_key

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', openai_api_key)
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

persist_directory = ''
vectorstore=Chroma(persist_directory=persist_directory, embedding_function=embeddings)
#vectorstore.get()

def ask_openai(message):
    #query = "What is difference between error and bias?"
    docs = vectorstore.similarity_search(message)
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages = [
            {"role":"system", "content": "Answer a question given this information: {docs}"},
            {"role":"user", "content": message},
        ],
    )
    #print(response)
    answer = response.choices[0].message.content
    return answer

# Create your views here.
def chatbot(request):
    chats = Chat.objects.filter(user=request.user)
    
    if request.method == 'POST':
        message = request.POST.get('message')
        response = ask_openai(message)
        chat = Chat(user=request.user, message=message, response=response, created_at=timezone.now())
        chat.save()
        return JsonResponse({'message': message, 'response': response})
    return render(request, 'chatbot.html', {'chats':chats})


def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('chatbot')
        else:
            error_message = 'Invalid username or password'
            return render(request, 'login.html', {'error_message':error_message})

    else:
        return render(request, 'login.html')

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 == password2:
            try:
                user = User.objects.create_user(username, email, password1)
                user.save()
                auth.login(request, user)
                return redirect('chatbot')
            except:
                error_message = 'Error creating account'
                return render(request, 'register.html', {'error_message':error_message})
        else:
            error_message = 'Passwords are not matching'
            return render(request, 'register.html', {'error_message':error_message})
    else:
        return render(request, 'register.html')

def logout(request):
    auth.logout(request)
    return redirect('login')