
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.contrib.postgres.fields import ArrayField

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200, blank=True)
    tags = ArrayField(models.CharField(max_length=50, blank=True))
    url = models.CharField(max_length=500)
    posted = models.DateTimeField(auto_now=True)
    likes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    dislikes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    views = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    comments_count = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-posted']

class UserPostReaction(models.Model):
    REACTION_CHOICES = [
        ('like', 'Like'),
        ('dislike', 'Dislike'),
        ('none', 'None'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=10, choices=REACTION_CHOICES, default='none')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'post')
        
    def __str__(self):
        return f"{self.user.username} - {self.post.title} - {self.reaction_type}"

class UserPostView(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # Один пользователь может просмотреть пост только один раз
        unique_together = ('user', 'post', 'ip_address')
        indexes = [
            models.Index(fields=['post', 'user']),
            models.Index(fields=['post', 'ip_address']),
        ]
        
    def __str__(self):
        if self.user:
            return f"{self.user.username} просмотрел {self.post.title}"
        else:
            return f"Анонимный пользователь ({self.ip_address}) просмотрел {self.post.title}"


class Comment(models.Model):
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField(max_length=5000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    class Meta:
        ordering = ['updated_at', 'created_at']
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['updated_at']),
        ]
    
    def __str__(self):
        return f'{self.user.username if self.user else "Аноним"}: {self.content[:50]}...'

    @property
    def is_edited(self):
        return self.updated_at != self.created_at