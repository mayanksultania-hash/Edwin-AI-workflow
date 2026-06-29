"""Read and write Action Group YAML."""

from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:
    yaml = None

from ai_workflow.models.action_group import ActionGroup, ActionGroupValidationError


def load_action_group_yaml(yaml_text: str) -> ActionGroup:
    data = _parse_yaml(yaml_text)
    return ActionGroup.from_dict(data)


def load_action_group_yaml_file(path: Path) -> ActionGroup:
    return load_action_group_yaml(path.read_text(encoding="utf-8"))


def dump_action_group_yaml(action_group: ActionGroup) -> str:
    data = action_group.to_dict()
    if yaml:
        return yaml.safe_dump(data, sort_keys=False)

    return _dump_simple_yaml(data)


def write_action_group_yaml_file(action_group: ActionGroup, path: Path) -> None:
    path.write_text(dump_action_group_yaml(action_group), encoding="utf-8")


def _parse_yaml(yaml_text: str) -> dict[str, Any]:
    if yaml:
        data = yaml.safe_load(yaml_text) or {}
    else:
        data = _parse_simple_yaml(yaml_text)

    if not isinstance(data, dict):
        raise ActionGroupValidationError("action group YAML must be an object")

    return data


def _parse_simple_yaml(yaml_text: str) -> dict[str, Any]:
    lines = _prepare_lines(yaml_text)
    if not lines:
        return {}

    data, next_index = _parse_block(lines, 0, lines[0][0])
    if next_index != len(lines):
        raise ActionGroupValidationError("could not parse full action group YAML")
    if not isinstance(data, dict):
        raise ActionGroupValidationError("action group YAML must be an object")

    return data


def _prepare_lines(yaml_text: str) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    for raw_line in yaml_text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(line.lstrip(" "))
        lines.append((indent, stripped))

    return lines


def _parse_block(
    lines: list[tuple[int, str]],
    index: int,
    indent: int,
) -> tuple[Any, int]:
    if lines[index][1].startswith("- "):
        return _parse_list(lines, index, indent)

    return _parse_dict(lines, index, indent)


def _parse_dict(
    lines: list[tuple[int, str]],
    index: int,
    indent: int,
) -> tuple[dict[str, Any], int]:
    data: dict[str, Any] = {}

    while index < len(lines):
        current_indent, text = lines[index]
        if current_indent < indent:
            break
        if current_indent > indent:
            raise ActionGroupValidationError(f"unexpected YAML indentation: {text}")
        if text.startswith("- "):
            break

        key, raw_value = _split_key_value(text)
        index += 1

        if raw_value:
            data[key] = _parse_scalar(raw_value)
            continue

        if index >= len(lines) or lines[index][0] <= current_indent:
            data[key] = None
            continue

        data[key], index = _parse_block(lines, index, lines[index][0])

    return data, index


def _parse_list(
    lines: list[tuple[int, str]],
    index: int,
    indent: int,
) -> tuple[list[Any], int]:
    items: list[Any] = []

    while index < len(lines):
        current_indent, text = lines[index]
        if current_indent < indent:
            break
        if current_indent > indent:
            raise ActionGroupValidationError(f"unexpected YAML indentation: {text}")
        if not text.startswith("- "):
            break

        item_text = text[2:].strip()
        index += 1

        if not item_text:
            if index >= len(lines) or lines[index][0] <= current_indent:
                items.append(None)
                continue
            item, index = _parse_block(lines, index, lines[index][0])
            items.append(item)
            continue

        if ":" not in item_text:
            items.append(_parse_scalar(item_text))
            continue

        key, raw_value = _split_key_value(item_text)
        item_data: dict[str, Any] = {
            key: _parse_scalar(raw_value) if raw_value else None,
        }

        if index < len(lines) and lines[index][0] > current_indent:
            nested, index = _parse_dict(lines, index, lines[index][0])
            item_data.update(nested)

        items.append(item_data)

    return items, index


def _dump_simple_yaml(data: Any, indent: int = 0) -> str:
    lines = _dump_lines(data, indent)
    return "\n".join(lines) + "\n"


def _dump_lines(data: Any, indent: int) -> list[str]:
    prefix = " " * indent

    if isinstance(data, dict):
        lines: list[str] = []
        for key, value in data.items():
            if isinstance(value, dict | list):
                lines.append(f"{prefix}{key}:")
                lines.extend(_dump_lines(value, indent + 2))
            else:
                lines.append(f"{prefix}{key}: {_format_scalar(value)}")
        return lines

    if isinstance(data, list):
        lines = []
        for item in data:
            if isinstance(item, dict):
                item_items = list(item.items())
                if not item_items:
                    lines.append(f"{prefix}- {{}}")
                    continue

                first_key, first_value = item_items[0]
                if isinstance(first_value, dict | list):
                    lines.append(f"{prefix}- {first_key}:")
                    lines.extend(_dump_lines(first_value, indent + 4))
                else:
                    lines.append(f"{prefix}- {first_key}: {_format_scalar(first_value)}")

                for key, value in item_items[1:]:
                    if isinstance(value, dict | list):
                        lines.append(f"{prefix}  {key}:")
                        lines.extend(_dump_lines(value, indent + 4))
                    else:
                        lines.append(f"{prefix}  {key}: {_format_scalar(value)}")
                continue

            lines.append(f"{prefix}- {_format_scalar(item)}")

        return lines

    return [f"{prefix}{_format_scalar(data)}"]


def _split_key_value(text: str) -> tuple[str, str]:
    if ":" not in text:
        raise ActionGroupValidationError(f"expected YAML key/value line: {text}")

    key, value = text.split(":", 1)
    key = key.strip()
    if not key:
        raise ActionGroupValidationError(f"expected YAML key before colon: {text}")

    return key, value.strip()


def _parse_scalar(value: str) -> Any:
    if value in {"", "null", "Null", "NULL", "~"}:
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
        return int(value)

    return value


def _format_scalar(value: Any) -> str:
    if value is None:
        return ""
    if value is True:
        return "true"
    if value is False:
        return "false"

    return str(value)
