import pytest
from aioresponses import aioresponses

from app.core import config
from app.core.authentication import (
    GITHUB_ACCESS_TOKEN_URL,
    GITHUB_USER_URL,
    get_github_access_token,
    get_github_user,
)

pytestmark = pytest.mark.asyncio


async def test_get_github_access_token() -> None:
    with aioresponses() as m:
        code = "2823716201c373c9fa6e"
        url = (
            f"{GITHUB_ACCESS_TOKEN_URL}?client_id={config.GITHUB_CLIENT_ID}&client_secret={config.GITHUB_SECRET}"
            f"&code={code}"
        )

        payload = {
            "access_token": "gho_16C7e42F292c6912E7710c838347Ae178B4a",
            "scope": "repo,gist",
            "token_type": "bearer",
        }
        m.post(url, status=200, payload=payload)
        rv = await get_github_access_token(code)
        assert rv == payload["access_token"]


async def test_get_github_username() -> None:
    with aioresponses() as m:
        access_token = "gho_16C7e42F292c6912E7710c838347Ae178B4a"
        payload = {
            "login": "octocat",
            "id": 1,
            "node_id": "MDQ6VXNlcjE=",
            "avatar_url": "https://github.com/images/error/octocat_happy.gif",
            "gravatar_id": "",
            "url": "https://api.github.com/users/octocat",
            "html_url": "https://github.com/octocat",
            "followers_url": "https://api.github.com/users/octocat/followers",
            "following_url": "https://api.github.com/users/octocat/following{/other_user}",
            "gists_url": "https://api.github.com/users/octocat/gists{/gist_id}",
            "starred_url": "https://api.github.com/users/octocat/starred{/owner}{/repo}",
            "subscriptions_url": "https://api.github.com/users/octocat/subscriptions",
            "organizations_url": "https://api.github.com/users/octocat/orgs",
            "repos_url": "https://api.github.com/users/octocat/repos",
            "events_url": "https://api.github.com/users/octocat/events{/privacy}",
            "received_events_url": "https://api.github.com/users/octocat/received_events",
            "type": "User",
            "site_admin": False,
            "name": "monalisa octocat",
            "company": "GitHub",
            "blog": "https://github.com/blog",
            "location": "San Francisco",
            "email": "octocat@github.com",
            "hireable": False,
            "bio": "There once was...",
            "twitter_username": "monatheoctocat",
            "public_repos": 2,
            "public_gists": 1,
            "followers": 20,
            "following": 0,
            "created_at": "2008-01-14T04:33:35Z",
            "updated_at": "2008-01-14T04:33:35Z",
            "private_gists": 81,
            "total_private_repos": 100,
            "owned_private_repos": 100,
            "disk_usage": 10000,
            "collaborators": 8,
            "two_factor_authentication": True,
            "plan": {
                "name": "Medium",
                "space": 400,
                "private_repos": 20,
                "collaborators": 0,
            },
        }
        m.get(GITHUB_USER_URL, status=200, payload=payload)
        rv = await get_github_user(access_token)
        assert rv == payload["login"]
