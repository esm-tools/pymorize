from sly import Lexer, Parser


class CellMethodsLexer(Lexer):
    # set of token names
    tokens = {DIMENSION, ACTION, REGION, CONSTRAINT, SCOPE, SELECTION}  # noqa: F821

    # string containing ignored characters between token
    ignore = " \t"

    # Regular expression rules for tokens
    DIMENSION = r"area:|time:|grid_longitude:|longitude:|latitude:|depth:"
    ACTION = r"mean|minimum|maximum|sum|point"
    CONSTRAINT = r"within|over|where"  # Must come before REGION/SELECTION
    REGION = r"[a-z_]+(?![a-z_])"  # Match words with underscores
    SELECTION = r"[a-z_]+(?![a-z_])"  # Match words with underscores

    def DIMENSION(self, t):  # noqa: F811
        t.value = t.value[:-1]
        return t

    def REGION(self, t):  # noqa: F811
        if t.value not in (
            "land",
            "sea",
            "sea_ice",
            "snow",
            "ice_sheet",
            "grounded_ice_sheet",
            "crops",
            "ice_free_sea",
        ):
            t.type = "SELECTION"
        return t

    @_(r"\(.*?\)")  # noqa: F821
    def SCOPE(self, t):
        t.value = t.value[1:-1]
        return t

    @_(r"\n+")  # noqa: F821
    def newline(self, t):
        self.lineno += t.value.count("\n")


class CellMethodsParser(Parser):
    tokens = CellMethodsLexer.tokens

    def __init__(self):
        self.groups = []

    @_("statements")  # noqa: F821
    def program(self, p):
        return self.groups

    @_("statement")  # noqa: F821
    def statements(self, p):
        return p.statement

    @_("statements statement")  # noqa: F821
    def statements(self, p):  # noqa: F811
        return p.statements

    @_("dimension action")  # noqa: F821
    def statement(self, p):
        current_group = [("DIMENSION", p.dimension), ("ACTION", p.action)]
        self.groups.append(current_group)
        return p

    @_("dimension action SCOPE")  # noqa: F821
    def statement(self, p):  # noqa: F811
        current_group = [
            ("DIMENSION", p.dimension),
            ("ACTION", p.action),
            ("SCOPE", p.SCOPE),
        ]
        self.groups.append(current_group)
        return p

    @_("dimension action constraint region")  # noqa: F821
    def statement(self, p):  # noqa: F811
        current_group = [
            ("DIMENSION", p.dimension),
            ("ACTION", p.action),
            ("CONSTRAINT", p.constraint),
            ("REGION", p.region),
        ]
        self.groups.append(current_group)
        return p

    @_("dimension action constraint region SCOPE")  # noqa: F821
    def statement(self, p):  # noqa: F811
        current_group = [
            ("DIMENSION", p.dimension),
            ("ACTION", p.action),
            ("CONSTRAINT", p.constraint),
            ("REGION", p.region),
            ("SCOPE", p.SCOPE),
        ]
        self.groups.append(current_group)
        return p

    @_("dimension action constraint SELECTION")  # noqa: F821
    def statement(self, p):  # noqa: F811
        current_group = [
            ("DIMENSION", p.dimension),
            ("ACTION", p.action),
            ("CONSTRAINT", p.constraint),
            ("SELECTION", p.SELECTION),
        ]
        self.groups.append(current_group)
        return p

    @_("dimensions ACTION")  # noqa: F821
    def statement(self, p):  # noqa: F811
        for dimension in p.dimensions:
            current_group = [("DIMENSION", dimension), ("ACTION", p.ACTION)]
            self.groups.append(current_group)
        return p

    @_("dimension")  # noqa: F821
    def dimensions(self, p):
        return [p.dimension]

    @_("dimensions dimension")  # noqa: F821
    def dimensions(self, p):  # noqa: F811
        return p.dimensions + [p.dimension]

    @_("DIMENSION")  # noqa: F821
    def dimension(self, p):
        return p.DIMENSION

    @_("ACTION")  # noqa: F821
    def action(self, p):
        return p.ACTION

    @_("CONSTRAINT")  # noqa: F821
    def constraint(self, p):
        return p.CONSTRAINT

    @_("REGION")  # noqa: F821
    def region(self, p):
        return p.REGION


class XArrayTranslator:
    """
    Represent parsed tree as human readable (pseudo code) xarray operations.
    Produces strings and not xarray objects.
    """

    def __init__(self, da_name="da"):
        self.da_name = da_name

    def translate_group(self, group):
        """Translate a single group of tokens into an xarray operation."""
        tokens_dict = dict(group)

        # Base operation
        operation = f"{self.da_name}"

        # Handle the main action
        if "ACTION" in tokens_dict:
            action = tokens_dict["ACTION"]
            dim = tokens_dict.get("DIMENSION")

            if "CONSTRAINT" in tokens_dict:
                constraint = tokens_dict["CONSTRAINT"]
                if constraint == "within":
                    # For 'within', we first group by the selection
                    selection = tokens_dict.get("SELECTION")
                    if selection:
                        operation = f"{operation}.groupby('{selection}').{action}()"
                elif constraint == "over":
                    # For 'over', we apply the operation over the selection
                    selection = tokens_dict.get("SELECTION")
                    if selection:
                        operation = f"{operation}.{action}(dim='{selection}')"
                elif constraint == "where":
                    # For 'where', we apply a mask before the operation
                    region = tokens_dict.get("REGION")
                    if region:
                        operation = (
                            f"{operation}.where(mask=='{region}').{action}(dim='{dim}')"
                        )
            else:
                # Simple dimension reduction
                operation = f"{operation}.{action}(dim='{dim}')"

            # Add any scope comments as a comment in the code
            if "SCOPE" in tokens_dict:
                operation = f"{operation}  # {tokens_dict['SCOPE']}"

        return operation

    def translate(self, groups):
        """Translate all groups into a sequence of xarray operations."""
        operations = []
        intermediate = self.da_name

        if len(groups) == 1:
            # For single operations, just return the operation directly
            return self.translate_group(groups[0])

        for i, group in enumerate(groups):
            if i > 0:
                # Use the result of the previous operation
                self.da_name = f"result_{i}"
                operations.append(f"{self.da_name} = {intermediate}")

            intermediate = self.translate_group(group)

            if i == len(groups) - 1:
                # Last operation should be assigned to final result
                operations.append(f"result = {intermediate}")

        return "\n".join(operations)


def parse_cell_methods(text):
    lexer = CellMethodsLexer()
    parser = CellMethodsParser()
    return parser.parse(lexer.tokenize(text))


def translate_to_xarray(text):
    """Convenience function to parse cell methods and translate to xarray operations."""
    translator = XArrayTranslator()

    parsed = parse_cell_methods(text)
    return translator.translate(parsed)


if __name__ == "__main__":
    text = "area: mean where sea depth: sum where sea (top 100m only) time: mean"
    result = parse_cell_methods(text)
    from pprint import pprint

    pprint(result)
    print(
        "\nXArray translation (pseduo code, human readable strings. not xarray object):"
    )
    print(translate_to_xarray(text))
