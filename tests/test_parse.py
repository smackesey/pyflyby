# pyflyby/test_parse.py

# License for THIS FILE ONLY: CC0 Public Domain Dedication
# http://creativecommons.org/publicdomain/zero/1.0/

from __future__ import absolute_import, division, with_statement

import pytest
from   textwrap                 import dedent

from   pyflyby._file            import FilePos, FileText, Filename
from   pyflyby._flags           import CompilerFlags
from   pyflyby._parse           import PythonBlock, PythonStatement


def test_PythonBlock_FileText_1():
    text = FileText(dedent('''
        foo()
        bar()
    ''').lstrip(), filename="/foo/test_PythonBlock_1.py", startpos=(101,55))
    block = PythonBlock(text)
    assert text is block.text
    assert text is FileText(block)
    assert block.filename == Filename("/foo/test_PythonBlock_1.py")
    assert block.startpos == FilePos(101, 55)


def test_PythonBlock_attrs_1():
    block = PythonBlock(dedent('''
        foo()
        bar()
    ''').lstrip(), filename="/foo/test_PythonBlock_1.py", startpos=(101,99))
    assert block.text.lines == ("foo()", "bar()", "")
    assert block.filename   == Filename("/foo/test_PythonBlock_1.py")
    assert block.startpos   == FilePos(101, 99)


def test_PythonBlock_idempotent_1():
    block = PythonBlock("foo()\n")
    assert PythonBlock(block) is block


def test_PythonBlock_from_statement_1():
    stmt = PythonStatement("foo()\n", startpos=(101,202))
    block = PythonBlock(stmt)
    assert stmt.block is block
    assert block.statements == (stmt,)


def test_PythonBlock_statements_1():
    block = PythonBlock(dedent('''
        1
        [ 2,
          3,
        ]
        5
    ''').lstrip())
    expected = (
        PythonStatement("1\n"                            ),
        PythonStatement("[ 2,\n  3,\n]\n", startpos=(2,1)),
        PythonStatement("5\n"            , startpos=(5,1)),
    )
    assert block.statements == expected


def test_PythonBlock_lineno_1():
    block = PythonBlock(dedent('''
        1
        [ 2,
          3,
        ]
        5
    ''').lstrip(), startpos=(101,1))
    expected = (
        PythonStatement("1\n"            , startpos=(101,1)),
        PythonStatement("[ 2,\n  3,\n]\n", startpos=(102,1)),
        PythonStatement("5\n"            , startpos=(105,1)),
    )
    assert block.statements == expected


def test_PythonBlock_statements_comments_1():
    block = PythonBlock(dedent('''
        # 1
        print 2
        # 3
        # 4
        print 5
        x=[6,
         7]
        # 8
    ''').lstrip())
    expected = (
        PythonStatement('# 1\n'                 ),
        PythonStatement('print 2\n',    startpos=(2,1)),
        PythonStatement('# 3\n# 4\n',   startpos=(3,1)),
        PythonStatement('print 5\n',    startpos=(5,1)),
        PythonStatement('x=[6,\n 7]\n', startpos=(6,1)),
        PythonStatement('# 8\n',        startpos=(8,1)),
    )
    assert block.statements == expected


def test_PythonBlock_statements_continuation_1():
    block = PythonBlock(dedent(r'''
        a
        b,\
        c
        d
    ''').lstrip(), startpos=(101,1))
    expected = (
        PythonStatement('a\n' , startpos=(101,1)),
        PythonStatement('b,\\\nc\n', startpos=(102,1)),
        PythonStatement('d\n' , startpos=(104,1)),
    )
    assert block.statements == expected


def test_PythonBlock_statements_last_line_comment_continuation_1():
    block = PythonBlock(dedent(r'''
        a
        b\
        # c
    ''').lstrip(), startpos=(101,1))
    expected = (
        PythonStatement('a\n'       , startpos=(101,1)),
        PythonStatement('b\\\n# c\n', startpos=(102,1)),
    )
    assert block.statements == expected


def test_PythonBlock_statements_comment_no_continuation_1():
    block = PythonBlock(dedent('''
        x
        # y
        # z
    ''').lstrip())
    expected = (
        PythonStatement("x\n"                       ),
        PythonStatement("# y\n# z\n", startpos=(2,1)),
    )
    assert block.statements == expected


def test_PythonBlock_statements_comment_continuation_to_comment_1():
    block = PythonBlock(dedent('''
        x
        # y \\
        # z
    ''').lstrip())
    expected = (
        PythonStatement("x\n"                          ),
        PythonStatement("# y \\\n# z\n", startpos=(2,1)),
    )
    assert block.statements == expected


