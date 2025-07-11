from django.contrib import admin

# Register your models here.
from .models import Post, UserPostReaction, UserPostView, Comment

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'likes', 'dislikes', 'views', 'comments_count', 'posted')
    list_filter = ('posted', 'user')
    search_fields = ('title', 'user__username', 'tags')
    readonly_fields = ('posted', 'views') 
    ordering = ('-posted',)

@admin.register(UserPostReaction)
class UserPostReactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'reaction_type', 'created_at', 'updated_at')
    list_filter = ('reaction_type', 'created_at', 'updated_at')
    search_fields = ('user__username', 'post__title')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(UserPostView)
class UserPostViewAdmin(admin.ModelAdmin):
    list_display = ('get_user_display', 'post', 'ip_address', 'viewed_at')
    list_filter = ('viewed_at',)
    search_fields = ('user__username', 'post__title', 'ip_address')
    readonly_fields = ('viewed_at',)
    
    def get_user_display(self, obj):
        if obj.user:
            return obj.user.username
        else:
            return f"Анонимный ({obj.ip_address})"
    get_user_display.short_description = 'Пользователь'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'content_preview', 'created_at', 'is_active']
    list_filter = ['is_active', 'created_at', 'post']
    search_fields = ['content', 'user__username', 'post__title']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Содержание'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'post')