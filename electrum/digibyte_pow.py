import ctypes
import os
import sys
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
    if getattr(sys, 'frozen', False):
        candidates.append(Path(getattr(sys, '_MEIPASS', '')) / 'libdigibytepow-0.dll')
    candidates.append(project_dir / '.build' / 'libdigibytepow.so')
    candidates.append(project_dir / '.build' / 'libdigibytepow-0.dll')
    candidates.append(project_dir / 'libdigibytepow-0.dll')

    for path in candidates:
        if path.is_file():
            _library = ctypes.CDLL(str(path))
            break
    else:
        # python-for-android places recipe libraries in the APK's native
        # library directory; its filesystem path is not stable, so resolve
        # the bare SONAME through Android's dynamic loader.
        try:
            _library = ctypes.CDLL('libdigibytepow.so')
        except OSError as exc:
            raise RuntimeError(
                'DigiByte PoW library not found. Build it with '
                'DIGIBYTE_CORE_DIR=/path/to/digibyte-core '
                './contrib/build_digibyte_pow.sh') from exc

    _library.digibyte_pow_hash.argtypes = [
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_ubyte),
    ]
    _library.digibyte_pow_hash.restype = ctypes.c_int
    _library.digibyte_pow_hash_batch.argtypes = [
        ctypes.POINTER(ctypes.c_ubyte), ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_ubyte),
    ]
    _library.digibyte_pow_hash_batch.restype = ctypes.c_int
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


def pow_hash_batch(raw_headers: bytes) -> list[bytes]:
    if len(raw_headers) % 80:
        raise ValueError(f'expected 80-byte headers, got {len(raw_headers)}')
    count = len(raw_headers) // 80
    if not count:
        return []
    header_buf = (ctypes.c_ubyte * len(raw_headers)).from_buffer_copy(raw_headers)
    output_buf = (ctypes.c_ubyte * (count * 32))()
    rc = _load_library().digibyte_pow_hash_batch(header_buf, count, output_buf)
    if rc:
        raise ValueError('unsupported DigiByte PoW algorithm in header batch')
    return [bytes(output_buf[index * 32:(index + 1) * 32]) for index in range(count)]
