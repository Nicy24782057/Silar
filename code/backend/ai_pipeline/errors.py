from common.api import ApiProblem


class PipelineFailure(ApiProblem):
    """A safe, contract-defined failure, without provider exception text."""


def not_ready():
    return PipelineFailure(
        "AI_CONFIGURATION_NOT_READY",
        "Aset, konfigurasi, atau dependensi AI belum siap.",
        503,
    )


def invalid_output():
    return PipelineFailure(
        "AI_OUTPUT_INVALID", "Keluaran AI belum dapat digunakan. Periksa sumber analisis.", 503
    )


class FencedExecution(ApiProblem):
    def __init__(self):
        super().__init__(
            "TRANSITION_REJECTED",
            "Eksekusi ini sudah tidak berlaku. Baca keadaan analisis tersimpan.",
            422,
        )
