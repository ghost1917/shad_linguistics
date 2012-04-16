#!/usr/bin/env python

# GLOSSARY
################################################################################
#   * Term
# Either terminal or non-terminal symbol.
#   * Production
# A right-hand side of a production rule; formally, a sequence of terms.
#   * Rule
# A set of all possible production rules, grouped by left-hand side.
#
# For example, in grammar:
#   S  -> NP VP
#   NP -> D N
#   NP -> John
#   D  -> the
#   D  -> a
#   N  -> cat
#   N  -> dog
#   ...
#
# "S", "NP", "VP", "D", "N", "John", "the", "a", "cat", "god"
#   are terms.
# [ "NP, "VP" ], [ "D", "N" ], [ "John" ], [ "the" ], [ "a" ], ...
#   are productions for productions rules (1) and (2) respectivelly.
# ("S", [ [ "NP" "VP" ] ]), ("NP", [ [ "D", "N" ], [ "John"] ]), ...
#   are rules.

import sys

class Feature:
    def __init__(self, str):
        parts = str.split("=")
        self.name = parts[0]
        self.val = parts[1] if len(parts) > 1 else None

    def __str__(self):
        return self.name + "=" + self.val

    def __repr__(self):
        return self.name if self.val is None else self.name + "=" + self.val

class Production(object):
    def __init__(self, *terms):
        self.terms = terms
        self.setfeatures = dict()
        self.checkfeatures = set()

    def __len__(self):
        return len(self.terms)

    def __getitem__(self, index):
        return self.terms[index]

    def __iter__(self):
        return iter(self.terms)

    def __repr__(self):
        return " ".join(str(t) for t in self.terms) + " # " + str(self.setfeatures) + " " + str(self.checkfeatures)

    def __eq__(self, other):
        if not isinstance(other, Production):
            return False
        return self.terms == other.terms

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self.terms)

    def addfeatures(self, features):
        for f in features:
            if f.val is None:
                self.checkfeatures.add(f.name)
            else:
                self.setfeatures[f.name] = f.val


class Rule(object):
    def __init__(self, name):
        self.name = name
        self.productions = []
        print self.name, self.productions

    def __str__(self):
        return self.name

    def __repr__(self):
        return "%s -> %s" % (
            self.name,
            " | ".join(repr(p) for p in self.productions))

    def add(self, *productions):
        self.productions.extend(productions)


# State is a 3-tuple of a dotted rule, start column and end column.
class State(object):
    # A dotted rule is represented as a (name, production, dot_index) 3-tuple.
    def __init__(self, name, production, dot_index, start_column, checkfeatures, rawfeatures, resfeatures):
        self.name = name
        self.production = production
        self.dot_index = dot_index

        self.start_column = start_column
        self.end_column = None
        self.checkfeatures = checkfeatures
        self.rawfeatures = rawfeatures
        self.resfeatures = resfeatures

        self.rules = [ term for term in self.production if isinstance(term, Rule) ]

    def __repr__(self):
        terms = [ str(term) for term in self.production ]
        terms.insert(self.dot_index, "$")

        return "%-5s -> %-23s [%2s-%-2s]" % (
            self.name,
            " ".join(terms),
            self.start_column,
            self.end_column)

    def __eq__(self, other):
        return \
            (self.name,  self.production,  self.dot_index,  self.start_column) == \
            (other.name, other.production, other.dot_index, other.start_column)

    def __ne__(self, other):
        return not (self == other)

    # Note that objects are hashed by (name, production), but not the whole state.
    def __hash__(self):
        return hash((self.name, self.production))

    def is_completed(self):
        return self.dot_index >= len(self.production)

    def get_next_term(self):
        if self.is_completed():
            return None
        return self.production[self.dot_index]




# Column is a list of states in a chart table.
class Column(object):
    def __init__(self, index, token):
        self.index = index
        self.token = token

        self.states = []
        self._unique_states = set()

    def __str__(self):
        return str(self.index)

    def __len__(self):
        return len(self.states)

    def __iter__(self):
        return iter(self.states)

    def __getitem__(self, index):
        return self.states[index]

    def add(self, state):
        if state not in self._unique_states:
            self._unique_states.add(state)
            state.end_column = self
            self.states.append(state)
            return True
        return False

    def dump(self, only_completed = False):
        print " [%s] %r" % (self.index, self.token)
        print "=" * 40
        for s in self.states:
            if only_completed and not s.is_completed():
                continue
            print repr(s)
        print "=" * 40
        print




class Node(object):
    def __init__(self, value, children):
        self.value = value
        self.children = children

    def dump(self, level = 0):
        print "  " * level + str(self.value)
        for child in self.children:
            child.dump(level + 1)

# INTERNAL SUBROUTINES FOR EARLEY ALGORITHM
################################################################################