def test_PythonBlock_statements_last_line_no_newline_1():
    block = PythonBlock(dedent('''
        a
        b''').lstrip(), startpos=(101,1))
    expected = (
        PythonStatement('a\n', startpos=(101,1)),
        PythonStatement('b'  , startpos=(102,1)),
    )
    assert block.statements == expected


def test_PythonBlock_statements_last_line_comment_no_newline_1():
    block = PythonBlock(dedent('''
        a
        #b''').lstrip(), startpos=(101,1))
    expected = (
        PythonStatement('a\n', startpos=(101,1)),
        PythonStatement('#b'  , startpos=(102,1)),
    )
    assert block.statements == expected


def test_PythonBlock_statements_last_line_comment_continuation_no_newline_1():
    block = PythonBlock(dedent(r'''
        a
        b\
        # c''').lstrip(), startpos=(101,1))
    expected = (
        PythonStatement('a\n' , startpos=(101,1)),
        PythonStatement('b\\\n# c', startpos=(102,1)),
    )
    assert block.statements == expected


def test_PythonBlock_statements_last_line_nested_continuation_1():
    block = PythonBlock(dedent(r'''
        a
        if b:
            "c\
        # d"''').lstrip(), startpos=(101,1))
    expected = (
        PythonStatement('a\n' , startpos=(101,1)),
        PythonStatement('if b:\n    "c\\\n# d"', startpos=(102,1)),
    )
    assert block.statements == expected


def test_PythonBlock_statements_comment_backslash_1():
    block = PythonBlock(dedent(r'''
        #a\
        b''').lstrip(), startpos=(101,1))
    expected = (
        PythonStatement('#a\\\n', startpos=(101,1)),
        PythonStatement('b'     , startpos=(102,1)),
    )
    assert block.statements == expected


def test_PythonBlock_statements_single_1():
    block = PythonBlock("foo(1,2)")
    assert len(block.statements) == 1
    assert block.statements[0].block is block


def test_PythonBlock_statements_empty_1():
    block = PythonBlock("")
    assert len(block.statements) == 1
    assert block.statements[0].block is block


def test_PythonBlock_statements_lone_comment_no_newline_1():
    block = PythonBlock('#a a')
    assert len(block.statements) == 1
    assert block.statements[0].block is block


def test_PythonBlock_statements_lone_comment_no_newline_with_offset_1():
    block = PythonBlock('#a a', startpos=(101,55))
    assert len(block.statements) == 1
    assert block.statements[0].block is block


def test_PythonBlock_statements_single_trailing_comment_1():
    block = PythonBlock(dedent('''
        foo(1,2)
        # last
    ''').lstrip())
    expected = (
        PythonStatement("foo(1,2)\n", startpos=(1,1)),
        PythonStatement("# last\n"  , startpos=(2,1)),
    )
    assert block.statements == expected


def test_PythonBlock_statements_single_preceding_comment_1():
    block = PythonBlock(dedent('''
        # first
        foo(1,2)
    ''').lstrip())
    expected = (
        PythonStatement("# first\n" , startpos=(1,1)),
        PythonStatement("foo(1,2)\n", startpos=(2,1)),
    )
    assert block.statements == expected


def test_PythonBlock_statements_all_comments_1():
    block = PythonBlock("#a\n#b")
    assert len(block.statements) == 1
    assert block.statements[0].block is block


def test_PythonBlock_statements_all_comments_2():
    block = PythonBlock("#a\n#b\n")
    assert len(block.statements) == 1
    assert block.statements[0].block is block


def test_PythonBlock_doctest_1():
    block = PythonBlock(dedent("""
        # x
        '''
          >>> foo(bar
          ...     + baz)
        '''
    """).lstrip())
    expected = [PythonBlock('foo(bar\n    + baz)\n', startpos=(3,3))]
    assert block.get_doctests() == expected


def test_PythonBlock_doctest_nested_1():
    # Verify that we only include doctests from nested functions.
    block = PythonBlock(dedent("""
        def f():
            '>>> f(18739149)'
            def g():
                '>>> g(29355493)'
    """).lstrip())
    expected = [PythonBlock('f(18739149)\n', startpos=(2,5)),
                PythonBlock('g(29355493)\n', startpos=(4,9))]
    assert block.get_doctests() == expected


def test_PythonBlock_doctest_nested_cond_1():
    block = PythonBlock(dedent("""
        def f():
            '>>> f(17556901)'
            if True:
                def g():
                    '>>> g(21607865)'
    """).lstrip())
    expected = [PythonBlock('f(17556901)\n', startpos=(2,5)),
                PythonBlock('g(21607865)\n', startpos=(5,13))]
    assert block.get_doctests() == expected


