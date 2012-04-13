#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Класс "элемент грамматики". Что то, что объединяет 
# терминалы и нетерминалы в одно понятие
class GrammarElement (object):
    # перевод объекта в строку
    def __str__ (self):
        return str(self.value)
    
    # сравнение с другим объектом
    def __eq__(self, other):        
        return self.__class__ == other.__class__ and self.value == other.value
    
    # ну вобщем тоже сравнение
    def __ne__ (self,other):
        return not (self == other)



# Класс терминального элемента
class Terminal (GrammarElement):
    def __init__ (self, word):
        self.value = word
    


# Нетерминал в грамматике
class NonTerminal (GrammarElement):
    def __init__ (self, word):
        self.value = word


# Это определения класса продукции
# У него есть символ терминал слева и терминалы справа
class Production:
    # Предполагается. что источник продукции - это нетерминал
    # А источинком продукции может быть список порождаемых терминалов 
    # И нетерминалов
    def __init__ (self, source, targets):
        assert isinstance (source, NonTerminal)
        for target in targets:
            assert isinstance (target, GrammarElement)

        self.source = source        # левая часть выражения S -> A B C
        self.targets = targets      # массив правых частей S -> A B C
    
    def __str__ (self):
        return str(self.source) + "->" + ",".join(map (str, self.targets))

    def __hash__(self):
        return hash(tuple ([str(self.source)] + map(str,self.targets)))



# Микропарсер, который переводит элемент словаря в терминал или нетерминал
def word_to_grammar_element (word):
    if word == word.lower():
        return Terminal (word)
    elif word == word.upper():
        return NonTerminal (word)
    
    raise RuntimeError, "(unreachable)"


# Метод загружает грамматику в память
def load_grammar (source):
    grammar = dict ()
    for line in source:
        words = line.strip ().split (" ")
        if (len (words) < 3):
            continue
        assert (words [1] == "->")
        source = words [0]
        targets = words [2:]
        newProduction = Production (NonTerminal (source), \
                                    map (word_to_grammar_element, targets))
        if source not in grammar:
            grammar [source] = []
        
        grammar [source].append(newProduction)
        
    return grammar
