class PipelineError(Exception):
    """파이프라인 처리 중 발생하는 모든 예외의 기반 클래스."""
    pass


class ParseError(PipelineError):
    """파일 파싱 실패 (손상, 암호화, 지원하지 않는 형식)."""
    pass


class InsufficientSlidesError(PipelineError):
    """슬라이드 수가 분석 최소 요건(MIN_SLIDES)을 충족하지 못할 때."""
    pass