def test_PythonBlock_doctest_nested_class_1():
    block = PythonBlock(dedent("""
        def f():
            '>>> f(11462083)'
            class C:
                '>>> C(21800340)'
                @classmethod
                def g(cls):
                    '>>> g(35606252)'
    """).lstrip())
    expected = [PythonBlock('f(11462083)\n', startpos=(2,5)),
                PythonBlock('C(21800340)\n', startpos=(4,9)),
                PythonBlock('g(35606252)\n', startpos=(7,13))]
    assert block.get_doctests() == expected


def test_PythonBlock_doctest_only_first_in_function_1():
    # Verify that we only include doctests from the first string in a
    # function.
    block = PythonBlock(dedent("""
        def f():
            '>>> a'
            3
            '>>> b'
    """).lstrip())
    expected = [PythonBlock('a\n', startpos=(2,5))]
    assert block.get_doctests() == expected


def test_PythonBlock_doctest_only_first_in_function_2():
    block = PythonBlock(dedent("""
        def f():
            if True:
                '>>> x'
    """).lstrip())
    expected = []
    assert block.get_doctests() == expected


def test_PythonBlock_doctest_only_first_in_function_3():
    block = PythonBlock(dedent("""
        def f():
            return '>>> x'
    """).lstrip())
    expected = []
    assert block.get_doctests() == expected


def test_PythonBlock_doctest_only_first_in_function_4():
    block = PythonBlock(dedent("""
        def f():
            ('>>> a' + '')
            3
    """).lstrip())
    expected = []
    assert block.get_doctests() == expected


def test_PythonBlock_doctest_only_first_in_function_not_try_1():
    block = PythonBlock(dedent("""
        def f():
            '>>> a'
            try:
                '>>> b'
            except:
                pass
    """).lstrip())
    expected = [PythonBlock('a\n', startpos=(2,5))]
    assert block.get_doctests() == expected


def test_PythonBlock_doctest_only_first_in_class_1():
    block = PythonBlock(dedent("""
        class C:
            '>>> C(11475111)'
            def f(self): pass
            '>>> x'

    """).lstrip())
    expected = [PythonBlock('C(11475111)\n', startpos=(2,5))]
    assert block.get_doctests() == expected


def test_PythonBlock_doctest_assignments_at_global_scope_1():
    # Verify that we only include doctests from (Epydoc) "variable docstrings"
    # at global scope.
    block = PythonBlock(dedent("""
        '>>> x'
        def f(): pass

        a = 4
        '>>> a'

        def g(): pass

        b = 5
        '>>> b'
    """).lstrip())
    expected = [PythonBlock('x\n'),
                PythonBlock('a\n', startpos=(5,1)),
                PythonBlock('b\n', startpos=(10,1))]
    assert block.get_doctests() == expected


def test_PythonBlock_doctest_assignments_ClassDef_1():
    block = PythonBlock(dedent("""
        class C:
            ">>> C(17621216)"
            x = 5
            ">>> C(28208124)"
            def f(self): pass
            ">>> x"
    """).lstrip())
    expected = [PythonBlock('C(17621216)\n', startpos=(2,5)),
                PythonBlock('C(28208124)\n', startpos=(4,5))]
    assert block.get_doctests() == expected


def test_PythonBlock_doctest_assignments_method_1():
    block = PythonBlock(dedent("""
        class C:
            ">>> C(13798505)"
            def __init__(self):
                ">>> C(25709748)"
                self.x = 0
                ">>> C(32231717)"
                f()
                ">>> x"
    """).lstrip())
    expected = [PythonBlock('C(13798505)\n', startpos=(2,5)),
                PythonBlock('C(25709748)\n', startpos=(4,9)),
                PythonBlock('C(32231717)\n', startpos=(6,9))]
    assert block.get_doctests() == expected


def test_PythonBlock_flags_bad_1():
    # In Python2.x, this should cause a syntax error, since we didn't do
    # flags='print_function':
    with pytest.raises(SyntaxError):
        PythonBlock('print("x",\n file=None)\n').statements


def test_PythonBlock_flags_good_1():
    PythonBlock('print("x",\n file=None)\n', flags="print_function").statements


def test_PythonBlock_flags_1():
    block = PythonBlock('print("x",\n file=None)\n', flags="print_function")
    assert block.flags == CompilerFlags(0x10000)


def test_PythonBlock_flags_deduce_1():
    block = PythonBlock(dedent('''
        from __future__ import print_function
        print("x",
              file=None)
    ''').lstrip())
    assert block.flags == CompilerFlags(0x10000)


