from __future__ import annotations

import io
import tokenize
from pathlib import Path


def normalized_tokens(source: str) -> list[str]:
    tokens: list[str] = []
    stream = io.StringIO(source)
    try:
        for token in tokenize.generate_tokens(stream.readline):
            if token.type in {
                tokenize.ENCODING,
                tokenize.ENDMARKER,
                tokenize.INDENT,
                tokenize.DEDENT,
                tokenize.NEWLINE,
                tokenize.NL,
                tokenize.COMMENT,
            }:
                continue
            if token.type == tokenize.NAME:
                tokens.append("NAME")
            elif token.type == tokenize.NUMBER:
                tokens.append("NUMBER")
            elif token.type == tokenize.STRING:
                tokens.append("STRING")
            else:
                tokens.append(token.string)
    except tokenize.TokenError:
        return source.split()
    return tokens


def shingles(tokens: list[str], width: int = 5) -> set[tuple[str, ...]]:
    if len(tokens) < width:
        return {tuple(tokens)} if tokens else set()
    return {tuple(tokens[index : index + width]) for index in range(len(tokens) - width + 1)}


def jaccard_similarity(left_source: str, right_source: str, width: int = 5) -> float:
    left = shingles(normalized_tokens(left_source), width)
    right = shingles(normalized_tokens(right_source), width)
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def file_similarity(left_path: str | Path, right_path: str | Path, width: int = 5) -> float:
    left = Path(left_path).read_text(encoding="utf-8")
    right = Path(right_path).read_text(encoding="utf-8")
    return jaccard_similarity(left, right, width=width)
