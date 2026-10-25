"""Small owned export cache, separate from Gradio's download-file copies."""
from __future__ import annotations
import atexit
from pathlib import Path
import shutil
import tempfile
import threading
import time


class ArtifactCache:
    def __init__(self, parent=None, ttl=900, maximum=8, clock=time.monotonic, background=True):
        self.root = Path(tempfile.mkdtemp(prefix="form-exports-", dir=parent)).resolve()
        self.ttl, self.maximum, self.clock = ttl, maximum, clock
        self.batches = {}
        self.lock = threading.RLock()
        self.stopped = threading.Event()
        if background:
            threading.Thread(target=self._maintain, daemon=True, name="form-export-cleanup").start()
        atexit.register(self.close)

    def _remove(self, path):
        resolved = Path(path).resolve()
        # Recursive removal is restricted to directories allocated by this instance.
        if resolved.parent != self.root or resolved not in self.batches:
            return
        self.batches.pop(resolved, None)
        shutil.rmtree(resolved, ignore_errors=True)

    def purge(self):
        with self.lock:
            for path, created in list(self.batches.items()):
                if self.clock() - created >= self.ttl:
                    self._remove(path)

    def create(self):
        with self.lock:
            self.purge()
            while len(self.batches) >= self.maximum:
                self._remove(min(self.batches, key=self.batches.get))
            path = Path(tempfile.mkdtemp(prefix="batch-", dir=self.root)).resolve()
            self.batches[path] = self.clock()
            return path

    def contains(self, filename):
        with self.lock:
            self.purge()
            path = Path(filename).resolve()
            if path.parent.parent != self.root or path.parent not in self.batches or not path.is_file():
                return False
            self.batches[path.parent] = self.clock()
            return True

    def discard(self, path):
        with self.lock:
            self._remove(path)

    def _maintain(self):
        while not self.stopped.wait(60):
            self.purge()

    def close(self):
        self.stopped.set()
        with self.lock:
            for path in list(self.batches):
                self._remove(path)
            # Only the empty, uniquely allocated owner directory may be removed.
            try:
                self.root.rmdir()
            except OSError:
                pass
