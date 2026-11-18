import re

from leadengine.pipeline import demo
from leadengine.site import build


def test_site_is_self_contained(tmp_path):
    html = build(demo(tmp_path), tmp_path / "index.html").read_text()
    assert "Demo on synthetic data" in html
    assert not re.search(r'<script[^>]+src=|<link[^>]+href="http', html)
    for view in ("inbox", "approvals", "routing", "runs", "lead"):
        assert view in html