def test_PythonBlock_flags_deduce_eq_1():
    block1 = PythonBlock(dedent('''
        from __future__ import print_function
        print("x",
              file=None)
    ''').lstrip())
    block2 = PythonBlock(dedent('''
        from __future__ import print_function
        print("x",
              file=None)
    ''').lstrip(), flags=0x10000)
    assert block1 == block2


def test_PythonBlock_eqne_1():
    b1a = PythonBlock("foo()\nbar()\n")
    b1b = PythonBlock("foo()\nbar()\n")
    b2  = PythonBlock("foo()\nBAR()\n")
    assert     (b1a == b1b)
    assert not (b1a != b1b)
    assert     (b1a != b2 )
    assert not (b1a == b2 )


def test_PythonBlock_eqne_startpos_1():
    b1a = PythonBlock("foo()\nbar()\n")
    b1b = PythonBlock("foo()\nbar()\n", startpos=(1,1))
    b2  = PythonBlock("foo()\nbar()\n", startpos=(1,2))
    assert     (b1a == b1b)
    assert not (b1a != b1b)
    assert     (b1a != b2 )
    assert not (b1a == b2 )


def test_PythonBlock_eqne_flags_1():
    b1a = PythonBlock("foo", flags="print_function")
    b1b = PythonBlock("foo", flags=0x10000)
    b2  = PythonBlock("foo")
    assert     (b1a == b1b)
    assert not (b1a != b1b)
    assert     (b1a != b2 )
    assert not (b1a == b2 )


def test_PythonStatement_from_source_1():
    stmt = PythonStatement('print("x",\n file=None)\n', flags=0x10000)
    assert stmt.block == PythonBlock('print("x",\n file=None)\n', flags=0x10000)


def test_PythonStatement_startpos_1():
    stmt = PythonStatement('foo()', startpos=(20,30))
    assert stmt.startpos            == FilePos(20,30)
    assert stmt.block.startpos      == FilePos(20,30)
    assert stmt.block.text.startpos == FilePos(20,30)


def test_PythonStatement_from_block_1():
    block = PythonBlock('print("x",\n file=None)\n', flags=0x10000)
    stmt = PythonStatement(block)
    assert stmt.block is block


def test_PythonStatement_bad_from_multi_statements_1():
    with pytest.raises(ValueError):
        PythonStatement("a\nb\n")


def test_PythonStatement_flags_bad_1():
    # In Python2.x, this should cause a syntax error, since we didn't do
    # flags='print_function':
    with pytest.raises(SyntaxError):
        PythonStatement('print("x",\n file=None)\n')


def test_PythonStatement_flags_good_1():
    PythonStatement('print("x",\n file=None)\n', flags="print_function")


def test_str_lineno_simple_1():
    block = PythonBlock(dedent(r'''
        a = [
          2,
          3,
        ]
        b = 'five-a' + 'five-b'
        """
        seven
        eight
        """
        d = 'ten\n'
    ''').lstrip(), startpos=(101,1))
    expected_statements = (
        PythonStatement("a = [\n  2,\n  3,\n]\n"   , startpos=(101,1)),
        PythonStatement("b = 'five-a' + 'five-b'\n", startpos=(105,1)),
        PythonStatement('"""\nseven\neight\n"""\n' , startpos=(106,1)),
        PythonStatement("d = 'ten\\n'\n"           , startpos=(110,1))
    )
    assert block.statements == expected_statements
    literals = [(f.s, f.startpos) for f in block.string_literals()]
    expected = [
        ("five-a"          , FilePos(105,5)),
        ("five-b"          , FilePos(105,16)),
        ("\nseven\neight\n", FilePos(106,1)),
        ("ten\n"           , FilePos(110,5)),
    ]
    assert literals == expected


def test_str_lineno_trailing_1():
    block = PythonBlock(dedent(r'''
        one
        """
        three
        four
        """.split()
        six
    ''').lstrip(), startpos=(101,1))
    expected_statements = (
        PythonStatement('one\n'                          , startpos=(101,1)),
        PythonStatement('"""\nthree\nfour\n""".split()\n', startpos=(102,1)),
        PythonStatement('six\n'                          , startpos=(106,1)),
    )
    assert block.statements == expected_statements
    literals = [(f.s, f.startpos) for f in block.string_literals()]
    expected_literals = [("\nthree\nfour\n", FilePos(102,1))]
    assert literals == expected_literals


