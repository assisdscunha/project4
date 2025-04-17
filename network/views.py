import json
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from .models import Posts, User


def index(request):
    return render(request, "network/index.html")


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
            return render(
                request,
                "network/login.html",
                {"message": "Invalid username and/or password."},
            )
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
            return render(
                request, "network/register.html", {"message": "Passwords must match."}
            )

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(
                request, "network/register.html", {"message": "Username already taken."}
            )
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")


@csrf_exempt
@login_required
def share_post(request):
    """Makes possible for user to create a post on the Network"""
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)

    body = data.get("body", "")
    parent_id = data.get("parent")

    if not body:
        return JsonResponse({"error": "Post body cannot be empty."}, status=400)

    parent_post = None
    if parent_id:
        try:
            parent_post = Posts.objects.get(id=parent_id)
        except Posts.DoesNotExist:
            return JsonResponse({"error": "Post cannot be found."}, status=400)

    media_post = Posts(user=request.user, body=body, parent=parent_post)
    media_post.save()
    return JsonResponse({"message": "Post has been successfully added."}, status=201)


@csrf_exempt
@login_required
def post(request, post_id):
    try:
        social_post = Posts.objects.get(id=post_id)
    except Posts.DoesNotExist:
        return JsonResponse({"error": "Post cannot be found."}, status=400)

    if request.method == "GET":
        return JsonResponse(social_post.serialize())

    elif request.method == "PUT":
        if social_post.user != request.user:
            return JsonResponse(
                {"error": "User post not the same as requested."}, status=401
            )

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)

        allowed_keys = {"body", "likes"}
        if not set(data.keys()).issubset(allowed_keys):
            return JsonResponse(
                {"error": "Only 'body' or 'likes' fields are allowed."}, status=400
            )

        if data.get("body") is not None:
            social_post.body = data["body"]
        if data.get("likes") is not None:
            social_post.likes = data["likes"]
        social_post.save()

        return HttpResponse(status=204)

    else:
        return JsonResponse({"error": "GET or PUT request required."}, status=400)


def handle_profile(request):
    user_data = request.user.serialize()
    all_post_data = Posts.objects.filter(user=request.user)
    user_data["posts"] = [post.serialize() for post in all_post_data]
    return JsonResponse(user_data)


def handle_all(request):
    all_post_data = Posts.objects.all()
    data = [post.serialize() for post in all_post_data]
    return JsonResponse({"posts": data})


def handle_following(request):
    following = request.user.following.all()
    posts = Posts.objects.filter(user__in=following)
    data = [post.serialize() for post in posts]
    return JsonResponse({"posts": data})


@login_required
def page(request, page_name):
    if request.method != "GET":
        return JsonResponse({"error": "GET request required."}, status=400)

    handlers = {
        "profile": handle_profile,
        "all": handle_all,
        "following": handle_following,
    }

    handler = handlers.get(page_name)
    if handler:
        return handler(request)

    return JsonResponse({"error": "Page not found."}, status=404)
