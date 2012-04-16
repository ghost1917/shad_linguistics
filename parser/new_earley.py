#!/usr/bin/env python
# -*- coding: utf-8 -*-

from grammar import load_grammar, Production, Terminal, NonTerminal 

# Это правило с точкой... но не совсем.
# Оно имеет 3 члена:
# - продукция, которая используется
# - положение точки 
# - и положение парсера, кода это правило впервые появилось, в которой оно появилось в первый раз
class DottedRule:
    def __init__ (self, production, start_index, end_index = -1, dot_index = 0, table_position = [0,0]):
        assert isinstance (production, Production)
        self.production   = production              # продукция
        self.dot_index    = dot_index               # положение точки внутри правила с точкой
        self.start_index  = start_index             # откуда начинается правило
        self.table_position  = table_position       # положение правила в таблице правил
        self.prev_rules      = []                   # "координаты правил", из которых было получено данное при complete
                                                    # эта фишка нужна, для печати дерева
        
        if end_index == -1:                         # индекс конца правила
            self.end_index = start_index
        else:
            self.end_index = end_index
            
    # Дошла ли точка в правиле до самого его конца
    def is_completed (self):
        return self.dot_index >= len (self.production.targets) 

    # Выводит правило на экран в детальном виде    
    def __repr__(self):
        elements = [ str(element) for element in self.production.targets ]
        elements.insert(self.dot_index, "$")

        return "%-5s -> %-23s [%2s-%-2s]" % (
            self.production.source,
            " ".join(elements),
            self.start_index,
            self.end_index)

    def __eq__(self, other):
        return \
            (self.production.source,  self.production.targets,  self.dot_index,  self.start_index) == \
            (other.production.source, other.production.targets, other.dot_index, other.start_index)

    def __ne__(self, other):
        return not (self == other)
    
    # Это такой ленивый способ сделать копию правила, чтобы вставить ее в таблицу.
    # Мы только обновляем значение конца правила, и передаем положение, под которым 
    # оно будет храниться в таблице разбора
    def make_a_copy (self, end_index, table_position):
        return DottedRule (self.production, self.start_index, end_index, self.dot_index+1, table_position)
    
    # Получение правила, которое стоит сразу после точки
    def get_dotted_target (self):
        return self.production.targets [self.dot_index]

    def __hash__(self):
        return hash(self.production)
    
        

# Каждая колонка хранит в себе список правил с точкой
# и множество уникальных правил
# это для того, чтобы одно и то же правило нельзя было 
# бы добавить в одну колонку два раза 
class ParsingTableColumn:
    def __init__ (self):
        self.dotted_rules_list = list ()
        self.dotted_rules_set  = set ()

    # Добавляется еще одно правило с точкой в список.
    # Проверка используется для того, чтобы в список 
    # Попадали только уникальные правила
    def add (self, dotted_rule):
        if dotted_rule not in self.dotted_rules_set:
            self.dotted_rules_set.add(dotted_rule)
            self.dotted_rules_list.append(dotted_rule)

    # Перегрузка некоторых операторов. Теперь  
    # с колонкой можно обращаться как с массивом
    def __iter__(self):
        return iter(self.dotted_rules_list)

    def __getitem__(self, index):
        return self.dotted_rules_list[index]

    def __len__ (self):
        return len (self.dotted_rules_list)
    
    def __str__ (self):
        result = "" 
        for dotted_rule in self.dotted_rules_list:
            result +=  repr (dotted_rule) + "\n"
            
        return result


# Таблица правил
class ParsingTable:
    def __init__ (self):
        self.columns = [ParsingTableColumn ()]

    def __iter__(self):
        return iter(self.columns)

    def __getitem__(self, index):        
        return self.columns[index]

    def get_free_pos(self, index):        
        return [index, len (self.columns[index])]

    def __str__ (self):
        result = "" 
        for i in xrange (len (self.columns)):
            result +=  "col " + str (i) + "\n"
            result +=  "==================\n"
            result += str (self.columns [i])
            result +=  "------------------\n\n"
        return result



