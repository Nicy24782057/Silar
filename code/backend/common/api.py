from uuid import uuid4
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404, JsonResponse
from rest_framework import serializers
from rest_framework.exceptions import APIException, AuthenticationFailed, NotAuthenticated, PermissionDenied, ValidationError, Throttled
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView, exception_handler as drf_exception_handler
from django.middleware.csrf import CsrfViewMiddleware

class ApiProblem(APIException):
    def __init__(self, code, message, status=422, fields=None, retry_after=None):
        self.status_code, self.error_code = status, code
        self.fields, self.retry_after = fields or {}, retry_after
        super().__init__(message)

class StrictSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError({'non_field_errors': ['Body harus berupa objek JSON.']})
        unknown = set(data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({k: ['Field tidak diizinkan.'] for k in sorted(unknown)})
        return super().to_internal_value(data)

class SilarPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

def validate_query(request, allowed):
    bad = set(request.query_params) - set(allowed) - {'page', 'page_size'}
    fields = {k: ['Parameter tidak diizinkan.'] for k in bad}
    for k in ('page', 'page_size'):
        if k in request.query_params:
            try:
                value = int(request.query_params[k])
                if value < 1 or (k == 'page_size' and value > 100):
                    raise ValueError
            except (TypeError, ValueError):
                fields[k] = ['Harus bilangan positif; page_size maksimal 100.']
    if fields:
        raise ValidationError(fields)

def reject_query(request):
    if request.query_params:
        raise ValidationError({k:['Endpoint ini tidak menerima parameter query.'] for k in request.query_params})

def exception_handler(exc, context):
    if isinstance(exc, DjangoValidationError):
        exc = ValidationError(getattr(exc, 'message_dict', {'non_field_errors': exc.messages}))
    response = drf_exception_handler(exc, context)
    request = context.get('request')
    if response is None:
        # Unexpected failures have a safe envelope, never a debug traceback.
        return Response({'error': {'code': 'INTERNAL_ERROR', 'message': 'Permintaan belum dapat diselesaikan.',
                                  'fields': {}, 'request_id': str(getattr(request, 'request_id', uuid4()))}}, status=500)
    code = getattr(exc, 'error_code', None)
    if not code:
        code = ('AUTH_REQUIRED' if isinstance(exc, NotAuthenticated) else
                'TOKEN_INVALID' if isinstance(exc, AuthenticationFailed) else
                'PERMISSION_DENIED' if isinstance(exc, PermissionDenied) else
                'RATE_LIMITED' if isinstance(exc, Throttled) else
                'NOT_FOUND' if response.status_code == 404 else 'INVALID_PAYLOAD')
    fields = getattr(exc, 'fields', {})
    if isinstance(exc, ValidationError):
        data = exc.detail if isinstance(exc.detail, dict) else {'non_field_errors': exc.detail}
        fields = {str(k): [str(x) for x in (v if isinstance(v, list) else [v])] for k, v in data.items()}
    message = str(exc.detail) if isinstance(exc, ApiProblem) else {
        400: 'Periksa isian permintaan.', 401: 'Autentikasi tidak dapat digunakan.',
        403: 'Tindakan tidak diizinkan.', 404: 'Informasi tidak tersedia.', 429: 'Terlalu banyak percobaan. Coba kembali nanti.'
    }.get(response.status_code, 'Permintaan belum dapat diselesaikan.')
    response.data = {'error': {'code': code, 'message': message, 'fields': fields,
                               'request_id': str(getattr(request, 'request_id', uuid4()))}}
    wait = getattr(exc, 'retry_after', None) or getattr(exc, 'wait', None)
    if wait is not None:
        response['Retry-After'] = str(max(1, int(wait)))
    return response

class CsrfCheck(CsrfViewMiddleware):
    def _reject(self, request, reason):
        return reason

class AuthAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        reject_query(request)
        if request.method == 'POST':
            check = CsrfCheck(lambda r: None)
            check.process_request(request._request)
            if check.process_view(request._request, lambda r: None, (), {}):
                raise ApiProblem('CSRF_FAILED', 'Token CSRF atau origin tidak dapat digunakan.', 403)

def not_found(request, exception=None):
    return JsonResponse({'error': {'code': 'NOT_FOUND', 'message': 'Informasi tidak tersedia.', 'fields': {},
                                   'request_id': str(getattr(request, 'request_id', uuid4()))}}, status=404)

def server_error(request):
    return JsonResponse({'error': {'code': 'INTERNAL_ERROR', 'message': 'Permintaan belum dapat diselesaikan.', 'fields': {},
                                   'request_id': str(getattr(request, 'request_id', uuid4()))}}, status=500)
