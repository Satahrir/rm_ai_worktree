import re
from copy import deepcopy

from rm_ref.schema.errors import SchemaError
from rm_ref.schema.field import FieldDefinition, _MISSING
from rm_ref.schema.schema import SchemaDefinition


_VALID_SCOPES = ("global", "packet", "cell")


def normalize_field_name(name):
    if not isinstance(name, str) or not name.strip():
        raise SchemaError("field name must be a non-empty string, got {0!r}".format(name))
    parts = []
    for part in name.strip().split("."):
        normalized = re.sub(r"[^A-Za-z0-9_]+", "_", part)
        normalized = re.sub(r"_+", "_", normalized).strip("_").lower()
        if not normalized:
            raise SchemaError("field name {0!r} normalizes to an empty name".format(name))
        parts.append(normalized)
    return ".".join(parts)


def _require_integer(value, label, schema_id, field_name=None):
    if isinstance(value, bool) or not isinstance(value, int):
        location = "schema {0}".format(schema_id)
        if field_name is not None:
            location += " field {0}".format(field_name)
        raise SchemaError(
            "{0} {1} must be an integer, got {2!r}".format(
                location, label, value
            )
        )
    return value


def _is_reserved(field_dict, original_name):
    if "reserved" in field_dict:
        return bool(field_dict["reserved"])
    compact = re.sub(r"[^A-Za-z0-9]", "", original_name).lower()
    return compact.startswith("rsv") or compact.startswith("reserved")


def _base_field_data(field_dict, schema_id, word_width, word_count):
    if not isinstance(field_dict, dict):
        raise SchemaError(
            "schema {0} field descriptor must be a dict, got {1!r}".format(
                schema_id, field_dict
            )
        )
    if "name" not in field_dict:
        raise SchemaError("schema {0} field is missing name".format(schema_id))

    name = field_dict["name"]
    original_name = field_dict.get("original_name", name)
    if not isinstance(original_name, str) or not original_name.strip():
        raise SchemaError(
            "schema {0} field {1!r} has invalid original_name {2!r}".format(
                schema_id, name, original_name
            )
        )
    group = field_dict.get("group")
    instance = field_dict.get("instance")
    explicit_normalized_name = field_dict.get("normalized_name")
    normalized_name = normalize_field_name(explicit_normalized_name or name)

    word = field_dict.get("word")
    msb = field_dict.get("msb")
    lsb = field_dict.get("lsb")
    width = field_dict.get("width")

    if word is not None:
        word = _require_integer(word, "word", schema_id, name)
        if word < 0 or word >= word_count:
            raise SchemaError(
                "schema {0} field {1} has invalid word index {2}; "
                "expected 0..{3}".format(schema_id, name, word, word_count - 1)
            )

    if (msb is None) != (lsb is None):
        raise SchemaError(
            "schema {0} field {1} must define both msb and lsb".format(
                schema_id, name
            )
        )
    implied_width = None
    if msb is not None:
        msb = _require_integer(msb, "msb", schema_id, name)
        lsb = _require_integer(lsb, "lsb", schema_id, name)
        if msb < lsb or lsb < 0 or msb >= word_width:
            raise SchemaError(
                "schema {0} field {1} has invalid bit range msb={2} lsb={3} "
                "for word_width={4}".format(
                    schema_id, name, msb, lsb, word_width
                )
            )
        implied_width = msb - lsb + 1

    if width is None:
        width = implied_width
    else:
        width = _require_integer(width, "width", schema_id, name)
        if width <= 0:
            raise SchemaError(
                "schema {0} field {1} width must be positive, got {2}".format(
                    schema_id, name, width
                )
            )
        if implied_width is not None and width != implied_width:
            raise SchemaError(
                "schema {0} field {1} width mismatch: declared width={2} "
                "but msb/lsb imply width={3}".format(
                    schema_id, name, width, implied_width
                )
            )

    enum = field_dict.get("enum") or {}
    if not isinstance(enum, dict):
        raise SchemaError(
            "schema {0} field {1} enum must be a dict, got {2!r}".format(
                schema_id, name, enum
            )
        )
    enum = deepcopy(enum)
    for enum_name, enum_value in enum.items():
        if not isinstance(enum_name, str) or not enum_name:
            raise SchemaError(
                "schema {0} field {1} has invalid enum name {2!r}".format(
                    schema_id, name, enum_name
                )
            )
        _require_integer(enum_value, "enum value", schema_id, name)

    minimum = field_dict.get("min")
    maximum = field_dict.get("max")
    if minimum is not None:
        _require_integer(minimum, "min", schema_id, name)
    if maximum is not None:
        _require_integer(maximum, "max", schema_id, name)
    if minimum is not None and maximum is not None and minimum > maximum:
        raise SchemaError(
            "schema {0} field {1} has min={2} greater than max={3}".format(
                schema_id, name, minimum, maximum
            )
        )

    scope = field_dict.get("scope", "cell")
    if scope not in _VALID_SCOPES:
        raise SchemaError(
            "schema {0} field {1} has invalid scope {2!r}; expected one of {3}".format(
                schema_id, name, scope, _VALID_SCOPES
            )
        )

    reserved = _is_reserved(field_dict, original_name)
    default = field_dict.get("default", _MISSING)
    return {
        "name": name,
        "normalized_name": normalized_name,
        "original_name": original_name,
        "word": word,
        "msb": msb,
        "lsb": lsb,
        "width": width,
        "enum": enum,
        "default": default,
        "minimum": minimum,
        "maximum": maximum,
        "description": field_dict.get("description", ""),
        "instance": instance,
        "group": group,
        "reserved": reserved,
        "required": bool(field_dict.get("required", False)),
        "scope": scope,
        "_explicit_normalized_name": explicit_normalized_name is not None,
    }


