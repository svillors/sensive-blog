from django.shortcuts import render
from blog.models import Comment, Post, Tag
from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404


def serialize_post(post):
    return {
        'title': post.title,
        'teaser_text': post.text[:200],
        'author': post.author.username,
        'comments_amount': post.comments_amount,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in post.tags.all()],
        'first_tag_title': post.first_tag_title(),
    }


def serialize_tag(tag):
    return {
        'title': tag.title,
        'posts_with_tag': tag.posts_with_tag,
    }


def index(request):

    most_popular_posts = (
        Post.objects
        .popular()
        .select_related('author')
        .fetch_with_tags()
        .fetch_with_comments_count()
    )[:5]

    most_fresh_posts = (
        Post.objects
        .fresh_posts()
        .select_related('author')
        .fetch_with_tags()
    )[:5]

    most_popular_tags = (
        Tag.objects
        .popular()
        .annotate(posts_with_tag=Count('posts'))
    )[:5]

    context = {
        'most_popular_posts': [
            serialize_post(post) for post in most_popular_posts
        ],
        'page_posts': [
            serialize_post(post) for post in most_fresh_posts
        ],
        'popular_tags': [
            serialize_tag(tag) for tag in most_popular_tags
        ],
    }
    return render(request, 'index.html', context)


def post_detail(request, slug):
    post = (
        Post.objects.filter(slug=slug)
        .annotate(likes_amount=Count("likes"))
        .prefetch_related(
            Prefetch(
                "comments",
                queryset=(
                    Comment.objects
                    .select_related("author")
                )
            ),
            Prefetch(
                'tags',
                queryset=Tag.objects.annotate(posts_with_tag=Count('posts'))
            )
        )
        .first()
    )

    comments = post.comments.all()
    serialized_comments = []
    for comment in comments:
        serialized_comments.append({
            'text': comment.text,
            'published_at': comment.published_at,
            'author': comment.author.username,
        })

    serialized_post = {
        'title': post.title,
        'text': post.text,
        'author': post.author.username,
        'comments': serialized_comments,
        'likes_amount': post.likes_amount,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [{
            'title': tag.title,
            'posts_with_tag': tag.posts_with_tag
        } for tag in post.tags.all()],
    }

    most_popular_tags = (
        Tag.objects
        .popular()
        .annotate(posts_with_tag=Count('posts'))
    )[:5]

    most_popular_posts = (
        Post.objects
        .popular()
        .select_related('author')
        .fetch_with_tags()
        .fetch_with_comments_count()
    )[:5]

    context = {
        'post': serialized_post,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'most_popular_posts': [
            serialize_post(post) for post in most_popular_posts
        ],
    }
    return render(request, 'post-details.html', context)


def tag_filter(request, tag_title):
    tag = get_object_or_404(Tag, title=tag_title)

    most_popular_tags = (
        Tag.objects
        .popular()
        .annotate(posts_with_tag=Count('posts'))
    )[:5]

    most_popular_posts = (
        Post.objects
        .popular()
        .select_related('author')
        .fetch_with_tags()
        .fetch_with_comments_count()
    )[:5]

    related_posts = (
        Post.objects
        .filter(tags=tag)
        .select_related('author')
        .fetch_with_tags()
        .fetch_with_comments_count()
    )[:20]

    context = {
        'tag': tag.title,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'posts': [serialize_post(post) for post in related_posts],
        'most_popular_posts': [
            serialize_post(post) for post in most_popular_posts
        ],
    }
    return render(request, 'posts-list.html', context)


def contacts(request):
    # позже здесь будет код для статистики заходов на эту страницу
    # и для записи фидбека
    return render(request, 'contacts.html', {})
