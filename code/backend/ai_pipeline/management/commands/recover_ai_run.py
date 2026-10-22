import json
import uuid

from django.core.management.base import BaseCommand, CommandError

from ai_pipeline.recovery import abort_stopped, mark_unknown
from core.models import AnalysisRun


class Command(BaseCommand):
    help = "Pemulihan teknis A7.5; hanya pemeriksaan host asal, bukan API retry."

    def add_arguments(self, parser):
        parser.add_argument("run_id", type=uuid.UUID)
        parser.add_argument("--expected-token", type=uuid.UUID)
        action = parser.add_mutually_exclusive_group(required=True)
        action.add_argument("--inspect", action="store_true")
        action.add_argument("--mark-unknown", action="store_true")
        action.add_argument("--abort-stopped", action="store_true")

    def handle(self, *args, **options):
        try:
            if options["inspect"]:
                run = AnalysisRun.objects.get(pk=options["run_id"])
                self.stdout.write(json.dumps({
                    "run_id": str(run.id), "status": run.status, "stage": run.stage,
                    "execution_token": str(run.execution_token),
                    "execution_context": run.execution_context,
                    "request_record_id": str(run.request_record_id),
                }, ensure_ascii=False, indent=2))
                return
            if options["expected_token"] is None:
                raise CommandError("--expected-token wajib untuk perubahan keadaan.")
            if options["mark_unknown"]:
                mark_unknown(options["run_id"], options["expected_token"])
                self.stdout.write("Run UNKNOWN; slot tetap ditahan sampai hasil pasti atau pemulihan sah.")
            else:
                abort_stopped(options["run_id"], options["expected_token"])
                self.stdout.write("Run terminal setelah bukti proses berhenti dan penggantian token.")
        except AnalysisRun.DoesNotExist as error:
            raise CommandError("Run tidak ditemukan.") from error
        except Exception as error:
            # Provider/private data is not printed by this command.
            from common.api import ApiProblem
            if isinstance(error, (ValueError, ApiProblem)):
                raise CommandError(str(error)) from error
            raise CommandError("Pemulihan belum berhasil; periksa keadaan database.") from error
