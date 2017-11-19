import sys
class Environment():
    '''Environment object that stores the variables in that environment and its parent if it has one'''
    def __init__(self):
        self.variables = {}
        self.parent = None

class Function():
    '''Function object that stores the parameters, body, and environment in which the function was defined'''
    def __init__(self):
        self.parameters = []
        self.body = None
        self.env = None

class LinkedList():
    '''Linked list object that stores the element value and pointer to next object in list'''
    def __init__(self):
        self.elt = None
        self.next = None

class EvaluationError(Exception):
    """Exception to be raised if there is an error during evaluation."""
    pass


def tokenize(source):
    """
    Splits an input string into meaningful tokens (left parens, right parens,
    other whitespace-separated values).  Returns a list of strings.

    Arguments:
        source (str): a string containing the source code of a carlae
                      expression
    """
    final = []
    was_space = False
    cur = ''
    cont = True
    for i in range(len(source)):
        #ignores commented line
        if source[i]==';':
            cont = False
        if cont:
            #adds the current word to the final list if we see a parenthesis
            if source[i] =='(' or source[i]==')':
                if len(cur)>0:
                    final.append(cur)
                    cur = ''
                final.append(source[i])
                was_space = False
            #adds current word to list if we see the first space after a word
            elif source[i] == ' ' or source[i]=="\n":
                if not was_space and len(cur)>0:
                    final.append(cur)

                    cur = ''
                was_space = True
            else:
                cur+=source[i]
                was_space = False
                if i==len(source)-1:
                    final.append(cur)
        elif source[i] == "\n":
            cont = True
    return final

def express(tokens):
    '''recursive function that tokenizes S-expressions'''
    final = []
    cur = 1
    go_ahead = 0
    carry = 0
    for i in range(len(tokens)):
        if go_ahead > 0:
            go_ahead -= 1
            continue
        if tokens[i] == '(':
            returned = express(tokens[i + 1:])
            #skips ahead to the next expression to not recount words
            go_ahead += returned[1]
            carry += returned[1]+1

            final.append(returned[0])
        else:
            if tokens[i] == ')':
                return (final, cur + carry)
            try:
                x = float(tokens[i])
                final.append(x)
                cur += 1
            except ValueError:
                final.append(tokens[i])
                cur += 1
    return final

def parse(tokens):
    """
    Parses a list of tokens, constructing a representation where:
        * symbols are represented as Python strings
        * numbers are represented as Python ints or floats
        * S-expressions are represented as Python lists

    Arguments:
        tokens (list): a list of strings representing tokens
    """
    open = 0
    #if the parentheses don't match, raise error
    for i in tokens:
        if i=="(":
            open+=1
        if i==")":
            open-=1
        if open<0:
            raise SyntaxError
    if open!=0:
        raise SyntaxError

    #recurses if necessary
    for i in range(len(tokens)):
        if tokens[i] == '(':
            return express(tokens[i+1:])[0]
        else:
            try:
                x=float(tokens[i])
                return x
            except ValueError:
                return tokens[i]

def copy_list(args):
    '''creates a new list that is a copy of args list'''
    original = LinkedList()
    original.elt = args.elt
    new_cur = original
    cur = args
    while cur.next!=None:
        cur = cur.next
        new = LinkedList()
        new_cur.next = new
        new.elt = cur.elt
        new_cur = new
    original.last = new_cur
    return original


def multiply(args):
    '''function to multiply numbers'''
    total = 1
    for i in args:
        total*=i
    return total

def turntolist(args):
    '''turns args into a linked list'''
    if len(args)==0:
        cur = LinkedList()
        return cur
    original = LinkedList()
    original.length = len(args)
    cur = original
    cur.elt = evaluate(args[0])
    for i in args[1:]:
        new = LinkedList()
        cur.next = new
        new.elt = evaluate(i)
        cur = new
    return original

def car(args):
    '''returns first element of list'''
    if args[0].elt == None:
        raise EvaluationError
    return args[0].elt

def cdr(args):
    '''returns all but first element of list'''
    if args[0].elt == None:
        raise EvaluationError
    return args[0].next

def length(args):
    '''returns the length of a LinkedList'''
    if args[0].elt==None:
        return 0
    counter = 1
    cur = args[0]
    while cur.next!=None:
        counter+=1
        cur = cur.next
    return counter

def elt_at_index(args):
    '''indexes into a LinkedList'''
    size = length(args)
    if size<=args[1]:
        raise EvaluationError
    cur = args[0]
    counter = 0
    for i in range(args[1]):
        counter +=1
        cur = cur.next
    return cur.elt

