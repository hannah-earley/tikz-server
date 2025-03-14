import time
import mimetypes
import config
from functools import wraps

def clean_time():
  """
  Cleans the cache of files that haven't been updated or accessed recently. If
  `auto` is True, then only clean if it has been sufficiently long since the
  last clean. Returns the files that were removed.
  """

  now = time.time()
  out = []
  for file in config.CACHE_DIR.iterdir():
    if not file.is_file():
      continue
    if now - file.lstat().st_mtime > config.CACHE_CLEAN_EXPIRY:
      out.append(file.name)
      file.unlink()

  return out

def clean_space():
  """
  Clean the cache of files that are both old _and_ exceed the maximum cache
  size allocated.
  """

  now = time.time()
  files = []
  total_size = 0
  for file in config.CACHE_DIR.iterdir():
    if not file.is_file():
      continue

    stat = file.lstat()
    mtime = stat.st_mtime
    size = stat.st_size
    total_size += size
    if now - mtime > config.CACHE_CLEAN_EXPIRY:
      files.append((mtime, size, file))

  out = []
  files.sort()
  to_clean = total_size - config.CACHE_CLEAN_SIZE
  for _, size, file in files:
    if to_clean <= 0:
      break
    to_clean -= size
    out.append(file.name)
    file.unlink()

  return out

LAST_CACHE_CLEAN = 0
def clean(auto=False, cleaner=clean_space):
  global LAST_CACHE_CLEAN

  now = time.time()
  if auto and now < LAST_CACHE_CLEAN + config.CACHE_CLEAN_PERIOD:
    return []

  out = cleaner()
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
