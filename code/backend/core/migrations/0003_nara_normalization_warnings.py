from django.db import migrations,models
import core.validators

class Migration(migrations.Migration):
    dependencies=[('core','0002_history_guards')]
    operations=[
        migrations.AddField(model_name='nararesult',name='normalization_warnings',
            field=models.JSONField(blank=True,default=list,validators=[core.validators.normalization_warnings])),
        migrations.RunSQL("ALTER TABLE core_nararesult ADD CONSTRAINT nara_warnings_array CHECK (jsonb_typeof(normalization_warnings)='array')",
                          'ALTER TABLE core_nararesult DROP CONSTRAINT nara_warnings_array'),
    ]