def test_str_lineno_multichars_1():
    block = PythonBlock(dedent('''
        [
          2,
          3,
        ]
        """ 5 "" " ""
        6 "" "
        7 "" """, """b "" "
        8 " "" """
        9
    ''').lstrip(), startpos=(101,1))
    expected_statements = (
        PythonStatement("[\n  2,\n  3,\n]\n", startpos=(101,1)),
        PythonStatement('""" 5 "" " ""\n6 "" "\n'
                        '7 "" """, """b "" "\n8 " "" """\n', startpos=(105,1)),
        PythonStatement("9\n", startpos=(109,1)),
        )
    assert block.statements == expected_statements
    literals = [(f.s, f.startpos) for f in block.string_literals()]
    expected_literals = [(' 5 "" " ""\n6 "" "\n7 "" ', FilePos(105,1 )),
                         ('b "" "\n8 " "" '          , FilePos(107,11))]
    assert literals == expected_literals


def test_str_lineno_in_dict_1():
    block = PythonBlock(dedent('''
        {
            1:
                """
                foo4
                bar5
                """,
            2:  \'\'\'
                foo8
                bar9
                \'\'\'}
    ''').lstrip(), startpos=(101,1))
    literals = [(f.s, f.startpos) for f in block.string_literals()]
    expected_literals = [('\n        foo4\n        bar5\n        ', FilePos(103,9)),
                         ('\n        foo8\n        bar9\n        ', FilePos(107,9))]
    assert literals == expected_literals


def test_str_lineno_strprefix_1():
    block = PythonBlock(dedent(r'''
        r"aa\nbb"
        0
        Ur"""cc\n
        dd"""
        r"x"
    ''').lstrip(), startpos=(101,1))
    expected_statements = (
        PythonStatement('r"aa\\nbb"\n'       , startpos=(101,1)),
        PythonStatement('0\n'                , startpos=(102,1)),
        PythonStatement('Ur"""cc\\n\ndd"""\n', startpos=(103,1)),
        PythonStatement('r"x"\n'             , startpos=(105,1)),
    )
    assert block.statements == expected_statements
    literals = [(f.s, f.startpos) for f in block.string_literals()]
    expected_literals = [('aa\\nbb'  , FilePos(101,1)),
                         ('cc\\n\ndd', FilePos(103,1)),
                         ('x'        , FilePos(105,1))]
    assert literals == expected_literals


def test_str_lineno_escaped_single_1():
    block = PythonBlock(dedent(r'''
        x = "a\
        #b" 'c\
        #d' \
        'e'
        'f' \
        #'g'
    ''').lstrip(), startpos=(101,1))
    expected_statements = (
        PythonStatement("""x = "a\\\n#b" 'c\\\n#d' \\\n'e'\n""", startpos=(101,1)),
        PythonStatement("""'f' \\\n#'g'\n""", startpos=(105,1)),
    )
    assert block.statements == expected_statements
    literals = [(f.s, f.startpos) for f in block.string_literals()]
    expected_literals = [('a#bc#de', FilePos(101,5)),
                         ('f'      , FilePos(105,1))]
    assert literals == expected_literals


