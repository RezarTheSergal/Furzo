import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from functools import wraps
from django.utils.timezone import now
from testproject.celery import app
from .client_ip import get_client_ip


@app.task(bind=True, max_retries=3)
def log_user_action_task(self, action_data, name :str):
    """Фоновая задача для логирования действий"""
    try:
        logger = logging.getLogger(name)
        
        logger.info(
            f"Post: {action_data['post_id']}",
            extra={
                'user_id': action_data['user_id'],
                'username': action_data['username'],
                'view_name': action_data['view_name'],
                'path': action_data['path'],
                'method': action_data['method'],
                'status_code': action_data['status_code'],
                'ip_address': action_data['ip_address'],
            }
        )
        
    except Exception as e:
        logger.error(f"Logging failed: {str(e)}")
        self.retry(exc=e, countdown=60)

class DecoratorActionLogger:
    def __init__(self, logger_name: str = "user_actions"):
        self.logger_name = logger_name
        self._setup_logger()


    def _setup_logger(self):
        logs_dir = Path('logs')
        logs_dir.mkdir(exist_ok=True)
        
        logger = logging.getLogger(self.logger_name)
        logger.setLevel(logging.INFO)
        
        for handler in logger.handlers:
            logger.removeHandler(handler)

        formatter = logging.Formatter(
            '%(asctime)s | '
            'User:%(user_id)s(%(username)s) | '
            'View:%(view_name)s | '
            'Path:%(path)s | '
            'Method:%(method)s | '
            'Status:%(status_code)s | '
            'IP:%(ip_address)s | '
        )
        
        file_handler = RotatingFileHandler(
            filename=logs_dir / 'user_actions.log',
            maxBytes=10*1024*1024,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)


    def async_log_action(self):
        """Декоратор для асинхронного логирования"""
        def decorator(view_func):
            @wraps(view_func)
            def wrapper(request, *args, **kwargs):
                response = view_func(request, *args, **kwargs)

                data = json.loads(request.body)
                post_id = data.get('post_id')

                if request.user.is_authenticated:
                    action_data = {
                        'timestamp': now().isoformat(),
                        'user_id': request.user.id,
                        'username': request.user.username,
                        'view_name': view_func.__name__,
                        'path': request.path,
                        'method': request.method,
                        'status_code': response.status_code,
                        'ip_address': get_client_ip(request),
                        'user_agent': request.META.get('HTTP_USER_AGENT'),
                        'post_id': post_id,
                    }
                    
                    try:
                        log_user_action_task.delay(action_data, self.logger_name)
                    except Exception as e:
                        logging.getLogger(self.logger_name).error(
                            f"Celery task failed: {e}. Logging synchronously",
                            extra=action_data
                        )
                
                return response
            return wrapper
        return decorator