import ctypes
import os
from pathlib import Path
from typing import Optional


_library: Optional[ctypes.CDLL] = None


def _load_library() -> ctypes.CDLL:
    global _library
    if _library is not None:
        return _library

    project_dir = Path(__file__).resolve().parent.parent
    candidates = []
    if path := os.environ.get('DIGIBYTE_POW_LIBRARY'):
        candidates.append(Path(path))
    candidates.append(project_dir / '.build' / 'libdigibytepow.so')

    for path in candidates:
        if path.is_file():
            _library = ctypes.CDLL(str(path))
            break
    else:
        raise RuntimeError(
            'DigiByte PoW library not found. Build it with '
            'DIGIBYTE_CORE_DIR=/path/to/digibyte-core '
            './contrib/build_digibyte_pow.sh')

    _library.digibyte_pow_hash.argtypes = [
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_ubyte),
    ]
    _library.digibyte_pow_hash.restype = ctypes.c_int
    return _library


def pow_hash(raw_header: bytes, *, version: int, timestamp: int) -> bytes:
    if len(raw_header) != 80:
        raise ValueError(f'expected 80-byte header, got {len(raw_header)}')
    header_buf = (ctypes.c_ubyte * 80).from_buffer_copy(raw_header)
    output_buf = (ctypes.c_ubyte * 32)()
    rc = _load_library().digibyte_pow_hash(header_buf, version, timestamp, output_buf)
    if rc:
        raise ValueError(f'unsupported DigiByte PoW algorithm for version {version:#x}')
    return bytes(output_buf)
