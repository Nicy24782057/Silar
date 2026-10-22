"""Explicit local asset preparation; never downloads weights during an API request."""
import hashlib
import json
from pathlib import Path
import shutil
import uuid

from django.core.management.base import BaseCommand, CommandError

from ai_pipeline.clients import verified_whisper_manifest
from ai_pipeline.config import options
from ai_pipeline.runtime import active_modules


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while block := stream.read(1024 * 1024):
            value.update(block)
    return value.hexdigest()


class Command(BaseCommand):
    help = "Verifikasi/ekstrak aset SLR09; unduh Whisper hanya bila diminta eksplisit."

    def add_arguments(self, parser):
        parser.add_argument("--sena-archive", type=Path)
        parser.add_argument("--nara-archive", type=Path)
        parser.add_argument("--include-whisper", action="store_true")
        parser.add_argument("--whisper-only", action="store_true")
        parser.add_argument("--whisper-revision", default="main")

    def handle(self, *args, **arguments):
        config = options()
        candidate, _, _ = active_modules(config.slr09_root)
        _, lock, _ = candidate.selected_assets(config.slr09_root)
        if not arguments["whisper_only"]:
            for name, directory in (("sena", config.sena_dir), ("nara", config.nara_dir)):
                spec = lock["models"][name]
                archive = arguments[name + "_archive"] or (
                    config.slr09_root.parent / name / spec["archive_name"]
                )
                try:
                    candidate.extract_candidate_archive(archive, directory, name, spec)
                except (OSError, ValueError, KeyError) as error:
                    raise CommandError(f"{name.upper()}: arsip atau hash aset belum sesuai.") from error
                self.stdout.write(f"{name.upper()}: berkas runtime cocok dengan manifest SLR09.")
        if arguments["include_whisper"] or arguments["whisper_only"]:
            self.prepare_whisper(config, arguments["whisper_revision"])
        self.stdout.write("Persiapan berkas selesai; ini bukan bukti inferensi atau uji integrasi.")

    def prepare_whisper(self, config, revision):
        from huggingface_hub import HfApi, snapshot_download
        target = config.whisper_dir
        if target.is_symlink():
            raise CommandError("Direktori Whisper tidak boleh berupa symlink.")
        target.mkdir(parents=True, exist_ok=True)
        manifest = target / "silar_whisper_manifest.json"
        if manifest.exists():
            verified_whisper_manifest(config)
            self.stdout.write("Whisper: manifest dan berkas lokal sudah cocok.")
            return
        repository = "Systran/faster-whisper-small"
        try:
            commit = HfApi().model_info(repository, revision=revision).sha
            snapshot = Path(snapshot_download(
                repository, revision=commit,
                allow_patterns=[
                    "config.json", "model.bin", "tokenizer.json",
                    "preprocessor_config.json", "vocabulary.json", "vocabulary.txt",
                ],
            ))
            files = {}
            for source in sorted(snapshot.iterdir()):
                if not source.is_file():
                    continue
                destination = target / source.name
                expected = digest(source)
                if destination.is_symlink() or (destination.exists() and digest(destination) != expected):
                    raise ValueError("Existing Whisper asset differs.")
                if not destination.exists():
                    shutil.copyfile(source, destination)
                files[source.name] = expected
            if not {"config.json", "model.bin", "tokenizer.json"} <= set(files):
                raise ValueError("Incomplete Whisper files.")
            value = {"variant": "small", "repository": repository, "revision": commit, "files": files}
            temporary = target / (".manifest-" + uuid.uuid4().hex)
            temporary.write_text(json.dumps(value, indent=2) + "\n")
            temporary.replace(manifest)
            verified_whisper_manifest(config)
        except Exception as error:
            raise CommandError("Whisper: unduhan atau verifikasi aset belum selesai.") from error
        self.stdout.write(f"Whisper small: revisi {commit} dicatat bersama SHA-256 berkas.")
