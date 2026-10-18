from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers
from django.http import JsonResponse
from common.api import validate_query,SilarPagination,ApiProblem
from .models import AuditEvent
from .permissions import require_admin

def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT current_setting(\'server_version_num\')::integer')
            version=cursor.fetchone()[0]
        ok=version//10000==16
        return JsonResponse({'data':{'status':'READY' if ok else 'UNAVAILABLE','database':'READY' if ok else 'UNSUPPORTED_VERSION',
                                      'scope':'SLR_08','postgresql_major':version//10000}},status=200 if ok else 503)
    except Exception:
        return JsonResponse({'error':{'code':'DATABASE_UNAVAILABLE','message':'Database belum dapat digunakan.',
                                      'fields':{},'request_id':str(getattr(request,'request_id',''))}},status=503)

class AuditSerializer(serializers.ModelSerializer):
    class Meta:
        model=AuditEvent
        fields=['id','created_at','actor_id','actor_role','report_id','action','object_type','object_id','before','after','request_id']

class AuditListView(APIView):
    def get(self,request):
        require_admin(request.user,'view_audit')
        validate_query(request,['report_id','actor_id','action'])
        qs=AuditEvent.objects.order_by('-created_at','id')
        for key in ['report_id','actor_id']:
            if key in request.query_params:
                field=serializers.UUIDField();value=field.run_validation(request.query_params[key])
                qs=qs.filter(**{key:value})
        if 'action' in request.query_params:qs=qs.filter(action=request.query_params['action'])
        pager=SilarPagination();page=pager.paginate_queryset(qs,request)
        return pager.get_paginated_response(AuditSerializer(page,many=True).data)

