from udebs.interpret import *
from nose.tools import *

class TestInterpret():
    def setUp(self):
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
        assert "solitary" in variables.keywords()
        assert "testing" in variables.keywords()
        assert "self" in variables.env

    def test_list(self):
        assert interpret("one two three") == "('one','two','three')"
        assert interpret("1 2 three") == "(1,2,'three')"

    @raises(UdebsSyntaxError)
    def test_Syntax(self):
        interpret("(one two (three)")

    @raises(UdebsSyntaxError)
    def test_Syntax2(Self):
        interpret("this is a test(some more stuff)")

    @raises(UdebsSyntaxError)
    def test_Syntax3(Self):
        interpret("one in two unused")

    @raises(UdebsSyntaxError)
    def test_Syntax4(self):
        interpret("max one in two")

    def test_solitary(self):
        assert interpret("one in (solitary)") == "standard.inside('one',solitary())"

    def test_redundant(self):
        assert interpret("one two three") == interpret("(one two three)") == interpret("((one two three))")

    def test_dot(self):
        assert interpret("one two one.two.three") == interpret("one two (one two three)")

    def test_prefix(self):
        assert interpret("one two -three") == "('one','two',standard.minus(0,'three'))"
        assert interpret("-one.two.three") == "(standard.minus(0,'one'),'two','three')"
        assert interpret("-(one two three)") == "standard.minus(0,('one','two','three'))"

    def test_call(self):
        assert interpret("negative testing one two") == "TEST('negative','one','two','three',none=50,test=10,value='empty')"

    def test_global(self):
        assert interpret("one $target") == "('one',standard.getvar(storage,'target'))"
