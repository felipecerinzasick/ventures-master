from .models import Post, Comment, Resource
from newsletter.models import Newsletter
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import PostForm,ContactForm
from django.views.generic import (
    CreateView,
    ListView,
    DetailView,
    UpdateView,
    DeleteView
)

def privacy_policy(request):
    return render(request, 'blog/privacy.html')

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thanks for contacting us!")
            return redirect('index')  # Redirect to a success page.
        else:
            print(form.errors)
    # else:
    #     form = ContactForm()
    
    # return render(request, 'base1.html', {'form': form})



@login_required
def resources_view(request):
    resources = Resource.objects.all().order_by('-created_at')  # Assuming you want the newest resources first
    return render(request, 'blog/resources.html', {'resources': resources})



@login_required
def dashboard(request):
    # Fetch the posts by the current user
    user_posts = Post.objects.filter(author=request.user).order_by('-date_posted')

    # Fetch comments on the user's posts
    user_comments = Comment.objects.filter(post__author=request.user).order_by('-created_at')

    # You can add more context as per your application's functionality
    context = {
        'title': 'Dashboard',
        'user_posts': user_posts,
        'user_comments': user_comments
    }

    return render(request, 'blog/dashboard.html', context)

class PostListView(ListView):
    model = Post
    template_name = 'blog/blog.html'
    context_object_name = 'posts'
    paginate_by = 5

    def get_queryset(self):
        try:
            keyword = self.request.GET['q']
        except:
            keyword = ''
        if (keyword != ''):
            object_list = self.model.objects.filter(
                Q(content__icontains=keyword) | Q(title__icontains=keyword))
        else:
            object_list = self.model.objects.all()
        return object_list


class UserPostListView(ListView):
    model = Post
    template_name = 'blog/user_posts.html'
    context_object_name = 'posts'
    paginate_by = 5

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        return Post.objects.filter(author=user).order_by('-date_posted')


class PostDetailView(DetailView):
    model = Post


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    fields = ['title', 'content']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    success_url = '/'

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False


def about(request):
    return render(request, 'blog/about.html', {'title': 'About'})

def bitcoin(request):
    return render(request, 'blog/bitcoin.html', {'title': 'Bitcoin'})

def blog(request):
        return render(request, 'blog/blog.html', {'title': 'Blog'})

def index(request):
    newsletter = Newsletter.objects.first()
    print(newsletter.slug)
    return render(request, 'blog/index.html', {'title': 'Index', 'newsletter':newsletter})

def dashboard(request):
    return render(request, 'blog/dashboard.html', {'title': 'Dashboard'})


@login_required
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        user = User.objects.get(id=request.POST.get('user_id'))
        text = request.POST.get('text')
        Comment(author=user, post=post, text=text).save()
        messages.success(request, "Your comment has been added successfully.")
    else:
        return redirect('post_detail', pk=pk)
    return redirect('post_detail', pk=pk)