def test_str_lineno_concatenated_1():
    block = PythonBlock(dedent('''
        "A" "a"
        "B" 'b'
        'C' 'c'
        'D' "d"
        """E
        e""" 'E'
        x = """F"""  'f'
        \'G\'\'\'\'g

        \'\'\' "G"
        x = """H
        h
        H""" 'h' \'\'\'H


        h\'\'\'
        "I" 'i'.split()
        "J" """j
        J"""    'j'.split()
        'K'
        'L'
        r"M" u'm' b"""M""" Ur\'\'\'
        m\'\'\'
        "N" ''"" "n" """"""\'\'\'\'\'\'\'N\'\'\'
        """
        O
        """
        """
        P
        """
        "Q" "q"""
        "R" "r""" + "S""""s""S""""s""""
        S"""
    ''').lstrip(), startpos=(101,1))
    expected_statements = (
        PythonStatement('''"A" "a"\n'''            , startpos=(101,1)),
        PythonStatement('''"B" 'b'\n'''            , startpos=(102,1)),
        PythonStatement(''''C' 'c'\n'''            , startpos=(103,1)),
        PythonStatement(''''D' "d"\n'''            , startpos=(104,1)),
        PythonStatement('''"""E\ne""" 'E'\n'''     , startpos=(105,1)),
        PythonStatement('''x = """F"""  'f'\n'''   , startpos=(107,1)),
        PythonStatement("""'G''''g\n\n''' "G"\n""" , startpos=(108,1)),
        PythonStatement('''x = """H\nh\nH""" 'h' \'\'\'H\n\n\nh\'\'\'\n''', startpos=(111,1)),
        PythonStatement('''"I" 'i'.split()\n'''    , startpos=(117,1)),
        PythonStatement('''"J" """j\nJ"""    'j'.split()\n'''             , startpos=(118,1)),
        PythonStatement("""'K'\n"""                , startpos=(120,1)),
        PythonStatement("""'L'\n"""                , startpos=(121,1)),
        PythonStatement('''r"M" u'm' b"""M""" Ur\'\'\'\nm\'\'\'\n'''      , startpos=(122,1)),
        PythonStatement('''"N" ''"" "n" """"""\'\'\'\'\'\'\'N\'\'\'\n'''  , startpos=(124,1)),
        PythonStatement('''"""\nO\n"""\n'''        , startpos=(125,1)),
        PythonStatement('''"""\nP\n"""\n'''        , startpos=(128,1)),
        PythonStatement('''"Q" "q"""\n'''          , startpos=(131,1)),
        PythonStatement('''"R" "r""" + "S""""s""S""""s""""\nS"""\n'''     , startpos=(132,1)),
    )
    assert block.statements == expected_statements
    literals = [(f.s, f.startpos) for f in block.string_literals()]
    expected_literals = [
        ("Aa", FilePos(101,1)),
        ("Bb", FilePos(102,1)),
        ("Cc", FilePos(103,1)),
        ("Dd", FilePos(104,1)),
        ("E\neE", FilePos(105,1)),
        ("Ff", FilePos(107,5)),
        ("Gg\n\nG", FilePos(108,1)),
        ("H\nh\nHhH\n\n\nh", FilePos(111,5)),
        ("Ii", FilePos(117,1)),
        ("Jj\nJj", FilePos(118,1)),
        ("K", FilePos(120,1)),
        ("L", FilePos(121,1)),
        ("MmM\nm", FilePos(122,1)),
        ("NnN", FilePos(124,1)),
        ("\nO\n", FilePos(125,1)),
        ("\nP\n", FilePos(128,1)),
        ("Qq", FilePos(131,1)),
        ("Rr", FilePos(132,1)),
        ('Ss""Ss\nS', FilePos(132,13)),
    ]
    assert literals == expected_literals


def test_PythonBlock_compound_statements_1():
    block = PythonBlock(dedent('''
        foo(); bar()
        if condition:
            a; b
        {1:100,
         2:200};{3:300,
         4:400}; """
        foo
        bar
        """; """x
        y"""
    ''').lstrip(), startpos=(101,1))
    expected = (
        PythonStatement("foo(); "                  , startpos=(101,1)),
        PythonStatement("bar()\n"                  , startpos=(101,8)),
        PythonStatement("if condition:\n    a; b\n", startpos=(102,1)),
        PythonStatement("{1:100,\n 2:200};"        , startpos=(104,1)),
        PythonStatement("{3:300,\n 4:400}; "       , startpos=(105,9)),
        PythonStatement('"""\nfoo\nbar\n"""; '     , startpos=(106,10)),
        PythonStatement('"""x\ny"""\n'             , startpos=(109,6)),
    )
    assert block.statements == expected


def test_PythonBlock_decorator_1():
    block = PythonBlock(dedent('''
        @foo1
        def bar1(): pass
        @foo2
        def bar2(): pass
    ''').lstrip(), startpos=(101,1))
    expected = (
        PythonStatement("@foo1\ndef bar1(): pass\n", startpos=(101,1)),
        PythonStatement("@foo2\ndef bar2(): pass\n", startpos=(103,1)),
    )
    assert block.statements == expected


# auto_flags tests.
# Key for test names:
#   ps = code contains print statement
#   pf = code contains print function
#   pn = code does not contain print statement or function
#   px = code contains ambiguous print statement/function
#   flagps = flags does not contain CompilerFlags("print_function")
#   flagpf = flags contains CompilerFlags("print_function")
#   futpf = code contains 'from __future__ import print_function'

def test_PythonBlock_no_auto_flags_ps_flagps_1():
    block = PythonBlock(dedent('''
        print 42
    ''').lstrip())
    assert not (block.flags                & "print_function")
    assert not (block.ast_node.input_flags & "print_function")
    assert not (block.source_flags         & "print_function")


def test_PythonBlock_no_auto_flags_ps_flagpf_1():
    block = PythonBlock(dedent('''
        print 42
    ''').lstrip(), flags="print_function")
    with pytest.raises(SyntaxError):
        block.ast_node


def test_PythonBlock_no_auto_flags_pf_flagps_1():
    block = PythonBlock(dedent('''
        print(42, out=x)
    ''').lstrip())
    with pytest.raises(SyntaxError):
        block.ast_node


def test_PythonBlock_no_auto_flags_pf_flagpf_1():
    block = PythonBlock(dedent('''
        print(42, out=x)
    ''').lstrip(), flags="print_function")
    assert     (block.flags                & "print_function")
    assert     (block.ast_node.input_flags & "print_function")
    assert not (block.source_flags         & "print_function")


