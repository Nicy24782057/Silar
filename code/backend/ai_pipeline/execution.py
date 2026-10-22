"""Process identity for technical recovery; never returned by public serializers."""
from datetime import datetime, timezone
import os
import socket
import uuid

_INSTANCE = str(uuid.uuid4())


def process_context():
    import psutil
    return {
        "instance_id": _INSTANCE, "host": socket.gethostname(), "pid": os.getpid(),
        "process_started_at": psutil.Process().create_time(), "boot_time": psutil.boot_time(),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }


def stopped_process_evidence(context):
    """Conservative same-host OS check; timeouts or missing heartbeats are not proof."""
    import psutil
    if context.get("host") != socket.gethostname():
        raise ValueError("Pemeriksaan harus dilakukan pada host eksekusi asal.")
    pid, started = context.get("pid"), context.get("process_started_at")
    if type(pid) is not int or pid < 1 or not isinstance(started, (float, int)):
        raise ValueError("Identitas proses asal tidak lengkap.")
    try:
        process = psutil.Process(pid)
        if abs(process.create_time() - started) < 0.01 and process.is_running():
            raise ValueError("Proses API lama masih hidup; pemulihan dibatalkan.")
        return "PID_REUSED_OLD_PROCESS_STOPPED"
    except psutil.NoSuchProcess:
        return "PROCESS_NOT_PRESENT"
    except psutil.AccessDenied as error:
        raise ValueError("Keadaan proses tidak dapat dibuktikan.") from error
