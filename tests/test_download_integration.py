import sys
from pathlib import Path
import importlib.util
from types import SimpleNamespace

# Ensure repository root is on sys.path so `src` is importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import asyncio

from src.ingest.download_manager import DownloadPipeline


def test_async_downloader_invoked(monkeypatch, tmp_path):
    """Smoke test: ensure the async `StandardsDownloader` from data source directories is invoked.

    This test patches `importlib.util.spec_from_file_location` to provide a
    fake module with a `StandardsDownloader` that records when its `run`
    coroutine is executed. We set `pipeline.downloaders = []` to avoid
    performing any synchronous network downloads from the builtin
    downloaders.
    """
    invoked = {"ok": False}

    class FakeDownloader:
        def __init__(self, output_dir=None):
            self.output_dir = output_dir

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def run(self, *args, **kwargs):
            invoked["ok"] = True

    class FakeLoader:
        def exec_module(self, mod):
            setattr(mod, "StandardsDownloader", FakeDownloader)

    def fake_spec_from_file_location(name, path):
        return SimpleNamespace(loader=FakeLoader())

    monkeypatch.setattr(importlib.util, "spec_from_file_location", fake_spec_from_file_location)

    # Ensure asyncio.run executes our coroutine even if pytest has an event loop running
    def _fake_asyncio_run(coro):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            try:
                loop.close()
            except Exception:
                pass

    monkeypatch.setattr(asyncio, 'run', _fake_asyncio_run)

    # Also ensure the explicit import path `data_raw.src.downloader` resolves to our fake
    # module so the direct import attempt in `download_manager` uses FakeDownloader.
    import types
    fake_module = types.ModuleType('data_raw.src.downloader')
    setattr(fake_module, 'StandardsDownloader', FakeDownloader)
    sys.modules['data_raw.src.downloader'] = fake_module

    pipeline = DownloadPipeline(skip_large_files=True)
    # Avoid executing synchronous downloader.download() calls which may perform network IO
    pipeline.downloaders = []

    summary = pipeline.run()

    assert invoked["ok"] is True
    assert isinstance(summary, dict)
