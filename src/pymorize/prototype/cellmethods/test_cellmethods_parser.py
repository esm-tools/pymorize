from .prototype.cellmethods.cellmethods_parser import parse_cell_methods


def test_single_statement_with_just_action():
    text = "area: mean"
    result = parse_cell_methods(text)
    expected = [[("DIMENSION", "area"), ("FUNCTION", "mean")]]
    assert result == expected


def test_single_statement_with_action_and_constraint():
    text = "area: mean where land"
    result = parse_cell_methods(text)
    expected = [
        [
            ("DIMENSION", "area"),
            ("FUNCTION", "mean"),
            ("CONSTRAINT", "where"),
            ("AREATYPE", "land"),
        ]
    ]
    assert result == expected


def test_single_statement_with_action_and_constraint_and_comment():
    text = "area: mean where land (comment: mask=landFrac)"
    result = parse_cell_methods(text)
    expected = [
        [
            ("DIMENSION", "area"),
            ("FUNCTION", "mean"),
            ("CONSTRAINT", "where"),
            ("AREATYPE", "land"),
            ("COMMENT", "mask=landFrac"),
        ]
    ]
    assert result == expected


def test_many_dimensions_map_to_single_function():
    text = "area: depth: time: mean"
    result = parse_cell_methods(text)
    expected = [
        [
            ("DIMENSION", "area"),
            ("FUNCTION", "mean"),
        ],
        [
            ("DIMENSION", "depth"),
            ("FUNCTION", "mean"),
        ],
        [
            ("DIMENSION", "time"),
            ("FUNCTION", "mean"),
        ],
    ]
    assert result == expected


def test_statements_with_comment_in_middle():
    text = "longitude: sum (comment: basin sum [along zig-zag grid path]) depth: sum time: mean"
    result = parse_cell_methods(text)
    expected = [
        [
            ("DIMENSION", "longitude"),
            ("FUNCTION", "sum"),
            ("COMMENT", "basin sum along zig-zag grid path"),
        ],
        [
            ("DIMENSION", "depth"),
            ("FUNCTION", "sum"),
        ],
        [
            ("DIMENSION", "time"),
            ("FUNCTION", "mean"),
        ],
    ]
    assert result == expected


def test_time_dimension_constraint_omits_areatpye():
    text = "area: time: mean where cloud"
    result = parse_cell_methods(text)
    expected = [
        [
            ("DIMENSION", "area"),
            ("FUNCTION", "mean"),
            ("CONSTRAINT", "where"),
            ("AREATYPE", "cloud"),
        ],
        [
            ("DIMENSION", "time"),
            ("FUNCTION", "mean"),
        ],
    ]
    assert result == expected


def test_multiple_contraints():
    text = "area: mean where land over all_area_types time: mean"
    result = parse_cell_methods(text)
    expected = [
        [
            ("DIMENSION", "area"),
            ("FUNCTION", "mean"),
            ("CONSTRAINT", "where"),
            ("AREATYPE", "land"),
            ("CONSTRAINT", "over"),
            ("SELECTION", "all_area_types"),
        ],
        [
            ("DIMENSION", "time"),
            ("FUNCTION", "mean"),
        ],
    ]
    assert result == expected


def test_statements_with_repeated_dimensions():
    text = "area: mean where crops time: minimum within days time: mean over days"
    result = parse_cell_methods(text)
    expected = [
        [
            ("DIMENSION", "area"),
            ("FUNCTION", "mean"),
            ("CONSTRAINT", "where"),
            ("AREATYPE", "crops"),
        ],
        [
            ("DIMENSION", "time"),
            ("FUNCTION", "minimum"),
            ("CONSTRAINT", "within"),
            ("SELECTION", "days"),
        ],
        [
            ("DIMENSION", "time"),
            ("FUNCTION", "mean"),
            ("CONSTRAINT", "over"),
            ("SELECTION", "days"),
        ],
    ]
    assert result == expected


def test_area_dimension_contraint_omits_selection():
    text = "area: time: mean over days"
    result = parse_cell_methods(text)
    expected = [
        [
            ("DIMENSION", "area"),
            ("FUNCTION", "mean"),
        ],
        [
            ("DIMENSION", "time"),
            ("FUNCTION", "mean"),
            ("CONSTRAINT", "over"),
            ("SELECTION", "days"),
        ],
    ]
    assert result == expected
