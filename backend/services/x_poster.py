"""
Light-weight poster for X (formerly Twitter).

Call `post_to_x("text")` whenever you need to tweet.
Requires OAuth 1.0 a user-context credentials; see
https://developer.x.com/ for details.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache

import tweepy                # pip install tweepy>=4.14.0
from dotenv import load_dotenv

load_dotenv()

_API_KEY            = os.getenv("X_API_KEY")
_API_KEY_SECRET     = os.getenv("X_API_KEY_SECRET")
_ACCESS_TOKEN       = os.getenv("X_ACCESS_TOKEN")
_ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")

_MAX_LEN = 280  # hard limit for X posts


@lru_cache                  # only build the client once per process
def _get_client() -> tweepy.API | None:
    if not all((_API_KEY, _API_KEY_SECRET, _ACCESS_TOKEN, _ACCESS_TOKEN_SECRET)):
        logging.warning("[x_poster] Missing X credentials – tweeting disabled")
        return None

    auth = tweepy.OAuth1UserHandler(
        _API_KEY, _API_KEY_SECRET, _ACCESS_TOKEN, _ACCESS_TOKEN_SECRET
    )
    return tweepy.API(auth, wait_on_rate_limit=True)


def post_to_x(text: str) -> None:
    """
    Publish a post on X.  Silently no-ops if credentials are absent
    or the API call fails.

    Parameters
    ----------
    text : str
        The message to publish (emoji / unicode allowed).  Anything
        longer than 280 characters will be truncated.
    """
    client = _get_client()
    if client is None:
        return

    try:
        client.update_status(status=text[:_MAX_LEN])
    except Exception as exc:  # tweepy raises its own subclasses of Exception
        logging.warning("[x_poster] Post failed: %s", exc)
