"""Tests model module."""
import datetime
from typing import Any
from typing import Dict

from flyswot import models

# flake8: noqa


def test_app_exists() -> None:
    """It exists"""
    assert models.app


single_github_release_dict: Dict[Any, Any] = {
    "url": "https://api.github.com/repos/davanstrien/learn-onnx/releases/40756746",
    "assets_url": "https://api.github.com/repos/davanstrien/learn-onnx/releases/40756746/assets",
    "upload_url": "https://uploads.github.com/repos/davanstrien/learn-onnx/releases/40756746/assets{?name,label}",
    "html_url": "https://github.com/davanstrien/learn-onnx/releases/tag/2021.03.31",
    "id": 40756746,
    "author": {
        "login": "davanstrien",
        "id": 8995957,
        "node_id": "MDQ6VXNlcjg5OTU5NTc=",
        "avatar_url": "https://avatars.githubusercontent.com/u/8995957?v=4",
        "gravatar_id": "",
        "url": "https://api.github.com/users/davanstrien",
        "html_url": "https://github.com/davanstrien",
        "followers_url": "https://api.github.com/users/davanstrien/followers",
        "following_url": "https://api.github.com/users/davanstrien/following{/other_user}",
        "gists_url": "https://api.github.com/users/davanstrien/gists{/gist_id}",
        "starred_url": "https://api.github.com/users/davanstrien/starred{/owner}{/repo}",
        "subscriptions_url": "https://api.github.com/users/davanstrien/subscriptions",
        "organizations_url": "https://api.github.com/users/davanstrien/orgs",
        "repos_url": "https://api.github.com/users/davanstrien/repos",
        "events_url": "https://api.github.com/users/davanstrien/events{/privacy}",
        "received_events_url": "https://api.github.com/users/davanstrien/received_events",
        "type": "User",
        "site_admin": False,
    },
    "node_id": "MDc6UmVsZWFzZTQwNzU2NzQ2",
    "tag_name": "2021.03.31",
    "target_commitish": "main",
    "name": "2021.03.31",
    "draft": False,
    "prerelease": False,
    "created_at": "2021-03-28T18:33:30Z",
    "published_at": "2021-03-31T12:47:12Z",
    "assets": [
        {
            "url": "https://api.github.com/repos/davanstrien/learn-onnx/releases/assets/34258568",
            "id": 34258568,
            "node_id": "MDEyOlJlbGVhc2VBc3NldDM0MjU4NTY4",
            "name": "2021-03-31-model.onnx",
            "label": None,
            "uploader": {
                "login": "davanstrien",
                "id": 8995957,
                "node_id": "MDQ6VXNlcjg5OTU5NTc=",
                "avatar_url": "https://avatars.githubusercontent.com/u/8995957?v=4",
                "gravatar_id": "",
                "url": "https://api.github.com/users/davanstrien",
                "html_url": "https://github.com/davanstrien",
                "followers_url": "https://api.github.com/users/davanstrien/followers",
                "following_url": "https://api.github.com/users/davanstrien/following{/other_user}",
                "gists_url": "https://api.github.com/users/davanstrien/gists{/gist_id}",
                "starred_url": "https://api.github.com/users/davanstrien/starred{/owner}{/repo}",
                "subscriptions_url": "https://api.github.com/users/davanstrien/subscriptions",
                "organizations_url": "https://api.github.com/users/davanstrien/orgs",
                "repos_url": "https://api.github.com/users/davanstrien/repos",
                "events_url": "https://api.github.com/users/davanstrien/events{/privacy}",
                "received_events_url": "https://api.github.com/users/davanstrien/received_events",
                "type": "User",
                "site_admin": False,
            },
            "content_type": "application/octet-stream",
            "state": "uploaded",
            "size": 5076633,
            "download_count": 0,
            "created_at": "2021-03-31T12:45:59Z",
            "updated_at": "2021-03-31T12:46:03Z",
            "browser_download_url": "https://github.com/davanstrien/learn-onnx/releases/download/2021.03.31/2021-03-31-model.onnx",
        }
    ],
    "tarball_url": "https://api.github.com/repos/davanstrien/learn-onnx/tarball/2021.03.31",
    "zipball_url": "https://api.github.com/repos/davanstrien/learn-onnx/zipball/2021.03.31",
    "body": "\r\n# Description \r\n\r\nblah blah blah\r\n\r\n## Model Metadata\r\n\r\n### Classes\r\n\r\ncat, dog, mouse\r\n\r\n### Scores\r\n\r\n| class | f1 |\r\n|----|---|\r\n|cat | 0.9 |",
}


def test_get_release_metadata_exists(test_dict: Dict[Any, Any] = single_github_release_dict) -> None:
    """It exists"""
    release = models.get_release_metadata(test_dict)
    assert release


def test_get_release_metadata_return_values(test_dict: Dict[Any, Any] = single_github_release_dict) -> None:
    """It returns expected values"""
    release = models.get_release_metadata(test_dict)
    assert type(release.html_url) == str
    assert release.html_url == test_dict["html_url"]
    assert type(release.body) == str
    assert release.body == test_dict["body"]
    assert type(release.updated_at) == datetime.datetime
    assert release.browser_download_url.startswith("https")
