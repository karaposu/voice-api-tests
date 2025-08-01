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
import pprint
import re  # noqa: F401
import json




from pydantic import BaseModel, ConfigDict, Field, StrictStr
from typing import Any, ClassVar, Dict, List, Optional
try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

class GetJournalAnalytics200ResponseAiInsights(BaseModel):
    """
    GetJournalAnalytics200ResponseAiInsights
    """ # noqa: E501
    growth_areas: Optional[List[StrictStr]] = Field(default=None, description="Areas where user is showing growth")
    focus_suggestions: Optional[List[StrictStr]] = Field(default=None, description="Areas AI suggests user focus on")
    coaching_recommendations: Optional[StrictStr] = Field(default=None, description="Personalized coaching recommendations")
    __properties: ClassVar[List[str]] = ["growth_areas", "focus_suggestions", "coaching_recommendations"]

    model_config = {
        "populate_by_name": True,
        "validate_assignment": True,
        "protected_namespaces": (),
    }


    def to_str(self) -> str:
        """Returns the string representation of the model using alias"""
        return pprint.pformat(self.model_dump(by_alias=True))

    def to_json(self) -> str:
        """Returns the JSON representation of the model using alias"""
        # TODO: pydantic v2: use .model_dump_json(by_alias=True, exclude_unset=True) instead
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        """Create an instance of GetJournalAnalytics200ResponseAiInsights from a JSON string"""
        return cls.from_dict(json.loads(json_str))

    def to_dict(self) -> Dict[str, Any]:
        """Return the dictionary representation of the model using alias.

        This has the following differences from calling pydantic's
        `self.model_dump(by_alias=True)`:

        * `None` is only added to the output dict for nullable fields that
          were set at model initialization. Other fields with value `None`
          are ignored.
        """
        _dict = self.model_dump(
            by_alias=True,
            exclude={
            },
            exclude_none=True,
        )
        return _dict

    @classmethod
    def from_dict(cls, obj: Dict) -> Self:
        """Create an instance of GetJournalAnalytics200ResponseAiInsights from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "growth_areas": obj.get("growth_areas"),
            "focus_suggestions": obj.get("focus_suggestions"),
            "coaching_recommendations": obj.get("coaching_recommendations")
        })
        return _obj


