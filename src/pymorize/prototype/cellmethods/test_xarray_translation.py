from .cellmethods_parser import translate_to_xarray

test_cases = [
    ("area: mean", "da.mean(dim='area')"),
    ("area: mean where sea", "da.where(mask=='sea').mean(dim='area')"),
    (
        "area: mean where sea time: mean",
        "result_1 = da.where(mask=='sea').mean(dim='area')\n"
        "result = result_1.mean(dim='time')",
    ),
    (
        "area: mean time: maximum within days",
        "result_1 = da.mean(dim='area')\n"
        "result = result_1.groupby('days').maximum()",
    ),
    (
        "area: mean time: mean within days time: mean over days",
        "result_1 = da.mean(dim='area')\n"
        "result_2 = result_1.groupby('days').mean()\n"
        "result = result_2.mean(dim='days')",
    ),
    (
        "area: mean (comment: over land and sea ice) time: point",
        "result_1 = da.mean(dim='area')  # comment: over land and sea ice\n"
        "result = result_1.point(dim='time')",
    ),
    (
        "area: depth: time: mean",
        "result_1 = da.mean(dim='area')\n"
        "result_2 = result_1.mean(dim='depth')\n"
        "result = result_2.mean(dim='time')",
    ),
]


def test_translations():
    for input_text, expected in test_cases:
        result = translate_to_xarray(input_text)
        assert (
            result == expected
        ), f"\nInput: {input_text}\nExpected:\n{expected}\nGot:\n{result}"
        print(f"\nInput: {input_text}")
        print("Generated xarray code:")
        print(result)


if __name__ == "__main__":
    test_translations()
