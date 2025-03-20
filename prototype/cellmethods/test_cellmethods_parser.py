import pytest
from cellmethods_parser import CellMethodsLexer, parse_cell_methods

test_cases = [
    (
        "area: depth: time: mean",
        [
            [('DIMENSION', 'area'), ('ACTION', 'mean')],
            [('DIMENSION', 'depth'), ('ACTION', 'mean')],
            [('DIMENSION', 'time'), ('ACTION', 'mean')]
        ]
    ),
    (
        "area: mean",
        [
            [('DIMENSION', 'area'), ('ACTION', 'mean')]
        ]
    ),
    (
        "area: mean (comment: over land and sea ice) time: point",
        [
            [('DIMENSION', 'area'), ('ACTION', 'mean'), ('SCOPE', 'comment: over land and sea ice')],
            [('DIMENSION', 'time'), ('ACTION', 'point')]
        ]
    ),
    (
        "area: mean time: maximum",
        [
            [('DIMENSION', 'area'), ('ACTION', 'mean')],
            [('DIMENSION', 'time'), ('ACTION', 'maximum')]
        ]
    ),
    (
        "area: mean time: maximum within days time: mean over days",
        [
            [('DIMENSION', 'area'), ('ACTION', 'mean')],
            [('DIMENSION', 'time'), ('ACTION', 'maximum'), ('CONSTRAINT', 'within'), ('SELECTION', 'days')],
            [('DIMENSION', 'time'), ('ACTION', 'mean'), ('CONSTRAINT', 'over'), ('SELECTION', 'days')]
        ]
    ),
    (
        "area: mean time: mean within days time: mean over days",
        [
            [('DIMENSION', 'area'), ('ACTION', 'mean')],
            [('DIMENSION', 'time'), ('ACTION', 'mean'), ('CONSTRAINT', 'within'), ('SELECTION', 'days')],
            [('DIMENSION', 'time'), ('ACTION', 'mean'), ('CONSTRAINT', 'over'), ('SELECTION', 'days')]
        ]
    ),
    (
        "area: mean time: mean within hours time: maximum over hours",
        [
            [('DIMENSION', 'area'), ('ACTION', 'mean')],
            [('DIMENSION', 'time'), ('ACTION', 'mean'), ('CONSTRAINT', 'within'), ('SELECTION', 'hours')],
            [('DIMENSION', 'time'), ('ACTION', 'maximum'), ('CONSTRAINT', 'over'), ('SELECTION', 'hours')]
        ]
    ),
    (
        "area: mean time: mean within years time: mean over years",
        [
            [('DIMENSION', 'area'), ('ACTION', 'mean')],
            [('DIMENSION', 'time'), ('ACTION', 'mean'), ('CONSTRAINT', 'within'), ('SELECTION', 'years')],
            [('DIMENSION', 'time'), ('ACTION', 'mean'), ('CONSTRAINT', 'over'), ('SELECTION', 'years')]
        ]
    ),
    (
        "area: mean time: minimum",
        [
            [('DIMENSION', 'area'), ('ACTION', 'mean')],
            [('DIMENSION', 'time'), ('ACTION', 'minimum')]
        ]
    ),
    (
        "area: mean time: minimum within days time: mean over days",
        [
            [('DIMENSION', 'area'), ('ACTION', 'mean')],
            [('DIMENSION', 'time'), ('ACTION', 'minimum'), ('CONSTRAINT', 'within'), ('SELECTION', 'days')],
            [('DIMENSION', 'time'), ('ACTION', 'mean'), ('CONSTRAINT', 'over'), ('SELECTION', 'days')]
        ]
    ),
    (
        "area: mean time: point",
        [
            [('DIMENSION', 'area'), ('ACTION', 'mean')],
            [('DIMENSION', 'time'), ('ACTION', 'point')]
        ]
    ),
    (
        "area: mean time: sum",
        [
            [('DIMENSION', 'area'), ('ACTION', 'mean')],
            [('DIMENSION', 'time'), ('ACTION', 'sum')]
        ]
    )
]


@pytest.mark.parametrize("input_text,expected_output", test_cases)
def test_cell_methods_parser(input_text, expected_output):
    result = parse_cell_methods(input_text)
    assert result == expected_output, f"\nInput: {input_text}\nExpected: {expected_output}\nGot: {result}"


def test_lexer_tokens():
    lexer = CellMethodsLexer()
    # Test each token type is recognized correctly
    test_tokens = {
        'DIMENSION': ['area:', 'time:', 'depth:', 'grid_longitude:', 'longitude:', 'latitude:'],
        'ACTION': ['mean', 'minimum', 'maximum', 'sum', 'point'],
        'REGION': ['land', 'sea', 'sea_ice', 'snow', 'ice_sheet', 'grounded_ice_sheet', 'crops', 'ice_free_sea'],
        'SELECTION': ['all_area_types', 'days', 'years', 'hours'],
        'CONSTRAINT': ['within', 'over', 'where'],
        'SCOPE': ['(comment text)', '(top 100m only)']
    }

    for token_type, values in test_tokens.items():
        for value in values:
            tokens = list(lexer.tokenize(value))
            assert len(tokens) == 1, f"Expected 1 token for {value}, got {len(tokens)}"
            token = tokens[0]
            assert token.type == token_type, f"Expected token type {token_type} for {value}, got {token.type}"
            if token_type == 'DIMENSION':
                assert token.value == value[:-1], f"Expected value {value[:-1]} for {value}, got {token.value}"
            elif token_type == 'SCOPE':
                assert token.value == value[1:-1], f"Expected value {value[1:-1]} for {value}, got {token.value}"
            else:
                assert token.value == value, f"Expected value {value}, got {token.value}"