def predict(column, rule):
    for production in rule.productions:
        #print "-",rule.name, production, production.setfeatures, production.checkfeatures
        column.add(
            State(
                rule.name,
                production,
                0,
                column,
                production.checkfeatures,
                production.setfeatures,
                dict()))
        #print "-", production.setfeatures

def scan(column, state, token):
    if token != column.token:
        return
    print "=",token, state.name, state.production, state.rules, state.rawfeatures, state.resfeatures
    column.add(
        State(
            state.name,
            state.production,
            state.dot_index + 1,
            state.start_column,
            state.checkfeatures,
            state.rawfeatures,
            state.rawfeatures))
    print "=",state.rawfeatures

def is_value(s):
    return s is not None and s.find('_') == -1

# a giant man eats

def merge_features(f1, f2, rulecheck, ruleset, pos, total):
    print "#",f1, f2, rulecheck, ruleset, pos

    res = dict()

    for rawkey in rulecheck:
        keys = rawkey.split('_')
        key = keys[0]

        needCheckV2 = len(keys) == 1 or str(pos) in keys[1:]

        v1 = f1[key] if ((key in f1) and is_value(f1[key])) else None
        v2 = f2[key] if ((key in f2) and is_value(f2[key])) else None

        print v1, v2, needCheckV2

        if not needCheckV2:
            res[key] = v1
        elif (v1 is None or v1 == v2):
            res[key] = v2
        elif v2 is None:
            res[key] = v1
        else:
            print dict()
            return (False, dict())

    if pos == total - 1:
        for key in ruleset.keys():
            res[key] = ruleset[key]

        for rawkey in rulecheck:
            keys = rawkey.split('_')
            key = keys[0]

            for v in keys[1:]:
                if v[0] == '+' and v[1:] != res[key] and res[key] is not None:
                    return (False, dict())

    print res

    return (True, res)

def complete(column, state):
    if not state.is_completed():
        return
    for prev_state in state.start_column:
        term = prev_state.get_next_term()
        if not isinstance(term, Rule):
            continue
        if term.name == state.name:
            print "#",term.name, prev_state.name
            (fOK, features) = merge_features(prev_state.resfeatures, state.resfeatures, prev_state.checkfeatures, prev_state.rawfeatures, prev_state.dot_index, len(prev_state.production.terms));
            if fOK:
                column.add(
                    State(
                        prev_state.name,
                        prev_state.production,
                        prev_state.dot_index + 1,
                        prev_state.start_column,
                        prev_state.checkfeatures,
                        prev_state.rawfeatures,
                        features))

GAMMA_RULE = "GAMMA"

# ENTRY POINT FOR EARLEY ALGORITHM
################################################################################

def parse(starting_rule, text):
    text_with_indexes = enumerate([ None ] + text.lower().split())

    table = [ Column(i, token) for i, token in text_with_indexes ]
    table[0].add(State(GAMMA_RULE, Production(starting_rule), 0, table[0], dict(), dict(), dict()))

    for i, column in enumerate(table):
        for state in column:
            if state.is_completed():
                complete(column, state)
            else:
                term = state.get_next_term()
                if isinstance(term, Rule):
                    predict(column, term)
                elif i + 1 < len(table):
                    scan(table[i + 1], state, term)

        # XXX(sandello): You can uncomment this line to see full dump of
        # the chart table.
        #
        # column.dump(only_completed = False)

    # Find Gamma rule in the last table column or fail otherwise.
    for state in table[-1]:
        if state.name == GAMMA_RULE and state.is_completed():
            return state
    else:
        raise ValueError, "Unable to parse the text."

# AUXILIARY ROUTINES
################################################################################

def build_trees(state):
    return build_trees_helper([], state, len(state.rules) - 1, state.end_column)

def build_trees_helper(children, state, rule_index, end_column):
    if rule_index < 0:
        return [Node(state, children)]
    elif rule_index == 0:
        start_column = state.start_column
    else:
        start_column = None

    rule = state.rules[rule_index]
    outputs = []

    for prev_state in end_column:
        if prev_state is state:
            break
        if prev_state is state or not prev_state.is_completed() or prev_state.name != rule.name:
            continue
        if start_column is not None and prev_state.start_column != start_column:
            continue
        for sub_tree in build_trees(prev_state):
            for node in build_trees_helper([sub_tree] + children, state, rule_index - 1, prev_state.start_column):
                outputs.append(node)

    return outputs

def qtree(node):
    # http://yohasebe.com/rsyntaxtree/
    if node.value.name == GAMMA_RULE:
        return qtree(node.children[0])

    sub_qtrees = dict(
        (child.value.name, qtree(child))
        for child in node.children)

    return "[{0} {1}]".format(
        node.value.name,
        " ".join(
            sub_qtrees[term.name] if isinstance(term, Rule) else term
            for term in node.value.production)
        )