def test_PythonBlock_no_auto_flags_pf_flagps_futpf_1():
    block = PythonBlock(dedent('''
        from __future__ import print_function
        print(42)
    ''').lstrip())
    assert     (block.flags                & "print_function")
    assert not (block.ast_node.input_flags & "print_function")
    assert     (block.source_flags         & "print_function")


def test_PythonBlock_no_auto_flags_pf_flagpf_futpf_1():
    block = PythonBlock(dedent('''
        from __future__ import print_function
        print(42)
    ''').lstrip(), flags="print_function")
    assert     (block.flags                & "print_function")
    assert     (block.ast_node.input_flags & "print_function")
    assert     (block.source_flags         & "print_function")


def test_PythonBlock_no_auto_flags_px_flagps_1():
    block = PythonBlock(dedent('''
        print(42)
    ''').lstrip())
    assert not (block.flags                & "print_function")
    assert not (block.ast_node.input_flags & "print_function")
    assert not (block.source_flags         & "print_function")


def test_PythonBlock_no_auto_flags_px_flagpf_1():
    block = PythonBlock(dedent('''
        print(42)
    ''').lstrip(), flags="print_function")
    assert     (block.flags                & "print_function")
    assert     (block.ast_node.input_flags & "print_function")
    assert not (block.source_flags         & "print_function")


def test_PythonBlock_no_auto_flags_pn_flagps_1():
    block = PythonBlock(dedent('''
        42
    ''').lstrip())
    assert not (block.flags                & "print_function")
    assert not (block.ast_node.input_flags & "print_function")
    assert not (block.source_flags         & "print_function")


def test_PythonBlock_no_auto_flags_pn_flagpf_1():
    block = PythonBlock(dedent('''
        42
    ''').lstrip(), flags="print_function")
    assert     (block.flags                & "print_function")
    assert     (block.ast_node.input_flags & "print_function")
    assert not (block.source_flags         & "print_function")


def test_PythonBlock_no_auto_flags_pn_futpf_1():
    block = PythonBlock(dedent('''
        from __future__ import print_function
        42
    ''').lstrip())
    assert     (block.flags                & "print_function")
    assert not (block.ast_node.input_flags & "print_function")
    assert     (block.source_flags         & "print_function")


def test_PythonBlock_auto_flags_ps_flagps_1():
    block = PythonBlock(dedent('''
        print 42
    ''').lstrip(), auto_flags=True)
    assert not (block.flags                & "print_function")
    assert not (block.ast_node.input_flags & "print_function")
    assert not (block.source_flags         & "print_function")


def test_PythonBlock_auto_flags_ps_flagpf_1():
    block = PythonBlock(dedent('''
        print 42
    ''').lstrip(), flags="print_function", auto_flags=True)
    assert not (block.flags                & "print_function")
    assert not (block.ast_node.input_flags & "print_function")
    assert not (block.source_flags         & "print_function")


def test_PythonBlock_auto_flags_ps_flagpf_futpf_1():
    block = PythonBlock(dedent('''
        from __future__ import print_function
        print 42
    ''').lstrip(), flags="print_function", auto_flags=True)
    with pytest.raises(SyntaxError):
        block.ast_node


def test_PythonBlock_auto_flags_ps_flagps_futpf_1():
    block = PythonBlock(dedent('''
        from __future__ import print_function
        print 42
    ''').lstrip(), auto_flags=True)
    with pytest.raises(SyntaxError):
        block.ast_node


def test_PythonBlock_auto_flags_pf_flagps_1():
    block = PythonBlock(dedent('''
        print(42, out=x)
    ''').lstrip(), auto_flags=True)
    assert     (block.flags                & "print_function")
    assert     (block.ast_node.input_flags & "print_function")
    assert not (block.source_flags         & "print_function")


def test_PythonBlock_auto_flags_pf_flagpf_1():
    block = PythonBlock(dedent('''
        print(42, out=x)
    ''').lstrip(), flags="print_function", auto_flags=True)
    assert     (block.flags                & "print_function")
    assert     (block.ast_node.input_flags & "print_function")
    assert not (block.source_flags         & "print_function")


def test_PythonBlock_auto_flags_pf_flagps_futpf_1():
    block = PythonBlock(dedent('''
        from __future__ import print_function
        print(42, out=x)
    ''').lstrip(), auto_flags=True)
    assert     (block.flags                & "print_function")
    assert not (block.ast_node.input_flags & "print_function")
    assert     (block.source_flags         & "print_function")


