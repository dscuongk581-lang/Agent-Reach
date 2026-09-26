# -*- coding: utf-8 -*-

import subprocess
import sys

from agent_reach.channels import ALL_CHANNELS, WebChannel, get_all_channels, get_channel


def test_registry_keeps_historical_order_and_count():
    channels = get_all_channels()
    assert len(channels) == 16
    assert [channel.name for channel in channels] == [
        "github",
        "twitter",
        "youtube",
        "reddit",
        "facebook",
        "instagram",
        "bilibili",
        "xiaohongshu",
        "linkedin",
        "boss",
        "xiaoyuzhou",
        "v2ex",
        "xueqiu",
        "rss",
        "exa_search",
        "web",
    ]
    assert len(ALL_CHANNELS) == 16


def test_direct_class_export_remains_compatible():
    assert WebChannel.__name__ == "WebChannel"
    assert get_channel("web").__class__ is WebChannel


def test_importing_registry_does_not_eager_load_optional_platforms():
    code = r"""
import sys
import agent_reach.channels as channels

boss = "agent_reach.channels.boss"
xueqiu = "agent_reach.channels.xueqiu"
web = "agent_reach.channels.web"

assert boss not in sys.modules
assert xueqiu not in sys.modules
assert web not in sys.modules

channel = channels.get_channel("web")
assert channel.name == "web"
assert web in sys.modules
assert boss not in sys.modules
assert xueqiu not in sys.modules

print("lazy-ok")
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "lazy-ok"