def _disambiguate_names(field_data, schema_id):
    grouped = {}
    for data in field_data:
        grouped.setdefault(data["normalized_name"], []).append(data)

    for normalized_name, duplicates in grouped.items():
        if len(duplicates) == 1:
            continue
        for data in duplicates:
            if data["_explicit_normalized_name"]:
                continue
            if data["group"]:
                data["normalized_name"] = "{0}.{1}".format(
                    normalize_field_name(data["group"]),
                    normalize_field_name(data["original_name"]),
                )
            elif data["instance"] is not None:
                data["normalized_name"] = "{0}.instance{1}".format(
                    normalize_field_name(data["original_name"]),
                    data["instance"],
                )

    seen = {}
    for data in field_data:
        normalized_name = data["normalized_name"]
        if normalized_name in seen:
            raise SchemaError(
                "schema {0} has duplicate normalized field name {1}".format(
                    schema_id, normalized_name
                )
            )
        seen[normalized_name] = True


def normalize_schema(schema_dict):
    if not isinstance(schema_dict, dict):
        raise SchemaError("schema must be a dict, got {0!r}".format(schema_dict))

    schema_id = schema_dict.get("schema_id")
    if not isinstance(schema_id, str) or not schema_id.strip():
        raise SchemaError(
            "schema_id must be a non-empty string, got {0!r}".format(schema_id)
        )

    word_width = _require_integer(
        schema_dict.get("word_width"), "word_width", schema_id
    )
    word_count = _require_integer(
        schema_dict.get("word_count"), "word_count", schema_id
    )
    if word_width <= 0 or word_count <= 0:
        raise SchemaError(
            "schema {0} word_width and word_count must be positive".format(
                schema_id
            )
        )

    raw_fields = schema_dict.get("fields")
    if not isinstance(raw_fields, (list, tuple)):
        raise SchemaError(
            "schema {0} fields must be a list or tuple".format(schema_id)
        )

    field_data = [
        _base_field_data(item, schema_id, word_width, word_count)
        for item in raw_fields
    ]
    _disambiguate_names(field_data, schema_id)

    fields = []
    for data in field_data:
        data.pop("_explicit_normalized_name")
        fields.append(FieldDefinition(**data))

    metadata = dict(
        (key, deepcopy(value))
        for key, value in schema_dict.items()
        if key not in ("schema_id", "word_width", "word_count", "fields")
    )
    return SchemaDefinition(
        schema_id=schema_id,
        word_width=word_width,
        word_count=word_count,
        fields=fields,
        metadata=metadata,
    )
