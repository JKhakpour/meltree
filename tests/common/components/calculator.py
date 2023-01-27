from pathlib import Path


class Calculator(object):
    def __init__(self, meld_id=None, **kwargs):
        pass
        # super(Calculator, self).__init__(meld_id, **kwargs)

    expression = ""
    expression_shown = ""
    template_path = Path(__file__).name.replace(".py", ".html")
    ## only 64bit integer
    result = "0"
    last_btn = None
    opers = ("%", "÷", "+", "-", "^", "x")
    numerals = ["."] + [str(i) for i in range(10)]
    symbol_translation = {
        "x": "*",
        "÷": "/",
        "^": "**",
    }

    def btn_pressed(self, btn):
        # button presss actions. logic has flaws, but simple logic is good enough here
        if btn in ("c",):
            self.expression = ""
            # self.expression_shown = ""
            self.result = "0"
        elif btn in self.opers:
            if (btn, self.expression[-1]) == ("x", "x"):
                # change xx to ^
                self.expression = self.expression[:-1] + "^"
            else:
                self.expression += btn
        elif btn in self.numerals:
            if self.last_btn == "=":
                self.expression = btn
            else:
                self.expression += btn
        elif btn in ("<",):
            self.expression = self.expression[:-1]
        elif btn in ("=",):
            _expression = self.expression
            for m, r in self.symbol_translation.items():
                _expression = _expression.replace(m, r)
            try:
                self.result = str(round(eval(_expression), 5))
            except Exception as e:
                self.result = type(e).__name__
        self.last_btn = btn
