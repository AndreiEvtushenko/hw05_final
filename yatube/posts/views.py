from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post
from .utils import paginator

AMOUNT_OF_POSTS = 10


@cache_page(20)
def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.all()
    page_obj = paginator(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    post_list = group.posts.all()
    page_obj = paginator(request, post_list)
    context = {
        'posts': posts,
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    posts_of_author = Post.objects.filter(author=author)
    page_obj = paginator(request, posts_of_author)
    count_posts_of_author = len(posts_of_author)
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=author
        ).exists()
    else:
        following = False
    context = {
        'posts': posts_of_author,
        'count': count_posts_of_author,
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, template, context)


@cache_page(10 * 2)
def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    posts = Post.objects.filter(pk=post_id)
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.filter(post=post_id)
    post_author = Post.objects.get(pk=post_id)
    count = post_author.author.posts.count()
    if request.method == 'POST':
        add_comment(request, post_id)
    else:
        form = CommentForm()
    context = {
        'posts': posts,
        'count': count,
        'post': post,
        'form': form,
        'comments': comments,
    }

    return render(request, template, context)


@login_required
def create_post(request):
    template = 'posts/create_post.html'
    form = PostForm()
    context = {
        'form': form,
    }
    if request.method != "POST":
        return render(request, template, context)
    form = PostForm(request.POST or None,
                    files=request.FILES or None
                    )
    if form.is_valid() is False or None:
        return render(request, template, context)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user)


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:post_detail', post_id)
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    # Получите пост и сохраните его в переменную post.
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts_follow_authors = Post.objects.filter(
        author__following__user=request.user)
    page_obj = paginator(request, posts_follow_authors)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    is_follower = Follow.objects.filter(user=user, author=author)
    if user != author and not is_follower.exists():
        Follow.objects.create(user=user, author=author)
    return redirect(reverse('posts:profile', args=[username]))


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=user, author=author).delete()
    return redirect('posts:profile', username=user)
