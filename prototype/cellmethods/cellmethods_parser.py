from sly import Lexer, Parser


class CellMethodsLexer(Lexer):
    # set of token names
    tokens = {
        DIMENSION,  # noqa: F821
        FUNCTION,  # noqa: F821
        CONSTRAINT,  # noqa: F821
        AREATYPE,  # noqa: F821
        SELECTION,  # noqa: F821
        COMMENT,  # noqa: F821
    }  # noqa: F821

    # string containing ignored characters between token
    ignore = " \t"

    # Regular expression rules for tokens
    # DIMENSION = r"area:|time:|grid_longitude:|longitude:|latitude:|depth:"
    DIMENSION = r"[a-zA-Z_]+:"
    FUNCTION = r"mean|minimum|maximum|sum|point"
    CONSTRAINT = r"within|over|where"
    AREATYPE = r"[a-zA-Z_]+"
    SELECTION = r"[a-zA-Z_]+"

    def DIMENSION(self, t):  # noqa: F811
        t.value = t.value[:-1]
        return t

    _areatypes = set(
        [
            "land",
            "shrubs",
            "pastures",
            "crops",
            "trees",
            "vegetation",
            "unfrozen_soil",
            "cloud",
            "natural_grasses",
            "floating_ice_shelf",
            "grounded_ice_sheet",
            "ice_free_sea",
            "ice_sheet",
            "sea",
            "sea_ice",
            "sea_ice_melt_pond",
            "sea_ice_ridges",
            "snow",
            "sector",
        ]
    )
    _selection = set(["hours", "days", "years", "months"])
    _selection.add("all_area_types")

    @_(r"[a-zA-Z_]+")  # noqa: F821
    def AREATYPE(self, t):  # noqa: F811
        if t.value in self._areatypes:
            return t
        if t.value in self._selection:
            t.type = "SELECTION"
            return t

    @_(r"\(.*?\)")  # noqa: F821
    def COMMENT(self, t):
        value = t.value[1:-1]
        t.value = (
            value.replace("comment:", "").replace("[", "").replace("]", "").strip()
        )
        return t

    @_(r"\n+")  # noqa: F821
    def newline(self, t):
        self.lineno += t.value.count("\n")


class CellMethodsParser(Parser):
    tokens = CellMethodsLexer.tokens
    debugfile = "parser.out"

    def __init__(self):
        self.tmp = []

    @_("statements")  # noqa: F821
    def program(self, p):
        return corrections(p.statements)
        # return p.statements

    @_("statement")  # noqa: F821
    def statements(self, p):
        return p.statement

    @_("statements statement")  # noqa: F821
    def statements(self, p):  # noqa: F811
        return p.statements + p.statement

    @_("dimension function")  # noqa: F821
    def statement(self, p):
        return [p.dimension + p.function]

    @_("dimension function comment")  # noqa: F821
    def statement(self, p):  # noqa: F811
        return [p.dimension + p.function + p.comment]

    @_("dimension function expr")  # noqa: F821
    def statement(self, p):  # noqa: F811
        return [p.dimension + p.function + p.expr]

    @_("dimension function exprs")  # noqa: F821
    def statement(self, p):  # noqa: F811
        return [p.dimension + p.function + p.exprs]

    @_("dimensions function")  # noqa: F821
    def statement(self, p):  # noqa: F811
        return [dim + p.function for dim in p.dimensions]

    @_("dimensions function comment")  # noqa: F821
    def statement(self, p):  # noqa: F811
        return [dim + p.function + p.comment for dim in p.dimensions]

    @_("dimensions function expr")  # noqa: F821
    def statement(self, p):  # noqa: F811
        return [dim + p.function + p.expr for dim in p.dimensions]

    @_("dimensions function exprs")  # noqa: F821
    def statement(self, p):  # noqa: F811
        return [dim + p.function + expr for dim in p.dimensions for expr in p.exprs]

    @_("constraint areatype comment")  # noqa: F821
    def expr(self, p):
        return p.constraint + p.areatype + p.comment

    @_("constraint selection comment")  # noqa: F821
    def expr(self, p):  # noqa: F811
        return p.constraint + p.selection + p.comment

    @_("constraint areatype")  # noqa: F821
    def expr(self, p):  # noqa: F811
        return p.constraint + p.areatype

    @_("constraint selection")  # noqa: F821
    def expr(self, p):  # noqa: F811
        return p.constraint + p.selection

    @_("expr expr")  # noqa: F821
    def exprs(self, p):
        return p.expr0 + p.expr1

    @_("exprs expr")  # noqa: F821
    def exprs(self, p):  # noqa: F811
        return p.exprs + p.expr

    @_("dimension dimension")  # noqa: F821
    def dimensions(self, p):
        return [p.dimension0, p.dimension1]

    @_("dimensions dimension")  # noqa: F821
    def dimensions(self, p):  # noqa: F811
        return p.dimensions + [p.dimension]

    @_("DIMENSION")  # noqa: F821
    def dimension(self, p):
        return [("DIMENSION", p.DIMENSION)]

    @_("FUNCTION")  # noqa: F821
    def function(self, p):
        return [("FUNCTION", p.FUNCTION)]

    @_("CONSTRAINT")  # noqa: F821
    def constraint(self, p):
        return [("CONSTRAINT", p.CONSTRAINT)]

    @_("AREATYPE")  # noqa: F821
    def areatype(self, p):
        return [("AREATYPE", p.AREATYPE)]

    @_("SELECTION")  # noqa: F821
    def selection(self, p):
        return [("SELECTION", p.SELECTION)]

    @_("COMMENT")  # noqa: F821
    def comment(self, p):
        return [("COMMENT", p.COMMENT)]


