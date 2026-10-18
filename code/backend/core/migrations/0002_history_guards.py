from django.db import migrations

IMMUTABLE = ['EvidenceItem','EvidenceBundle','EvidenceBundleItem','Transcript','NarrativeVersion',
             'SENAResult','NARAResult','IncidentCardVersion','HumanVerification','OperatorReview','AuditEvent']

def install(apps,schema_editor):
    if schema_editor.connection.vendor!='postgresql':
        raise RuntimeError('SILAR menggunakan PostgreSQL 16; SQLite bukan pengganti pengujian constraint.')
    with schema_editor.connection.cursor() as cursor:
        cursor.execute('SHOW server_version_num')
        if int(cursor.fetchone()[0])//10000!=16:raise RuntimeError('Gunakan PostgreSQL mayor 16 sesuai acuan SILAR.')
    schema_editor.execute('''
    CREATE FUNCTION silar_history_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN RAISE EXCEPTION 'Historical SILAR record is immutable' USING ERRCODE='23514'; END $$;
    ''')
    for name in IMMUTABLE:
        table=schema_editor.quote_name(apps.get_model('core',name)._meta.db_table)
        schema_editor.execute(f'CREATE TRIGGER silar_immutable BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION silar_history_immutable()')
    schema_editor.execute('''
    ALTER TABLE core_evidencebundle ADD COLUMN _silar_creation_txid bigint NOT NULL DEFAULT txid_current();
    CREATE FUNCTION silar_bundle_membership() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE br uuid; er uuid; born bigint;
    BEGIN
      SELECT report_id,_silar_creation_txid INTO br,born FROM core_evidencebundle WHERE id=NEW.bundle_id;
      SELECT report_id INTO er FROM core_evidenceitem WHERE id=NEW.evidence_id;
      IF br IS DISTINCT FROM er THEN RAISE EXCEPTION 'Bundle evidence must share Report' USING ERRCODE='23514'; END IF;
      IF born IS DISTINCT FROM txid_current() THEN
        RAISE EXCEPTION 'Bundle membership is immutable after creation transaction' USING ERRCODE='23514';
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER silar_bundle_membership BEFORE INSERT ON core_evidencebundleitem FOR EACH ROW EXECUTE FUNCTION silar_bundle_membership();
    CREATE FUNCTION silar_bundle_nonempty() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF EXISTS(SELECT 1 FROM core_evidencebundle WHERE id=NEW.id)
         AND NOT EXISTS(SELECT 1 FROM core_evidencebundleitem WHERE bundle_id=NEW.id) THEN
        RAISE EXCEPTION 'EvidenceBundle needs at least one item in the same transaction' USING ERRCODE='23514';
      END IF;
      RETURN NULL;
    END $$;
    CREATE CONSTRAINT TRIGGER silar_bundle_nonempty AFTER INSERT ON core_evidencebundle
      DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION silar_bundle_nonempty();
    CREATE FUNCTION silar_report_guard() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE key text;
    BEGIN
      IF OLD.workflow_status='CLOSED' AND NEW IS DISTINCT FROM OLD THEN
        RAISE EXCEPTION 'CLOSED is terminal' USING ERRCODE='23514';
      END IF;
      IF OLD.submitted_at IS NOT NULL THEN
        FOREACH key IN ARRAY ARRAY['owner_id','official_card_version_id','submitted_at','active_bundle_id','active_narrative_id','current_card_version_id','input_revision','preparation_status'] LOOP
          IF (to_jsonb(NEW)->key) IS DISTINCT FROM (to_jsonb(OLD)->key) THEN
            RAISE EXCEPTION 'Official source is immutable' USING ERRCODE='23514';
          END IF;
        END LOOP;
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER silar_report_guard BEFORE UPDATE ON core_report FOR EACH ROW EXECUTE FUNCTION silar_report_guard();
    CREATE FUNCTION silar_publication_guard() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF EXISTS(SELECT 1 FROM core_report WHERE id=NEW.report_id AND workflow_status='CLOSED') THEN
        RAISE EXCEPTION 'CLOSED is terminal' USING ERRCODE='23514';
      END IF;
      IF TG_OP='UPDATE' THEN
        IF NEW.data IS DISTINCT FROM OLD.data OR NEW.card_version_id IS DISTINCT FROM OLD.card_version_id OR NEW.report_id IS DISTINCT FROM OLD.report_id OR NEW.version_number IS DISTINCT FROM OLD.version_number THEN
          RAISE EXCEPTION 'Publication content requires a new version' USING ERRCODE='23514';
        END IF;
        IF NEW.state<>OLD.state AND NOT ((OLD.state='DRAFT' AND NEW.state IN ('APPROVED','CANCELLED')) OR (OLD.state='APPROVED' AND NEW.state IN ('PUBLISHED','CANCELLED'))) THEN
          RAISE EXCEPTION 'Publication transition rejected' USING ERRCODE='23514';
        END IF;
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER silar_publication_guard BEFORE INSERT OR UPDATE ON core_publicationversion FOR EACH ROW EXECUTE FUNCTION silar_publication_guard();
    CREATE FUNCTION silar_preserve_history() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN RAISE EXCEPTION 'Historical SILAR record cannot be deleted' USING ERRCODE='23514'; END $$;
    CREATE TRIGGER silar_no_delete BEFORE DELETE ON core_operatorassignment FOR EACH ROW EXECUTE FUNCTION silar_preserve_history();
    CREATE TRIGGER silar_no_delete BEFORE DELETE ON core_publicationversion FOR EACH ROW EXECUTE FUNCTION silar_preserve_history();
    CREATE TRIGGER silar_no_delete BEFORE DELETE ON core_idempotencyrecord FOR EACH ROW EXECUTE FUNCTION silar_preserve_history();
    CREATE FUNCTION silar_assignment_guard() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF EXISTS(SELECT 1 FROM core_report WHERE id=NEW.report_id AND workflow_status='CLOSED') THEN
        RAISE EXCEPTION 'CLOSED is terminal' USING ERRCODE='23514';
      END IF;
      IF TG_OP='UPDATE' AND ((to_jsonb(NEW)-'ended_at') IS DISTINCT FROM (to_jsonb(OLD)-'ended_at')
            OR (OLD.ended_at IS NOT NULL AND NEW.ended_at IS DISTINCT FROM OLD.ended_at)) THEN
        RAISE EXCEPTION 'Assignment history is immutable; end then create a new assignment' USING ERRCODE='23514';
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER silar_assignment_guard BEFORE INSERT OR UPDATE ON core_operatorassignment FOR EACH ROW EXECUTE FUNCTION silar_assignment_guard();
    ''')
    for model in [apps.get_model('core',n) for n in ['AnalysisRun','SENAResult','NARAResult','IncidentCardVersion','PublicationVersion','AuditEvent','IdempotencyRecord']]:
        for field in model._meta.fields:
            if field.get_internal_type()=='JSONField':
                kind='array' if field.name=='uncertain_reasons' else 'object'
                table=schema_editor.quote_name(model._meta.db_table)
                col=schema_editor.quote_name(field.column)
                name=schema_editor.quote_name(f'{model._meta.model_name}_{field.name}_jsonkind')
                schema_editor.execute(f"ALTER TABLE {table} ADD CONSTRAINT {name} CHECK ({col} IS NULL OR jsonb_typeof({col})='{kind}')")

def uninstall(apps,schema_editor):
    for model in [apps.get_model('core',n) for n in ['AnalysisRun','SENAResult','NARAResult','IncidentCardVersion','PublicationVersion','AuditEvent','IdempotencyRecord']]:
        for field in model._meta.fields:
            if field.get_internal_type()=='JSONField':
                schema_editor.execute(f'ALTER TABLE {schema_editor.quote_name(model._meta.db_table)} DROP CONSTRAINT IF EXISTS {schema_editor.quote_name(f"{model._meta.model_name}_{field.name}_jsonkind")}')
    for function in ['silar_history_immutable','silar_bundle_membership','silar_bundle_nonempty','silar_report_guard','silar_publication_guard','silar_preserve_history','silar_assignment_guard']:
        schema_editor.execute(f'DROP FUNCTION IF EXISTS {function}() CASCADE')
    schema_editor.execute('ALTER TABLE core_evidencebundle DROP COLUMN _silar_creation_txid')

class Migration(migrations.Migration):
    dependencies=[('core','0001_initial')]
    operations=[migrations.RunPython(install,uninstall)]

