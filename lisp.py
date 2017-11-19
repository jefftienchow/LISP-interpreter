import sys
class Environment():
    '''Environment object that stores the variables in that environment and its parent if it has one'''
    def __init__(self):
        self.variables = {}
        self.parent = None

class Function():
    '''Function object that storesthe parameters, body, and environment in which the function was defined'''
    def __init__(self):
        self.parameters = []
        self.body = None
        self.env = None

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



def multiply(args):
    '''function to multiply numbers'''
    total = 1
    for i in args:
        total*=i
    return total

carlae_builtins = {
    '+': sum,
    '-': lambda args: -args[0] if len(args) == 1 else (args[0] - sum(args[1:])),
    '*': multiply,
    '/': lambda args: args[0] if len(args)==1 else (args[0]/multiply(args[1:]))
}
builtins = Environment()
builtins.variables = carlae_builtins

def go_up(variable,environment):
    '''recursively goes up the tree until we find the variable in the environment or there are no more parents'''
    if variable in environment.variables:

        return environment.variables[variable]
    elif environment.parent!=None:
        return go_up(variable,environment.parent)
    else:
        raise EvaluationError



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
    if type(tree) == float or type(tree)==int or type(tree)==Function:
        return tree
    elif type(tree)!= list:
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
            new_list = []
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
    x = input('test')
    globe = Environment()
    globe.parent = builtins
    while x != 'exit':
        token = tokenize(x)
        parsed = parse(token)
        try:
            print (evaluate(parsed,globe))
        except BaseException as e:
            print ('An exception occurred: {}'.format(e))
        x = input('test')
