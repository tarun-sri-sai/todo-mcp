import logging
import re
from hashlib import sha256

logging.getLogger()


class TodoParserError(Exception):
    pass


def _normalize_newlines(text):
    return re.sub(r"\r\n", "\n", text.strip())


def _split_blocks(text):
    text_blocks = re.split(r"\n[\n\s]*\n", text)
    return [block.split("\n") for block in text_blocks]


def _is_heading_block(block):
    if len(block) != 3 or len(block[0]) != 32 or block[0][0] != "*":
        return False

    start = set(block[0])
    end = set(block[-1])

    return (
        all(l == l.lstrip() and l for l in block) and
        len(start) == len(end) == 1 and
        start == end and
        len(block[0]) == len(block[-1])
    )


def _is_finished(block):
    return len(block) >= 2 and bool(re.match(r"^\[DONE\].*$", block[-1]))


def _parse_blocks(blocks):
    block_data = []
    for block in blocks:
        if _is_heading_block(block):
            block_data.append({
                "heading": block[1],
                "id": sha256(block[1].encode()).hexdigest()[:8]
            })
            continue

        curr_indent = None
        block_lines = []

        for line in block:
            indent_matches = re.match(r"^((?: {4})*)\S.*$", line)
            if not indent_matches:
                raise TodoParserError(f"invalid indentation for \"{line}\"")

            indent = indent_matches.group(1)
            if (
                curr_indent is not None and
                indent != curr_indent
            ):
                raise TodoParserError(
                    f"inconsistent indentation for \"{line}\""
                )

            if curr_indent is None:
                curr_indent = indent

            block_lines.append(line.strip())

        block_data.append({
            "level": len(curr_indent) // 4,
            "updates": block_lines,
            "id": sha256(block_lines[0].encode()).hexdigest()[:7],
            "finished": _is_finished(block_lines)
        })

    return block_data


def _validate_parents(block_data):
    curr_indents = [-1]
    curr_heading = ""
    blocks_since_heading = 0
    for block in block_data:
        if "heading" in block:
            blocks_since_heading = 0
            curr_indents = [-1]
            curr_heading = block["heading"]
            continue

        if blocks_since_heading == 0:
            if block.get("level") > 0:
                raise TodoParserError(
                    f"invalid first task for {curr_heading}"
                )

            curr_indents.append(0)
            blocks_since_heading += 1
            continue

        while curr_indents and curr_indents[-1] > block["level"]:
            curr_indents.pop()

        if (
            block["level"] != curr_indents[-1] and
            block["level"] - 1 != curr_indents[-1]
        ):
            raise TodoParserError(
                f"invalid parent task for \"{block['updates'][0]}\""
            )

        if block["level"] == curr_indents[-1] + 1:
            curr_indents.append(block["level"])

        blocks_since_heading += 1


def _validate_block_data(block_data):
    if len(block_data) == 0:
        raise TodoParserError("empty todo")

    if "heading" not in block_data[0]:
        logging.warning("first block must be a heading")

    _validate_parents(block_data)


def parse_todo(text):
    text = _normalize_newlines(text)
    blocks = _split_blocks(text)

    block_data = _parse_blocks(blocks)
    _validate_block_data(block_data)

    return block_data
