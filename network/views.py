from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import User, Post
import json
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator


def index(request):
    all_posts = Post.objects.all().order_by('-date_created')

    # Paginate by 10
    paginator = Paginator(all_posts, 10)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)

    current_user =  request.user.id
    who_to_follow = User.objects.exclude(following=current_user).all()

    return render(request, "network/index.html", {
        'posts': posts,
        'who_to_follow': who_to_follow
    })


def create_post(request):
    if request.method == 'POST':
        body = request.POST['content']
        author = User.objects.get(pk=request.user.id)
        post = Post(author=author, body=body)
        post.save()
        return HttpResponseRedirect(reverse('index'))


def profile(request, user_id):
    user_profile = User.objects.get(pk=user_id)
    following_people = User.objects.filter(following=user_profile)
    followers = User.objects.filter(followers=user_profile)
    
    all_posts = Post.objects.filter(author=user_profile).order_by('-date_created')
    is_following = request.user in user_profile.following.all()

    # Paginate by 10
    paginator = Paginator(all_posts, 10)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)

    return render(request, "network/profile.html", {
        'posts': posts,
        'user_profile': user_profile,
        'is_following': is_following,
        'posts_count': all_posts.count,
        'following_people': following_people,
        'followers': followers
    })


def follow(request, user_id):
    if request.user.is_authenticated:
        # Access User Profile from DB
        user_profile = User.objects.get(pk=user_id)
        
        # Access User currently logged in
        current_user = request.user

        # Add User Profile to following list of current user
        user_profile.following.add(current_user)

        # Redirect user to the listing page
        return HttpResponseRedirect(reverse("profile", args=(user_profile.id,)))
    return HttpResponseRedirect(reverse('login'))

def unfollow(request, user_id):
    if request.user.is_authenticated:
        # Access User Profile from DB
        user_profile = User.objects.get(pk=user_id)
        
        # Access User currently logged in
        current_user = request.user

        # Remove User Profile to following list of current user
        user_profile.following.remove(current_user)

        # Redirect user to the listing page
        return HttpResponseRedirect(reverse("profile", args=(user_profile.id,)))
    else:
        return HttpResponseRedirect(reverse('login'))


def following(request):
    # get current user
    current_user =  User.objects.get(pk=request.user.id)

    # get list of users that the current user follows.
    following_people = User.objects.filter(following=current_user)

    # get all posts from DB
    all_posts = Post.objects.all().order_by('-date_created')

    # if post.author == following_user -> add post to the following posts
    following_posts = []
    for post in all_posts:
        for person in following_people:
            if person.id == post.author.id:
                following_posts.append(post)
            

    # Paginate by 10
    paginator = Paginator(following_posts, 10)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)

    current_user =  request.user.id    
    who_to_follow = User.objects.exclude(following=current_user).all()
    return render(request, "network/following.html", {
        'posts': posts,
        'who_to_follow': who_to_follow
    })


def post_like(request, post_id):
    if request.user.is_authenticated:
        post = Post.objects.get(pk=post_id)
        current_user =  User.objects.get(pk=request.user.id)
        likes_count = post.likes.count()
        if post.likes.filter(id=current_user.id):
            post.likes.remove(current_user)
            likes_count = post.likes.count()
            return JsonResponse({'message': 'Like removed!', 'likes_count': likes_count, 'liked': False})
        else:
            post.likes.add(current_user)
            likes_count = post.likes.count()
            return JsonResponse({'message': 'Like added!', 'likes_count': likes_count, 'liked': True})
    else:
        return HttpResponseRedirect(reverse('login'))


def delete_post(request, post_id):
    if request.user.is_authenticated:
        post = Post.objects.get(pk=post_id)
        current_user =  User.objects.get(pk=request.user.id)
        if post.author == current_user:
            post.delete()
            return HttpResponseRedirect(reverse('index'))
    else:
        return HttpResponseRedirect(reverse('login'))


@csrf_exempt
def edit_post(request, post_id):
    if request.method == 'POST':
        data =  json.loads(request.body)
        post = Post.objects.get(pk=post_id)
        post.body = data['body']
        post.save()
        return JsonResponse({'message': 'Change successful', 'body': data['body']})
    else:
        return HttpResponseRedirect(reverse('login'))    


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")