# Ну и собственно говоря парсер
class EarleyParser:
    def __init__ (self, grammar):
        self.grammar = grammar      # На вход парсер получает грамматику
        
    def parse (self, sentence):
        print sentence
        
        # Бьем предложение на слова
        words = sentence.rstrip ().split (" ")
        # Пустое слово в конце - так как число дырок 
        # между словам = числу слов +1
        words.append (None)

        
        # таблица, в которой будет производиться парсинг
        parsing_table = ParsingTable ()

        # добавиляем в начало первый переход
        # ну пусть это будет правило gamma->s 
        initial_production = Production (NonTerminal ("GAMMA"), [NonTerminal ("S")]);
        parsing_table [0].add(DottedRule (initial_production, 0))
        
        # дальше делаем цикл по словам (по промежуткам между словами)
        for input_position in xrange (len (words)):
            # цикл по элементам текущей колонки в табице
            for rule in parsing_table [input_position]:
                # если точка в правиле дошла до конца - пытаемся сделать ему complete
                if rule.is_completed ():
                    self._complete(parsing_table, rule, input_position)
                    continue
                
                
                current_element = rule.get_dotted_target ()
                # Для терминала пробуем сделать scan
                if isinstance (current_element, Terminal):
                    if (current_element.value == words [input_position]):
                        self._scan(parsing_table, rule, input_position)
                    
                # Для нетерминала - predict
                elif isinstance (current_element, NonTerminal):
                    self._predict(parsing_table, current_element, input_position)
                      
        return parsing_table
             
        
    # Вот эти черточки в начале функций означают, что это приватные методы
    # в питоне вообще-то все методы и переменные публичные.
    # но таким образом можно "попросить" пользователя не лазить
    # внутрь реализации
    def _predict (self, parsing_table, non_terminal, input_position):
        for production in grammar [str (non_terminal)]: 
            free_position = parsing_table.get_free_pos(input_position)
            parsing_table [input_position].add (DottedRule (production,
                                                            input_position, 
                                                            table_position = free_position))
    
    
        
    def _scan (self, parsing_table, dotted_rule, input_position):
        if len (parsing_table.columns) == input_position + 1:
            parsing_table.columns.append (ParsingTableColumn ())
        free_position = parsing_table.get_free_pos(input_position + 1)
        parsing_table [input_position + 1].add (dotted_rule.make_a_copy(input_position + 1, free_position))
    
    
    def _complete (self, parsing_table, completed_rule, input_position):
        for old_dotted_rule in parsing_table [completed_rule.start_index]:
            if old_dotted_rule.is_completed ():
                continue

            if completed_rule.production.source == old_dotted_rule.get_dotted_target ():
                free_position = parsing_table.get_free_pos(input_position)
                new_rule = old_dotted_rule.make_a_copy (input_position, free_position)
                # Вот это мы проставляем ссылки на правила, из которых 
                # удалось построить текущее правило
                new_rule.prev_rules = list (old_dotted_rule.prev_rules)
                new_rule.prev_rules.append (completed_rule.table_position)
                
                parsing_table [input_position].add (new_rule)


    # Метод проверяет, удалось ли правильно разобрать предложение
    def is_correct_sentence (self, parsing_table):
        for rule in parsing_table[-1]:
            if str (rule.production.source) == "GAMMA" and rule.start_index == 0:
                return True
        return False


    # Как мы печатаем дерево?
    # Первая стадия - сик анд дистрой:
    # Проходим по последней колонке, находил полностью разобранные предложения
    # Для каждого из них строим дерево разбора
    def print_all_parsing_trees (self, parsing_table):
        for rule in parsing_table[-1]:
            if str (rule.production.source) == "GAMMA" and rule.start_index == 0:
                self._print_parsing_tree (parsing_table, rule.table_position)


    # Вторая стадия 
    def _print_parsing_tree (self, parsing_table, root):
        # Дерево строится обходом в глубину
        dfs_stack = [(root,0,None)]
        prev_state = None
        while (len (dfs_stack) != 0):
            # пока стек не опустеет, вынимаем из него верхушку...
            state, depth, parent = dfs_stack.pop ();
            # ... и укладываем всех детей в стек
            for child in reversed (parsing_table [state[0]][state[1]].prev_rules):
                dfs_stack.append((child, depth+1, state))
            
            # Потом печатаем информацию о текущем элементе разбора
            production = parsing_table [state[0]][state[1]].production
            element_name = str (production.source)            
            if (prev_state is None):
                print "%s" % element_name,

            elif (parent [0] == prev_state [0] and parent [1] == prev_state [1]):
                print "->%3s" % element_name,

            else:
                spaces = " " * (6 * depth)
                print "%s->%3s" % (spaces, element_name),
            
            if (len (production.targets) == 1 and 
                isinstance (production.targets [0], Terminal)):
                print "-> %s" % production.targets [0] 
                
            prev_state = state
            
                

if __name__ == "__main__":
    grammar = load_grammar("""
        N -> flight

        NN -> houston

        D -> the

        V -> book

        P -> through

        NP -> NN
        NP -> D N
        NP -> NP PP

        PP -> P NP

        VP -> V
        VP -> V NP
        VP -> V NP NP
        VP -> VP PP

        S -> NP VP
        S -> VP
    """.splitlines())

    earley_parser = EarleyParser (grammar)
    parsing_table = earley_parser.parse(sentence="book the flight through houston")
    
    print parsing_table
    if earley_parser.is_correct_sentence (parsing_table):
        print "Sentence is correct"
    else:
        print "Sentence is not correct"
        
    earley_parser.print_all_parsing_trees(parsing_table)
    
    
      
    
    
    
    
    
    