def concat(args):
    '''connects two LinkedLists'''
    if len(args)==0:
        cur = LinkedList()
        return cur
    real_args = []
    #removes empty lists first
    for i in args:
        if i.elt != None:
            real_args.append(i)
    original = copy_list(real_args[0])
    cur = original
    for i in range(len(real_args)-1):
        while cur.next!=None:
            cur = cur.next
        new = copy_list(real_args[i+1])
        cur.next = new
        cur = cur.next
    return original

def map(args):
    '''creates a new list that is a function of the elemnts of the old one'''
    function = args[0]
    mapped = copy_list(args[1])
    map_len = length([mapped])
    cur = mapped
    if type(function)==Function:
        for i in range(map_len):
            value = cur.elt
            new_environment = Environment()
            new_environment.parent = function.env
            # assigns the parameters in the new environment
            for i in range(len(function.parameters)):
                x = evaluate(['define', function.parameters[i], value], new_environment)
            cur.elt =  evaluate(function.body, new_environment)
            cur = cur.next
        return mapped
    for i in range(map_len):

        cur.elt = function([cur.elt])
        cur = cur.next

    return mapped

def filter(args):
    '''filters out the elements of the list that evaluate to false'''
    function = args[0]
    cur = args[1]
    list_len = length([cur])
    first = LinkedList()
    new_cur = first
    started = False
    for i in range(list_len):
        value = cur.elt
        new_environment = Environment()
        new_environment.parent = function.env
        # assigns the parameters in the new environment
        for i in range(len(function.parameters)):
            evaluate(['define', function.parameters[i], value], new_environment)
        cur = cur.next
        if evaluate(function.body, new_environment):
            if not started:
                new_cur.elt = value
                started = True
            else:
                new_cur.next = LinkedList()
                new_cur = new_cur.next
                new_cur.elt = value
    return first

def reduce(args):
    '''applies a function to the elements of a list in series, storing the current result'''
    function = args[0]
    cur = args[1]
    list_len = length([cur])
    cur_value = args[2]
    if type(function) == Function:
        for i in range(list_len):
            #applies the function to the current element and the last element
            value = cur.elt
            new_environment = Environment()
            new_environment.parent = function.env
            # assigns the parameters in the new environment
            evaluate(['define', function.parameters[0], cur_value], new_environment)
            evaluate(['define', function.parameters[1], value], new_environment)
            cur_value = evaluate(function.body, new_environment)
            cur = cur.next
        return cur_value
    for i in range(list_len):
        value = cur.elt
        cur_value = function([cur_value,value])
        cur = cur.next
    return cur_value

#builtin variables that can be called from any environment
carlae_builtins = {
    '+': sum,
    '-': lambda args: -args[0] if len(args) == 1 else (args[0] - sum(args[1:])),
    '*': multiply,
    '/': lambda args: args[0] if len(args)==1 else (args[0]/multiply(args[1:])),
    '#t': True,
    '#f': False,
    '=?': lambda args: all(args[0]==args[i] for i in range(len(args))),
    '>': lambda args: all(args[i]>args[i+1] for i in range(len(args)-1)),
    '>=': lambda args: all(args[i]>=args[i+1] for i in range(len(args)-1)),
    '<': lambda args: all(args[i]<args[i+1] for i in range(len(args)-1)),
    '<=': lambda args: all(args[i]<=args[i+1] for i in range(len(args)-1)),
    'list': turntolist,
    'car': car,
    'cdr': cdr,
    'length': length,
    'elt-at-index': elt_at_index,
    'concat': concat,
    'map': map,
    'filter': filter,
    'reduce': reduce,
    'begin': lambda args:args[-1]
}

builtins = Environment()
builtins.variables = carlae_builtins

def go_up(variable,environment,return_env = False):
    '''recursively goes up the tree until we find the variable in the environment or there are no more parents'''
    if variable in environment.variables:
        if return_env:
            return environment
        return environment.variables[variable]
    elif environment.parent!=None:

        return go_up(variable,environment.parent,return_env)
    else:
        raise EvaluationError

def evaluate_file(string,environment=None):
    '''opens are reads a file and then tokenizes, parses, and evalutes the expression'''
    x = open(string)
    next = x.read()
    token = tokenize(next)
    parsed = parse(token)
    return evaluate(parsed,environment)