def test_PythonBlock_auto_flags_pf_flagpf_futpf_1():
    block = PythonBlock(dedent('''
        from __future__ import print_function
        print(42, out=x)
    ''').lstrip(), flags="print_function", auto_flags=True)
    assert     (block.flags                & "print_function")
    assert     (block.ast_node.input_flags & "print_function")
    assert     (block.source_flags         & "print_function")


def test_PythonBlock_auto_flags_px_flagps_1():
    block = PythonBlock(dedent('''
        print(42)
    ''').lstrip(), auto_flags=True)
    assert not (block.flags                & "print_function")
    assert not (block.ast_node.input_flags & "print_function")
    assert not (block.source_flags         & "print_function")


def test_PythonBlock_auto_flags_px_flagpf_1():
    block = PythonBlock(dedent('''
        print(42)
    ''').lstrip(), flags="print_function", auto_flags=True)
    assert     (block.flags                & "print_function")
    assert     (block.ast_node.input_flags & "print_function")
    assert not (block.source_flags         & "print_function")


def test_PythonBlock_auto_flags_px_flagps_futpf_1():
    block = PythonBlock(dedent('''
        from __future__ import print_function
        print(42)
    ''').lstrip(), auto_flags=True)
    assert     (block.flags                & "print_function")
    assert not (block.ast_node.input_flags & "print_function")
    assert     (block.source_flags         & "print_function")


def test_PythonBlock_auto_flags_px_flagpf_futpf_1():
    block = PythonBlock(dedent('''
        from __future__ import print_function
        print(42)
    ''').lstrip(), flags="print_function", auto_flags=True)
    assert     (block.flags                & "print_function")
    assert     (block.ast_node.input_flags & "print_function")
    assert     (block.source_flags         & "print_function")


def test_PythonBlock_auto_flags_pn_flagps_1():
    block = PythonBlock(dedent('''
        42
    ''').lstrip(), auto_flags=True)
    assert not (block.flags                & "print_function")
    assert not (block.ast_node.input_flags & "print_function")
    assert not (block.source_flags         & "print_function")


def test_PythonBlock_auto_flags_pn_flagpf_1():
    block = PythonBlock(dedent('''
        42
    ''').lstrip(), flags="print_function", auto_flags=True)
    assert     (block.flags                & "print_function")
    assert     (block.ast_node.input_flags & "print_function")
    assert not (block.source_flags         & "print_function")


def test_PythonBlock_auto_flags_pn_flagps_futpf_1():
    block = PythonBlock(dedent('''
        from __future__ import print_function
        42
    ''').lstrip(), auto_flags=True)
    assert     (block.flags                & "print_function")
    assert not (block.ast_node.input_flags & "print_function")
    assert     (block.source_flags         & "print_function")


def test_PythonBlock_auto_flags_pn_flagpf_futpf_1():
    block = PythonBlock(dedent('''
        from __future__ import print_function
        42
    ''').lstrip(), flags="print_function", auto_flags=True)
    assert     (block.flags                & "print_function")
    assert     (block.ast_node.input_flags & "print_function")
    assert     (block.source_flags         & "print_function")


def test_PythonStatement_flags_1():
    block = PythonBlock("from __future__ import unicode_literals\nx\n",
                        flags="division")
    s0, s1 = block.statements
    assert s0.block.source_flags == CompilerFlags("unicode_literals")
    assert s1.block.source_flags == CompilerFlags(0)
    assert s0.block.flags        == CompilerFlags("unicode_literals", "division")
    assert s1.block.flags        == CompilerFlags("unicode_literals", "division")


def test_PythonStatement_auto_flags_1():
    block = PythonBlock(
        "from __future__ import unicode_literals\nprint(1,file=x)\n",
        flags="division", auto_flags=True)
    s0, s1 = block.statements
    assert s0.block.source_flags == CompilerFlags("unicode_literals")
    assert s1.block.source_flags == CompilerFlags(0)
    expected = CompilerFlags("unicode_literals", "division", "print_function")
    assert s0.block.flags        == expected
    assert s1.block.flags        == expected


def test_parsable_1():
    block = PythonBlock("if 1:\n  2")
    assert block.parsable


def test_unparsable_1():
    block = PythonBlock("if 1:\n2")
    assert not block.parsable


def test_parsable_explicit_flags_1():
    block = PythonBlock("print(3, file=4)", flags="print_function")
    assert block.parsable


def test_parsable_missing_flags_no_auto_flags_1():
    block = PythonBlock("print(3, file=4)")
    assert not block.parsable


def test_parsable_missing_flags_auto_flags_1():
    block = PythonBlock("print(3, file=4)", auto_flags=True)
    assert block.parsable
