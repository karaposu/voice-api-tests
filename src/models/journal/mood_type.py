# coding: utf-8

"""
    PowerManifest Journal API

    API for managing personal journal entries in the PowerManifest life coaching app

    The version of the OpenAPI document: 1.0.0
    Contact: api@powermanifest.com
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


from __future__ import annotations
import json
import pprint
import re  # noqa: F401
from enum import Enum



try:
    from typing import Self
except ImportError:
    from typing_extensions import Self


class MoodType(str, Enum):
    """
    User's emotional state when writing the entry
    """

    """
    allowed enum values
    """
    GREAT = 'great'
    GOOD = 'good'
    OKAY = 'okay'
    LOW = 'low'
    MIXED = 'mixed'

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        """Create an instance of MoodType from a JSON string"""
        return cls(json.loads(json_str))


