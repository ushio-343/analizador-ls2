from flask import Flask, render_template, request
import ply.lex as lex
import ply.yacc as yacc

app = Flask(__name__)

# List of token names
tokens = [
    'ID', 'NUMBER', 'STRING',
    'PLUS', 'EQUAL', 'OPEN_PAREN', 'CLOSE_PAREN',
    'OPEN_BRACE', 'CLOSE_BRACE', 'COMMA', 'SEMICOLON',
    'DOT', 'PUBLIC', 'CLASS', 'STATIC', 'VOID', 'MAIN', 'PRINTLN'
]

# Token regex definitions
t_PLUS = r'\+'
t_EQUAL = r'='
t_OPEN_PAREN = r'\('
t_CLOSE_PAREN = r'\)'
t_OPEN_BRACE = r'\{'
t_CLOSE_BRACE = r'\}'
t_COMMA = r','
t_SEMICOLON = r';'
t_DOT = r'\.'
t_STRING = r'\"([^\\\n]|(\\.))*?\"'
t_ignore = ' \t\n\r'

# Reserved words
reserved = {
    'public': 'PUBLIC',
    'class': 'CLASS',
    'static': 'STATIC',
    'void': 'VOID',
    'main': 'MAIN',
    'System.out.println': 'PRINTLN'
}

tokens = tokens + list(reserved.values())

def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'ID')
    return t

def t_error(t):
    print(f"Illegal character '{t.value[0]}'")
    t.lexer.skip(1)

lexer = lex.lex()

# Yacc Parsing rules

def p_program(p):
    '''program : PUBLIC CLASS ID OPEN_BRACE main_method CLOSE_BRACE'''
    p[0] = ('program', p[3], p[5])

def p_main_method(p):
    '''main_method : PUBLIC STATIC VOID MAIN OPEN_PAREN STRING CLOSE_BRACE OPEN_BRACE statement_list CLOSE_BRACE CLOSE_PAREN'''
    p[0] = ('main_method', p[9])

def p_statement_list(p):
    '''statement_list : statement
                      | statement_list statement'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

def p_statement(p):
    '''statement : println_statement'''
    p[0] = p[1]

def p_println_statement(p):
    '''println_statement : PRINTLN OPEN_PAREN STRING CLOSE_PAREN SEMICOLON'''
    p[0] = ('println', p[3])

def p_error(p):
    if p:
        print(f"Syntax error at '{p.value}'")
        yacc.errok()

parser = yacc.yacc()

@app.route('/', methods=['GET', 'POST'])
def index():
    counters = {tok: 0 for tok in tokens}
    counters.update({val: 0 for val in reserved.values()})
    token_data = []
    lexical_errors = []
    syntax_errors = []
    syntax_correct = False
    code = ''
    if request.method == 'POST':
        code = request.form.get('code', '')
        lexer.input(code)
        while True:
            tok = lexer.token()
            if not tok:
                break
            entry = {'token': tok.value, 'PR': '', 'ID': '', 'SIM': '', 'ERROR': ''}
            if tok.type in reserved.values():
                entry['PR'] = 'X'
            elif tok.type == 'ID':
                entry['ID'] = 'X'
            elif tok.type == 'ERROR':
                entry['ERROR'] = 'X'
                lexical_errors.append(f"Error Lexico: '{tok.value}'")
            else:
                entry['SIM'] = 'X'
            counters[tok.type] += 1
            token_data.append(entry)
        # Syntax analysis
        try:
            parser.parse(code, lexer=lexer)
            syntax_correct = True
        except Exception as e:
            syntax_errors.append(str(e))

    total_reserved = sum(counters[val] for val in reserved.values())
    total_errors = counters['ERROR'] if 'ERROR' in counters else 0

    return render_template("index.html", token_data=token_data, counters=counters, total_reserved=total_reserved,
                           lexical_errors=lexical_errors, total_errors=total_errors, syntax_errors=syntax_errors,
                           syntax_correct=syntax_correct, code=code)

if __name__ == "__main__":
    app.run(debug=True)
