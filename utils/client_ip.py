def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    if not ip or len(ip) > 45:  # IPv6 максимум 45 символов
        ip = '127.0.0.1'  # Fallback IP
    
    return ip