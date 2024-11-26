import time
import mimetypes
import config
from functools import wraps

LAST_CACHE_CLEAN = 0
def clean(auto=False):
  """
  Cleans the cache of files that haven't been updated or accessed recently. If
  `auto` is True, then only clean if it has been sufficiently long since the
  last clean. Returns the files that were removed.
  """

  global LAST_CACHE_CLEAN

  now = time.time()
  if auto and now < LAST_CACHE_CLEAN + config.CACHE_CLEAN_PERIOD:
    return

  out = []
  for file in config.CACHE_DIR.iterdir():
    if not file.is_file():
      continue
    if now - file.stat().st_mtime > config.CACHE_CLEAN_EXPIRY:
      out.append(file.name)
      file.unlink()

  LAST_CACHE_CLEAN = now
  return out

def filename(preamble, source, fmt):
  key = config.CACHE_KEY(preamble, source)
  format_ = config.formats[fmt]
  ext = mimetypes.guess_extension(format_['mimetype'])
  return f"{key}-{fmt}{ext}"

def cached(f):
  @wraps(f)
  def wrapper(filename, *a, **kw):
    CACHED = config.CACHE_DIR / filename
    if not CACHED.exists():
      out = f(*a, **kw)
      CACHED.write_bytes(out)
    CACHED.touch()
    return CACHED.read_bytes()
  return wrapper
