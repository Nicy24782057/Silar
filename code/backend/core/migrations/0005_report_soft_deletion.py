from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


GUARD = '''
CREATE FUNCTION silar_deleted_report_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.deleted_at IS NOT NULL AND NEW IS DISTINCT FROM OLD THEN
    RAISE EXCEPTION 'Deleted draft is terminal' USING ERRCODE='23514';
  END IF;
  IF OLD.deleted_at IS NULL AND NEW.deleted_at IS NOT NULL THEN
    IF NEW.revision <> OLD.revision + 1 OR
       (to_jsonb(NEW)-ARRAY['deleted_at','deleted_by_id','revision']) IS DISTINCT FROM
       (to_jsonb(OLD)-ARRAY['deleted_at','deleted_by_id','revision']) THEN
      RAISE EXCEPTION 'Deleting a draft preserves its source state' USING ERRCODE='23514';
    END IF;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER silar_deleted_report_guard BEFORE UPDATE ON core_report
FOR EACH ROW EXECUTE FUNCTION silar_deleted_report_guard();
'''


class Migration(migrations.Migration):
    dependencies = [('core','0004_allowed_enums'),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.AddField(model_name='report',name='deleted_at',field=models.DateTimeField(blank=True,null=True)),
        migrations.AddField(model_name='report',name='deleted_by',field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.PROTECT,related_name='+',to=settings.AUTH_USER_MODEL)),
        migrations.AddConstraint(model_name='report',constraint=models.CheckConstraint(
            condition=models.Q(deleted_at__isnull=True,deleted_by__isnull=True)|models.Q(
                deleted_at__isnull=False,deleted_by__isnull=False,deleted_by=models.F('owner'),workflow_status='NOT_SUBMITTED',submitted_at__isnull=True,
                official_card_version__isnull=True,published_version__isnull=True,active_publication_candidate__isnull=True),
            name='deleted_draft_owner_and_state')),
        migrations.RunSQL(GUARD,'DROP TRIGGER silar_deleted_report_guard ON core_report; DROP FUNCTION silar_deleted_report_guard();'),
    ]
