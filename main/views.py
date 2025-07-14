from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.db import transaction
from django.contrib.auth.models import AnonymousUser
import json
import logging
from utils.logging_config import get_client_ip, DecoratorActionLogger
from .models import Post, UserPostReaction, UserPostView, Comment

logger = logging.getLogger(__name__)
decorator_logger = DecoratorActionLogger("user_actions")

def get_post_boundaries():
    try:
        min_post_id = Post.objects.order_by('id').first()
        max_post_id = Post.objects.order_by('-id').first()
        
        return (
            min_post_id.id if min_post_id else 1,
            max_post_id.id if max_post_id else 1
        )
    except Exception as e:
        logger.error(f"Ошибка при получении границ постов: {e}")
        return (1, 1)

def validate_post_id(post_id):
    try:
        post_id = int(post_id)
        if post_id < 1:
            return None
        return post_id
    except (ValueError, TypeError):
        return None

def index(request):
    try:
        post_id = request.GET.get('post', get_post_boundaries()[0])
        post_id = validate_post_id(post_id)
        
        if not post_id:
            post_id = 1
            
        context = handle_register_view(request, get_post_data_context(post_id))
        return render(request, "main/index.html", context)
    except Exception as e:
        logger.error(f"Ошибка на главной странице: {e}")
        return render(request, "main/error.html", {"error": "Произошла ошибка при загрузке страницы"})

def get_post_data_context(post_id):
    try:
        post = get_object_or_404(Post, id=post_id)
        comments = Comment.objects.filter(post=post).select_related('user').order_by('created_at')
        
        comments = comments[:100]
        
        return {"post": post, "comments": comments}
    except Exception as e:
        logger.error(f"Ошибка при получении данных поста {post_id}: {e}")
        raise

def handle_register_view(request, context):
    try:
        if request.user.is_authenticated and not isinstance(request.user, AnonymousUser):
            try:
                user_reaction = UserPostReaction.objects.get(
                    user=request.user, 
                    post=context["post"]
                )
                context["user_reaction"] = user_reaction.reaction_type
            except UserPostReaction.DoesNotExist:
                context["user_reaction"] = None
        else:
            context["user_reaction"] = None
                
        register_view(request, context["post"])
        return context
    except Exception as e:
        logger.error(f"Ошибка при обработке регистрации просмотра: {e}")
        context["user_reaction"] = None
        return context

@csrf_exempt
@decorator_logger.async_log_action()
@require_http_methods(["POST"])
def get_post(request):
    try:
        if request.content_type != 'application/json':
            return JsonResponse({'error': 'Неверный Content-Type'}, status=400)
            
        data = json.loads(request.body)
        direction = data.get('direction')
        post_id = data.get('post_id')

        if direction not in [-1, 1]:
            return JsonResponse({'error': 'Неверное направление прокрутки'}, status=400)
        
        post_id = validate_post_id(post_id)
        if not post_id:
            return JsonResponse({'error': 'Некорректный ID поста'}, status=400)

        # Получаем границы постов
        min_post_id, max_post_id = get_post_boundaries()
        
        # Вычисляем новый ID поста с учетом границ
        new_post_id = post_id + direction
        
        if new_post_id < min_post_id:
            new_post_id = min_post_id
        elif new_post_id > max_post_id:
            new_post_id = max_post_id
        
        if not Post.objects.filter(id=new_post_id).exists():
            if direction > 0:
                next_post = Post.objects.filter(id__gt=post_id).order_by('id').first()
                if next_post:
                    new_post_id = next_post.id
                else:
                    new_post_id = max_post_id
            else:
                prev_post = Post.objects.filter(id__lt=post_id).order_by('-id').first()
                if prev_post:
                    new_post_id = prev_post.id
                else:
                    new_post_id = min_post_id

        context = handle_register_view(request, get_post_data_context(new_post_id))
        
        html = render_to_string('main/main.html', context, request=request)
        
        return JsonResponse({
            'success': True, 
            'html': html,
            'post_id': new_post_id
        })
            
    except json.JSONDecodeError:
        logger.warning(f"Неверный JSON от IP {get_client_ip(request)}")
        return JsonResponse({'error': 'Неверный формат JSON'}, status=400)
    except Exception as e:
        logger.error(f"Ошибка при получении поста: {e}")
        return JsonResponse({'error': 'Внутренняя ошибка сервера'}, status=500)

