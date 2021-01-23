from udebs.interpret import *
from pytest import raises
import udebs


class TestInterpret:
    @staticmethod
    def setup():
        test = {
            "solitary": {
                "f": "solitary",
            },
            "testing": {
                "f": "TEST",
                "default": {"$3": 50},
                "args": ["-$1", "$1", "$2", "three"],
                "kwargs": {"none": "$3", "value": "empty", "test": 10},
            }
        }
        importModule(test, {'self': None})

    def test_setup(self):
        assert "solitary" in Variables.keywords()
        assert "testing" in Variables.keywords()
        assert "self" in Variables.env

    def test_list(self):
        assert interpret("one two three") == "('one','two','three')"
        assert interpret("1 2 three") == "(1,2,'three')"

    def test_Syntax_mismatched_brackets(self):
        with raises(UdebsSyntaxError):
            interpret("(one two (three)")

    def test_Syntax_unused_arguments(self):
        with raises(UdebsSyntaxError):
            interpret("one in two unused, unused2")

    def test_Syntax_empty_callstring(self):
        with raises(UdebsSyntaxError):
            interpret("() == one")

    def test_Syntax_extra_keywords(self):
        with raises(UdebsSyntaxError):
            interpret("max one in two")

    def test_solitary(self):
        assert interpret("one in (solitary)") == "standard.inside('one',solitary(),1)"

    def test_dot(self):
        assert interpret("one two one.two.three") == interpret("one two (one two three)")

    def test_prefix(self):
        assert interpret("one two -three") == "('one','two',operator.sub(0,'three'))"
        assert interpret("-one.two.three") == "(operator.sub(0,'one'),'two','three')"
        assert interpret("-(one two three)") == "operator.sub(0,('one','two','three'))"

    def test_call(self):
        assert interpret(
            "negative testing one two") == "TEST('negative','one','two','three',none=50,test=10,value='empty')"

    def test_global(self):
        assert interpret("one $target") == "('one',storage.__getitem__('target'))"

    def test_specials(self):
        assert interpret("self") == "(self)"
        assert interpret("true") == "(True)"
        assert interpret("'help'") == "('help')"

    def test_debug(self):
        interpret("(one) two three", debug=True)

    def test_Error_repr(self):
        one = UdebsSyntaxError("test")
        print(one)


class TestBase:
    def setup(self):
        path = os.path.dirname(__file__)
        self.env = udebs.battleStart(path + "/test.xml", log=True)

    def test_logicif(self):
        assert self.env.castSingle("if 1 0 2") == 0
        assert self.env.castSingle("if 0 0 2") == 2

    def test_logicor(self):
        assert self.env.castSingle("1 or 0") is True
        assert self.env.castSingle("0 or 0") is False
        assert self.env.castSingle("0 or `move1") is True

    def test_var(self):
        # not sure how to test if this actually worked
        assert self.env.castSingle("1 = test")
        assert self.env.castSingle("1 -> test")

    def test_inside(self):
        assert self.env.castSingle("1 in (1 0)") is True
        assert self.env.castSingle("1 in (1 0) 2") is False
        assert self.env.castSingle("1 in (2 0) 0") is True

        assert self.env.castSingle("a in alberta") is True

    def test_notin(self):
        assert self.env.castSingle("1 not-in (0 2)") is True

    def test_equal(self):
        assert self.env.castSingle("1 == 1 1 1 1") is True
        assert self.env.castSingle("1 == 1 2 1 1") is False

    def test_not_equal(self):
        assert self.env.castSingle("1 != 1 2 3 4") is False
        assert self.env.castSingle("1 != 2 3 4 5") is True
        assert self.env.castSingle("1 != 2") is True

    def test_relations(self):
        assert self.env.castSingle("1 > 0") is True
        assert self.env.castSingle("1 < 0") is False
        assert self.env.castSingle("1 <= 1") is True
        assert self.env.castSingle("0 >= 1") is False

    def test_math(self):
        assert self.env.castSingle("+ 1 2 3 4 5") == 15
        assert self.env.castSingle("* 1 2 3") == 6
        assert self.env.castSingle("5 % 10") == 5
        assert self.env.castSingle("10 / 5") == 2

    def test_bool(self):
        assert self.env.castSingle("!true") is False

    def test_element(self):
        assert self.env.castSingle("(1 2 3) elem 0") == 1

    def test_len(self):
        assert self.env.castSingle("length (0 0 0 1)") == 4
