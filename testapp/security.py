# testapp/security.py

import hashlib
import hmac
import time
from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.http import HttpResponseForbidden
import re

class SecurityManager:
    """Security utilities and validations"""
    
    @staticmethod
    def validate_student_input(student_id, student_name):
        """Validate student input for security"""
        # Check for SQL injection patterns
        sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\b)",
            r"(\b(UNION|OR|AND)\b.*=)",
            r"(--|#|/\*|\*/)",
            r"(\bexec\b|\beval\b)"
        ]
        
        combined_input = f"{student_id} {student_name}".upper()
        
        for pattern in sql_patterns:
            if re.search(pattern, combined_input, re.IGNORECASE):
                raise SuspiciousOperation("Invalid input detected")
        
        # Check length limits
        if len(student_id) > 50 or len(student_name) > 100:
            raise SuspiciousOperation("Input too long")
        
        # Check for XSS patterns
        xss_patterns = [
            r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe",
            r"<object",
            r"<embed"
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, combined_input, re.IGNORECASE):
                raise SuspiciousOperation("Invalid input detected")
        
        return True
    
    @staticmethod
    def generate_secure_token(data):
        """Generate secure token for API calls"""
        if not settings.SECRET_KEY:
            raise ValueError("SECRET_KEY not configured")
        
        timestamp = str(int(time.time()))
        message = f"{data}:{timestamp}"
        signature = hmac.new(
            settings.SECRET_KEY.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{timestamp}:{signature}"
    
    @staticmethod
    def verify_secure_token(token, data, max_age=3600):
        """Verify secure token"""
        try:
            timestamp_str, signature = token.split(':', 1)
            timestamp = int(timestamp_str)
            
            # Check token age
            if int(time.time()) - timestamp > max_age:
                return False
            
            # Verify signature
            message = f"{data}:{timestamp_str}"
            expected_signature = hmac.new(
                settings.SECRET_KEY.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def sanitize_filename(filename):
        """Sanitize filename for safe file operations"""
        # Remove path components
        filename = filename.split('/')[-1].split('\\')[-1]
        
        # Remove dangerous characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        
        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:255-len(ext)-1] + '.' + ext if ext else name[:255]
        
        return filename
    
    @staticmethod
    def check_file_type(file, allowed_types):
        """Check uploaded file type"""
        import magic # Ensure python-magic is installed
        
        # Check file extension
        file_ext = file.name.lower().split('.')[-1] if '.' in file.name else ''
        if file_ext not in allowed_types:
            return False
        
        # Check MIME type (if python-magic is available)
        try:
            file_content = file.read(1024)
            file.seek(0)  # Reset file pointer
            
            mime_type = magic.from_buffer(file_content, mime=True)
            allowed_mimes = {
                'csv': 'text/csv',
                'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'xls': 'application/vnd.ms-excel'
            }
            
            return mime_type in allowed_mimes.values()
            
        except ImportError:
            # Fallback to extension check if python-magic not available
            return True
    
    @staticmethod
    def log_security_event(event_type, details, request=None):
        """Log security events"""
        import logging
        
        security_logger = logging.getLogger('security')
        
        log_data = {
            'event_type': event_type,
            'details': details,
            'timestamp': time.time()
        }
        
        if request:
            log_data.update({
                'ip_address': SecurityManager.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'path': request.path,
                'method': request.method
            })
        
        security_logger.warning(f"Security Event: {log_data}")
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