@csrf_exempt
@decorator_logger.async_log_action()
@require_http_methods(["POST"])
def get_specific_post(request):
    try:
        if request.content_type != 'application/json':
            return JsonResponse({'error': 'Неверный Content-Type'}, status=400)
            
        data = json.loads(request.body)
        post_id = validate_post_id(data.get('post_id'))
        
        if not post_id:
            return JsonResponse({'error': 'Некорректный ID поста'}, status=400)

        context = handle_register_view(request, get_post_data_context(post_id))
        html = render_to_string('main/main.html', context, request=request)
        
        return JsonResponse({
            'success': True, 
            'html': html,
            'post_id': post_id
        })
            
    except json.JSONDecodeError:
        logger.warning(f"Неверный JSON от IP {get_client_ip(request)}")
        return JsonResponse({'error': 'Неверный формат JSON'}, status=400)
    except Exception as e:
        logger.error(f"Ошибка при получении конкретного поста: {e}")
        return JsonResponse({'error': 'Внутренняя ошибка сервера'}, status=500)

def register_view(request, post):
    try:
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        if len(user_agent) > 500:
            user_agent = user_agent[:500]
        
        suspicious_patterns = ['<script', 'javascript:', 'data:']
        if any(pattern in user_agent.lower() for pattern in suspicious_patterns):
            logger.warning(f"Подозрительный user_agent от IP {ip_address}")
            user_agent = 'Suspicious'
        
        view_record, created = UserPostView.objects.get_or_create(
            user=request.user if request.user.is_authenticated else None,
            post=post,
            ip_address=ip_address,
            defaults={'user_agent': user_agent}
        )
        
        if created:
            with transaction.atomic():
                from django.db.models import F
                Post.objects.filter(id=post.id).update(views=F('views') + 1)
                post.refresh_from_db()
                return True
        else:
            return False
            
    except Exception as e:
        logger.error(f"Ошибка при регистрации просмотра: {e}")
        return False

@csrf_exempt
@login_required
@decorator_logger.async_log_action()
@require_http_methods(["POST"])
def toggle_like(request):
    try:
        if request.content_type != 'application/json':
            return JsonResponse({'error': 'Неверный Content-Type'}, status=400)
            
        data = json.loads(request.body)
        post_id = validate_post_id(data.get('post_id'))
        
        if not post_id:
            return JsonResponse({'error': 'Некорректный ID поста'}, status=400)
        
        post = get_object_or_404(Post, id=post_id)
        
        with transaction.atomic():
            user_reaction, created = UserPostReaction.objects.get_or_create(
                user=request.user,
                post=post,
                defaults={'reaction_type': 'none'}
            )
            
            if user_reaction.reaction_type == 'like':
                user_reaction.reaction_type = 'none'
                post.likes = max(0, post.likes - 1)
                is_liked = False
            else:
                if user_reaction.reaction_type == 'dislike':
                    post.dislikes = max(0, post.dislikes - 1)
                
                user_reaction.reaction_type = 'like'
                post.likes += 1
                is_liked = True
            
            user_reaction.save()
            post.save()
            
            return JsonResponse({
                'success': True,
                'likes': post.likes,
                'dislikes': post.dislikes,
                'is_liked': is_liked,
                'is_disliked': user_reaction.reaction_type == 'dislike'
            })
            
    except json.JSONDecodeError:
        logger.warning(f"Неверный JSON от IP {get_client_ip(request)}")
        return JsonResponse({'error': 'Неверный формат JSON'}, status=400)
    except Exception as e:
        logger.error(f"Ошибка при переключении лайка: {e}")
        return JsonResponse({'error': 'Внутренняя ошибка сервера'}, status=500)

@csrf_exempt
@login_required
@decorator_logger.async_log_action()
@require_http_methods(["POST"])
def toggle_dislike(request):
    try:
        if request.content_type != 'application/json':
            return JsonResponse({'error': 'Неверный Content-Type'}, status=400)
            
        data = json.loads(request.body)
        post_id = validate_post_id(data.get('post_id'))
        
        if not post_id:
            return JsonResponse({'error': 'Некорректный ID поста'}, status=400)
        
        post = get_object_or_404(Post, id=post_id)
        
        with transaction.atomic():
            user_reaction, created = UserPostReaction.objects.get_or_create(
                user=request.user,
                post=post,
                defaults={'reaction_type': 'none'}
            )
            
            if user_reaction.reaction_type == 'dislike':
                user_reaction.reaction_type = 'none'
                post.dislikes = max(0, post.dislikes - 1)
                is_disliked = False
            else:
                if user_reaction.reaction_type == 'like':
                    post.likes = max(0, post.likes - 1)
                
                user_reaction.reaction_type = 'dislike'
                post.dislikes += 1
                is_disliked = True
            
            user_reaction.save()
            post.save()
            
            return JsonResponse({
                'success': True,
                'likes': post.likes,
                'dislikes': post.dislikes,
                'is_liked': user_reaction.reaction_type == 'like',
                'is_disliked': is_disliked
            })
            
    except json.JSONDecodeError:
        logger.warning(f"Неверный JSON от IP {get_client_ip(request)}")
        return JsonResponse({'error': 'Неверный формат JSON'}, status=400)
    except Exception as e:
        logger.error(f"Ошибка при переключении дизлайка: {e}")
        return JsonResponse({'error': 'Внутренняя ошибка сервера'}, status=500)