################################################################################

def load_grammar(iterable):
    non_terminals = dict()
    starting_rule = None

    def get_term(part):
        if part == part.lower():
            return part
        if part == part.upper():
            if part not in non_terminals:
                non_terminals[part] = Rule(part)
            return non_terminals[part]
        raise RuntimeError, "(unreachable)"

    for n, line in enumerate(iterable):
        parts = line.strip().split()

        for part in parts:
            if part != part.upper() and part != part.lower():
                raise RuntimeError, "Malformed line #{0}: Mixed-case for term '{1}'".format(n + 1, part)

        if len(parts) == 0:
            continue

        if len(parts) == 1:
            if parts[0] not in non_terminals:
                raise RuntimeError, "Malformed line #{0}: Unknown non-terminal '{1}'".format(n + 1, parts[0])
            else:
                starting_rule = parts[0]
                continue

        if parts[1] != "->":
            raise RuntimeError, "Malformed line #{0}: Second part have to be '->'".format(n + 1)

        lhs = get_term(parts[0])
        bracket1 = len(parts)
        bracket2 = -1
        try:
            bracket1 = parts.index('[')
            bracket2 = parts.index(']')
        except:
            pass

        rhs = map(get_term, parts[2:bracket1])
        features = map(Feature, parts[bracket1+1:bracket2])

        if not isinstance(lhs, Rule):
            raise RuntimeError, "Malformed line #{0}: Left-hand side have to be a non-terminal".format(n + 1)

        prod = Production(*rhs)
        prod.addfeatures(features)
        lhs.add(prod)

    if starting_rule:
        return non_terminals[starting_rule]
    else:
        return non_terminals["S"]

################################################################################

if __name__ == "__main__":
    # You can specify grammar either by hard-coding it or by loading from file.
    #
    # (Specifying grammar in code)
    #     SYM  = Rule("SYM", Production("a"))
    #     OP   = Rule("OP",  Production("+"), Production("*"))
    #     EXPR = Rule("EXPR")
    #     EXPR.add(Production(SYM))
    #     EXPR.add(Production(EXPR, OP, EXPR))
    #
    # (Loading grammar from file)
    #     g = load_grammar(open("a.txt"))

    g = load_grammar("""
        N -> hat [ num=sg def=a ]
        N -> elephant [ num=sg def=an ]
        N -> garden [ num=sg def=a ]
        N -> apple [ num=sg def=an ]
        N -> time [ num=sg def=a ]
        N -> flight [ num=sg def=a ]
        N -> banana [ num=sg def=a ]
        N -> flies [ num=sg def=a ]
        N -> boy [ num=sg def=a ]
        N -> man [ num=sg def=a ]
        N -> telescope [ num=sg def=a ]

        NN -> john [ pers=3 num=sg ]
        NN -> mary [ pers=3 num=sg ]
        NN -> houston [ pers=3 num=sg ]

        ADJ -> giant [ def=a ]
        ADJ -> red [ def=a ]

        D -> the [ ]
        D -> a [ def=a ]
        D -> an [ def=an ]

        V -> book
        V -> books
        V -> eat [ pers=3 num=pl ]
        V -> eats [ pers=3 num=sg ]
        V -> sleep
        V -> sleeps
        V -> give
        V -> gives
        V -> walk
        V -> walks
        V -> saw

        P -> with
        P -> in
        P -> on
        P -> at
        P -> through

        PR -> he
        PR -> she
        PR -> his
        PR -> her

        NP -> NN [ pers num ]
        NP -> PR [ pers num ]
        NP -> PR N [ pers num ]
        NP -> NP PP  [ pers num ]
        NP -> D N [ def ]
        NP -> D ADJ N [ def_0_1 ]

        PP -> P NP

        VP -> V [ pers num ]
        VP -> V NP
        VP -> V NP NP
        VP -> VP PP

        S -> NP VP [ pers num ]
        S -> VP
    """.splitlines())

    def parse_and_print(g, s):
        for tree in build_trees(parse(g, s)):
            print "-" * 80
            print qtree(tree)
            print
            tree.dump()
            print

    #parse_and_print(g, "an giant man eats")

    #parse_and_print(g, "book the flight through houston")
    #parse_and_print(g, "john saw the boy with the telescope")
    #parse_and_print(g, "john sleeps")
    #parse_and_print(g, "he gives mary his hat")
    #parse_and_print(g, "an elephant walks in the garden")
    #parse_and_print(g, "a giant man eats a giant apple")


    text = ""
    while True:
        text = sys.stdin.readline()
        try:
            parse_and_print(g, text.strip())
        except:
            print "!!! failed"

        
