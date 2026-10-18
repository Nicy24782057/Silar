from uuid import uuid4
from django.http import JsonResponse

class RequestMetadataMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.request_id = uuid4()
        response = self.get_response(request)
        if request.path.startswith('/api/') or request.path.startswith('/health/'):
            if response.status_code >= 400 and 'json' not in response.get('Content-Type', ''):
                status = response.status_code
                code = {400:'INVALID_PAYLOAD',403:'PERMISSION_DENIED',404:'NOT_FOUND',405:'METHOD_NOT_ALLOWED'}.get(status,'INTERNAL_ERROR')
                response = JsonResponse({'error': {'code':code,'message':'Permintaan belum dapat diselesaikan.',
                    'fields':{},'request_id':str(request.request_id)}}, status=status)
            response['Cache-Control'] = 'no-store'
            response['X-Request-ID'] = str(request.request_id)
            response['X-Content-Type-Options'] = 'nosniff'
        return response
