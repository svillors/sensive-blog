from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models import Count, Prefetch


class PostQuerySet(models.QuerySet):

    def popular(self):
        most_popular_posts = (
            Post.objects
            .annotate(likes_count=Count('likes', distinct=True))
            .order_by('-likes_count')
        )
        return most_popular_posts

    def fetch_with_comments_count(self):
        posts = self
        posts_ids = [post.id for post in posts]
        posts_with_comments = (
            Post.objects
            .filter(id__in=posts_ids)
            .annotate(comments_amount=Count('comments'))
        )
        ids_and_comments = posts_with_comments.values_list(
            'id', 'comments_amount')
        count_for_id = dict(ids_and_comments)
        for post in posts:
            post.comments_amount = count_for_id[post.id]
        return posts

    def fetch_with_tags(self):
        return self.prefetch_related(
            Prefetch(
                'tags',
                queryset=Tag.objects.annotate(posts_with_tag=Count('posts'))
            )
        )

    def fresh_posts(self):
        return (
            self
            .annotate(comments_amount=Count('comments'))
            .order_by('-published_at')
        )


class TagQuerySet(models.QuerySet):

    def popular(self):
        popular_tags = (
            Tag.objects
            .annotate(tagged_posts_amount=Count('posts'))
            .order_by('-tagged_posts_amount')
        )
        return popular_tags


class Post(models.Model):
    title = models.CharField('Заголовок', max_length=200)
    text = models.TextField('Текст')
    slug = models.SlugField('Название в виде url', max_length=200)
    image = models.ImageField('Картинка')
    published_at = models.DateTimeField('Дата и время публикации')

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        limit_choices_to={'is_staff': True})
    likes = models.ManyToManyField(
        User,
        related_name='liked_posts',
        verbose_name='Кто лайкнул',
        blank=True)
    tags = models.ManyToManyField(
        'Tag',
        related_name='posts',
        verbose_name='Теги')

    objects = PostQuerySet.as_manager()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post_detail', args={'slug': self.slug})

    def first_tag_title(self):
        tags = list(self.tags.all())
        return tags[0].title if tags else None

    class Meta:
        ordering = ['-published_at']
        verbose_name = 'пост'
        verbose_name_plural = 'посты'


class Tag(models.Model):
    title = models.CharField('Тег', max_length=20, unique=True)

    objects = TagQuerySet.as_manager()

    def __str__(self):
        return self.title

    def clean(self):
        self.title = self.title.lower()

    def get_absolute_url(self):
        return reverse('tag_filter', args={'tag_title': self.slug})

    class Meta:
        ordering = ['title']
        verbose_name = 'тег'
        verbose_name_plural = 'теги'


class Comment(models.Model):
    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        verbose_name='Пост, к которому написан',
        related_name='comments')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор')

    text = models.TextField('Текст комментария')
    published_at = models.DateTimeField('Дата и время публикации')

    def __str__(self):
        return f'{self.author.username} under {self.post.title}'

    class Meta:
        ordering = ['published_at']
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'
