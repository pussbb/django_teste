from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey, \
    GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.db.models import F
from django.utils.text import slugify


VOTE_CHOICES = (
    (+1, '+1'),
    (-1, '-1'),
)


class VotesManager(models.Manager):

    def likes(self):
        return self.get_queryset().filter(vote__gt=0)

    def dislikes(self):
        return self.get_queryset().filter(vote__lt=0)


class Vote(models.Model):
    vote = models.SmallIntegerField(choices=VOTE_CHOICES)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='votes')
    # generic foreign key to the model being voted upon
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    objects = VotesManager()

    class Meta:
        pass
        #unique_together = (('author', 'content_type', 'object_id'),)

    def __update_related_content_object(self, amount=1):
        field = 'likes'
        if self.vote < 0:
            field = 'dislikes'
        #  select_for_update ???
        self.content_type.model_class().objects.filter(
            pk=self.object_id
        ).update(**{field: F(field) + amount})

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValueError("Updating the vote entry isn't allowed")
        with transaction.atomic():
            super().save(*args, **kwargs)
            self.__update_related_content_object()

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            super().delete(*args, **kwargs)
            self.__update_related_content_object(-1)

    def __str__(self):
        return '{} on {}'.format(self.get_vote_display(), self.content_object)


class Post(models.Model):
    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True,
                            default='', editable=False,)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='blog_posts')
    updated_on = models.DateTimeField(auto_now=True)
    content = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True, db_index=True)
    votes = GenericRelation(Vote)

    likes = models.PositiveIntegerField(default=0)
    dislikes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_on']

    def __str__(self):
        return self.title

    def _get_unique_slug(self):
        slug = slugify(self.title)
        unique_slug = slug
        num = 1
        while Post.objects.filter(slug=unique_slug).exists():
            unique_slug = '{}-{}'.format(slug, num)
            num += 1
        return unique_slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._get_unique_slug()
        super().save(*args, **kwargs)