def evaluate(tree,environment=None):
    """
    Evaluate the given syntax tree according to the rules of the carlae
    language.

    Arguments:
        tree (type varies): a fully parsed expression, as the output from the
                            parse function
    """
    #creates a new environment if none are passed
    if not environment:
        environment = Environment()
        environment.parent = builtins
    if type(tree) == float or type(tree)==int or type(tree)==Function or type(tree)==LinkedList or type(tree)==bool:
        return tree
    elif type(tree)!= list:
        if type(tree)==str:
            if tree in environment.variables:
                return environment.variables[tree]
            else:
                return go_up(tree,environment.parent)

    elif tree==[]:
        raise EvaluationError
    else:
        #if the first object is a lambda function, we evaluate it in a new child environment
        if type(tree[0])==list:
            function = evaluate(tree[0],environment)
            if len(tree)-1!=len(function.parameters):
                raise EvaluationError
            new_environment = Environment()
            new_environment.parent = function.env
            for i in range(len(function.parameters)):
                evaluate(['define',function.parameters[i],tree[i+1]],new_environment)

            return evaluate(function.body,new_environment)
        else:
            if tree[0]=='define':
                if type(tree[1])==list:
                    #simplifies assignments where the name is an S-expression
                    return evaluate(['define',tree[1][0],['lambda',tree[1][1:],tree[2]]],environment)
                else:
                    answer = evaluate(tree[2],environment)
                environment.variables[tree[1]] = answer
                return answer
            elif tree[0]=='lambda':
                try:
                    funct = Function()
                    funct.parameters = tree[1]
                    funct.body = tree[2]
                    funct.env = environment
                    return funct
                except IndexError:
                    raise EvaluationError
            elif tree[0]=='if':
                cond = evaluate(tree[1],environment)
                if cond:
                    return evaluate(tree[2],environment)
                return evaluate(tree[3],environment)
            elif tree[0]=='and':
                for i in tree[1:]:
                    if not evaluate(i,environment):
                        return False
                return True
            elif tree[0]=='or':
                for i in tree[1:]:
                    if evaluate(i,environment):
                        return True
                return False
            elif tree[0]=='not':
                return not evaluate(tree[1],environment)
            elif tree[0]=='let':
                new_environment = Environment()
                new_environment.parent = environment
                evaluated = []
                #evalutes arguments in current environment
                for i in tree[1]:
                    evaluated.append(evaluate(i[1],environment))
                for i in range(len(tree[1])):
                    evaluate(['define',tree[1][i][0],evaluated[i]],new_environment)
                return evaluate(tree[2],new_environment)
            elif tree[0]=='set!':
                eval = evaluate(tree[2],environment)
                #finds the first higher environment where the variable is stored
                upper_environment = go_up(tree[1],environment.parent,True)
                return evaluate(['define',tree[1],eval],upper_environment)

            #if the first object is not a special form, it is a function
            elif tree[0] in environment.variables:
                operator = environment.variables[tree[0]]
            else:
                operator = go_up(tree[0],environment.parent)

            if type(operator)== Function:
                #checks if the input is the correct length
                if len(tree)-1!=len(operator.parameters):
                    raise EvaluationError
                new_environment = Environment()
                new_environment.parent = operator.env
                tree_values = []
                #evalutes the input in the current environment
                for i in range(len(operator.parameters)):
                    tree_values.append(evaluate((tree[i+1]),environment))
                #assigns the parameters in the new environment
                for i in range(len(operator.parameters)):
                    evaluate(['define',operator.parameters[i],tree_values[i]],new_environment)
                return evaluate(operator.body,new_environment)
            else:
                #performs the function on the given objects
                new_list = []
                for i in tree[1:]:
                    x = evaluate(i, environment)
                    new_list.append(x)
                answer = operator(new_list)
                return answer



def result_and_env(tree,environment=None):
    '''runs evaluate and returns a tuple of what is returned from evaluate and the environment that was used'''
    if not environment:
        environment = Environment()
        environment.parent = builtins
    x = evaluate(tree,environment)
    return (x,environment)


if __name__ == '__main__':
    # code in this block will only be executed if lab.py is the main file being
    # run (not when this module is imported)
    globe = Environment()
    globe.parent = builtins
    args = sys.argv
    #evalutes  command line arguments
    for i in args[1:]:
        token = tokenize(i)
        parsed = parse(token)
        evaluate_file(parsed,globe)
    x = input('test')

    #REPL to test code
    while x != 'exit':
        token = tokenize(x)
        parsed = parse(token)
        try:
            print (evaluate(parsed,globe))
        except BaseException as e:
            print ('An exception occurred: {}'.format(e))
        x = input('test')