@csrf_exempt
@decorator_logger.async_log_action()
@require_http_methods(["POST"])
def increment_views(request):
    try:
        if request.content_type != 'application/json':
            return JsonResponse({'error': 'Неверный Content-Type'}, status=400)
            
        data = json.loads(request.body)
        post_id = validate_post_id(data.get('post_id'))
        
        if not post_id:
            return JsonResponse({'error': 'Некорректный ID поста'}, status=400)
        
        post = get_object_or_404(Post, id=post_id)
        
        view_registered = register_view(request, post)
        
        return JsonResponse({
            'success': True,
            'views': post.views,
            'new_view': view_registered
        })
        
    except json.JSONDecodeError:
        logger.warning(f"Неверный JSON от IP {get_client_ip(request)}")
        return JsonResponse({'error': 'Неверный формат JSON'}, status=400)
    except Exception as e:
        logger.error(f"Ошибка при увеличении просмотров: {e}")
        return JsonResponse({'error': 'Внутренняя ошибка сервера'}, status=500)

@csrf_exempt
@decorator_logger.async_log_action()
@require_http_methods(["POST"])
def comments(request):
    try:
        if request.content_type != 'application/json':
            return JsonResponse({'error': 'Неверный Content-Type'}, status=400)
            
        data = json.loads(request.body)
        post_id = validate_post_id(data.get('post_id'))
        
        if not post_id:
            return JsonResponse({'error': 'Некорректный ID поста'}, status=400)

        post = get_object_or_404(Post, id=post_id)
        comments = Comment.objects.filter(post=post).select_related('user').order_by('created_at')[:100]
        
        context = {"comments": comments, "post": post}
        html = render_to_string('main/comments.html', context, request=request)
        
        return JsonResponse({'success': True, 'html': html})
        
    except json.JSONDecodeError:
        logger.warning(f"Неверный JSON от IP {get_client_ip(request)}")
        return JsonResponse({'error': 'Неверный формат JSON'}, status=400)
    except Exception as e:
        logger.error(f"Ошибка при получении комментариев: {e}")
        return JsonResponse({'error': 'Внутренняя ошибка сервера'}, status=500)

@csrf_exempt   
@login_required
@decorator_logger.async_log_action()
@require_http_methods(["POST"])
def add_comment(request):
    try:
        if request.content_type != 'application/json':
            return JsonResponse({'error': 'Неверный Content-Type'}, status=400)
            
        data = json.loads(request.body)
        post_id = validate_post_id(data.get('post_id'))
        parent_comment_id = validate_post_id(data.get('parent_comment_id')) if data.get('parent_comment_id') else None

        if not post_id:
            return JsonResponse({'error': 'Некорректный ID поста'}, status=400)

        post = get_object_or_404(Post, id=post_id)
        parent = None
        if parent_comment_id:
            parent = get_object_or_404(Comment, id=parent_comment_id)

        content = data.get('content', '').strip()

        # Валидация содержимого комментария
        if not content:
            return JsonResponse({
                'success': False,
                'error': 'Комментарий не может быть пустым'
            })
        
        if len(content) > 5000:
            return JsonResponse({
                'success': False,
                'error': 'Комментарий слишком длинный (максимум 5000 символов)'
            })

        # Простая защита от HTML-инъекций
        import html
        content = html.escape(content)
        
        # Проверка на спам (не более 5 комментариев в минуту)
        from django.utils import timezone
        from datetime import timedelta
        
        recent_comments = Comment.objects.filter(
            user=request.user,
            created_at__gte=timezone.now() - timedelta(minutes=1)
        ).count()
        
        if recent_comments >= 5:
            return JsonResponse({
                'success': False,
                'error': 'Слишком много комментариев. Подождите минуту.'
            })
        
        with transaction.atomic():
            comment = Comment.objects.create(
                post=post,
                user=request.user,
                content=content,
                parent=parent,
                created_at=timezone.now()
            )

            from django.db.models import F
            Post.objects.filter(id=post.id).update(comments_count=F('comments_count') + 1)

        return JsonResponse({
            'success': True,
            'comment': {
                'id': comment.id,
                'content': comment.content,
                'created_at': comment.created_at.isoformat(),
                'user': comment.user.username
            }
        })
        
    except json.JSONDecodeError:
        logger.warning(f"Неверный JSON от IP {get_client_ip(request)}")
        return JsonResponse({'error': 'Неверный формат JSON'}, status=400)
    except Exception as e:
        logger.error(f"Ошибка при добавлении комментария: {e}")
        return JsonResponse({'error': 'Внутренняя ошибка сервера'}, status=500)