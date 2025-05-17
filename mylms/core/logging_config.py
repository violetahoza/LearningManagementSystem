import logging
import os
from django.conf import settings

# Create logs directory if it doesn't exist
logs_dir = os.path.join(settings.BASE_DIR, 'logs')
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Configure logging
def configure_logging():
    """Configure logging for the LMS application"""
    
    # Basic configuration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create custom loggers
    loggers = {
        'security': {
            'file': os.path.join(logs_dir, 'security.log'),
            'level': logging.WARNING,
        },
        'user_activity': {
            'file': os.path.join(logs_dir, 'user_activity.log'),
            'level': logging.INFO,
        },
        'errors': {
            'file': os.path.join(logs_dir, 'errors.log'),
            'level': logging.ERROR,
        },
        'api': {
            'file': os.path.join(logs_dir, 'api.log'),
            'level': logging.INFO,
        }
    }
    
    # Create handlers for each logger
    for logger_name, config in loggers.items():
        # Create logger
        logger = logging.getLogger(logger_name)
        logger.setLevel(config['level'])
        
        # Create file handler
        file_handler = logging.FileHandler(config['file'])
        file_handler.setLevel(config['level'])
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] - %(name)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(file_handler)
    
    # Configure Django logging
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '{levelname} {asctime} {module} {message}',
                'style': '{',
            },
            'simple': {
                'format': '{levelname} {message}',
                'style': '{',
            },
        },
        'handlers': {
            'django_file': {
                'level': 'INFO',
                'class': 'logging.FileHandler',
                'filename': os.path.join(logs_dir, 'django.log'),
                'formatter': 'verbose',
            },
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['django_file', 'console'],
                'level': 'INFO',
                'propagate': True,
            },
        },
    })

# Get loggers for different components
security_logger = logging.getLogger('security')
user_activity_logger = logging.getLogger('user_activity')
error_logger = logging.getLogger('errors')
api_logger = logging.getLogger('api')

# Define log decorators
def log_user_activity(message):
    """Decorator to log user activity"""
    def decorator(view_func):
        def wrapped_view(request, *args, **kwargs):
            user_id = request.user.id if request.user.is_authenticated else 'Anonymous'
            user_activity_logger.info(f"User {user_id}: {message}")
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator

def log_api_call(message):
    """Decorator to log API calls"""
    def decorator(view_func):
        def wrapped_view(request, *args, **kwargs):
            user_id = request.user.id if request.user.is_authenticated else 'Anonymous'
            api_logger.info(f"API call by User {user_id}: {message}")
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator

# Initialize logging
configure_logging()