def corrections(groups):
    result = []
    for group in groups:
        grp = []
        tokens = iter(group)
        tok = next(tokens)
        tok_type, tok_value = tok
        grp.append(tok)
        if tok_type == "DIMENSION" and tok_value == "time":
            while True:
                try:
                    tok = next(tokens)
                except StopIteration:
                    break
                tok_type, tok_value = tok
                # for `time` dimension, only SELECTION type is allowed as constraint
                if tok_type == "AREATYPE":
                    grp.pop()
                else:
                    grp.append(tok)
        elif tok_type == "DIMENSION" and tok_value == "area":
            while True:
                try:
                    tok = next(tokens)
                except StopIteration:
                    break
                tok_type, tok_value = tok
                if tok_type == "SELECTION" and tok_value != "all_area_types":
                    grp.pop()
                else:
                    grp.append(tok)
        else:
            grp.extend(list(tokens))
        result.append(grp)
    return result


class XArrayTranslator:
    """
    Represent parsed tree as human readable (pseudo code) xarray operations.
    Produces strings and not xarray objects.
    """

    def __init__(self, da_name="da"):
        self.da_name = da_name

    def translate_group(self, group):
        """Translate a single group of tokens into an xarray operation."""
        tokens = iter(group)
        token_type, dim = next(tokens)
        assert token_type == "DIMENSION"
        token_type, function = next(tokens)
        assert token_type == "FUNCTION"
        texts = []
        try:
            token_type, tok_value = next(tokens)
        except StopIteration:
            return f"{self.da_name}.{function}(dim={dim})"
        else:
            if token_type == "COMMENT":
                if "mask=" in tok_value:
                    mask = tok_value.split("=")[1]
                    return f"{self.da_name}.where({mask}){function}(dim={dim}  # comment: {tok_value})"
                else:
                    return (
                        f"{self.da_name}.{function}(dim={dim})  # comment: {tok_value}"
                    )
            elif token_type == "CONSTRAINT":
                constraint = tok_value
                token_type, tok_value = next(tokens)
                text = f"{self.da_name}.{function}(dim={dim}).{constraint}({tok_value})"
                texts.append(text)
                if constraint == "over":
                    token_type, tok_value = next(tokens)
                    text = f"{self.da_name}.{function}(dim={dim}).{constraint}({tok_value})"
                    texts.append(text)
            while True:
                try:
                    token_type, tok_value = next(tokens)
                except StopIteration:
                    break
                if token_type == "COMMENT":
                    text = f"  # comment: {tok_value}"
                    texts.append(text)
                elif token_type == "CONSTRAINT":
                    constraint = tok_value
                    token_type, tok_value = next(tokens)
                    text = f".{constraint}({tok_value})"
                    texts.append(text)
        text = "".join(texts)
        return text

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


lexer = CellMethodsLexer()
parser = CellMethodsParser()


def parse_cell_methods(text):
    tokens = lexer.tokenize(text)
    group = parser.parse(tokens)
    return group


def translate_to_xarray(text):
    """Convenience function to parse cell methods and translate to xarray operations."""
    translator = XArrayTranslator()

    parsed = parse_cell_methods(text)
    return translator.translate(parsed)
