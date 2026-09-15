from django.utils.translation import get_language


class LocalizedContentSerializerMixin:
    """Expose the requested language while retaining Persian as a safe fallback.

    Models store the primary Persian value and an optional ``*_en`` value. Public
    API responses use ``Accept-Language: en`` to substitute English content when
    it is available, without forcing frontend clients to map duplicate fields.
    """

    localized_fields = ()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        language = (get_language() or "").lower()
        use_english = language.startswith("en")

        for field_name in self.localized_fields:
            english_name = f"{field_name}_en"
            english_value = data.get(english_name)
            if use_english and english_value not in (None, "", [], {}):
                data[field_name] = english_value
            data.pop(english_name, None)

        return data
