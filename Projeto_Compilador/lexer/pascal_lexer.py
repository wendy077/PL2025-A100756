# lexer/pascal_lexer.py
import ply.lex as lex

# ---------------------------------------------
# Palavras reservadas Pascal
# ---------------------------------------------
reserved = {
    'program': 'PROGRAM',
    'var': 'VAR',
    'const': 'CONST',
    'begin': 'BEGIN',
    'end': 'END',
    'integer': 'INTEGER',
    'real': 'REAL',
    'boolean': 'BOOLEAN',
    'true': 'TRUE',
    'false': 'FALSE',
    'procedure': 'PROCEDURE',
    'function': 'FUNCTION',
    'if': 'IF',
    'then': 'THEN',
    'else': 'ELSE',
    'while': 'WHILE',
    'do': 'DO',
    'for': 'FOR',
    'to': 'TO',
    'downto': 'DOWNTO',
    'writeln': 'WRITELN',
    'readln': 'READLN',
    'array': 'ARRAY',
    'string': 'STRING',
    'of': 'OF', 
    'not': 'NOT',
    'and': 'AND',
    'or': 'OR',
    'div': 'DIV',
    'mod': 'MOD'
}

# ---------------------------------------------
# Lista completa de tokens (inclui operadores)
# ---------------------------------------------
tokens = [
    'ID', 'NUMBER', 'STRLIT', 

    # Operadores
    'PLUS', 'MINUS', 'MULT', 'DIVIDE', 'ASSIGN',
    'EQUAL', 'NEQ', 'LT', 'LE', 'GT', 'GE',

    # Delimitadores e símbolos especiais
    'LPAREN', 'RPAREN',
    'LBRACK', 'RBRACK',
    'SEMI', 'COLON', 'COMMA', 'DOTDOT', 'DOT'
] + list(reserved.values())


# ---------------------------------------------
# Expressões regulares para tokens simples
# ---------------------------------------------
t_PLUS     = r'\+'
t_MINUS    = r'-'
t_MULT     = r'\*'
t_DIVIDE   = r'/'
t_ASSIGN   = r':='
t_EQUAL    = r'='
t_NEQ      = r'<>'
t_LT       = r'<'
t_LE       = r'<='
t_GT       = r'>'
t_GE       = r'>='

t_LPAREN   = r'\('
t_RPAREN   = r'\)'
t_LBRACK   = r'\['
t_RBRACK   = r'\]'
t_SEMI     = r';'
t_COLON    = r':'
t_COMMA    = r','
t_DOTDOT   = r'\.\.'
t_DOT      = r'\.'

# ---------------------------------------------
# Ignorar espaços e tabulações
# ---------------------------------------------
t_ignore = ' \t'

# ---------------------------------------------
# Literais de string (entre aspas simples)
# ---------------------------------------------
def t_STRLIT(t):
    r'\'([^\\\n]|(\\.))*?\''
    t.value = t.value[1:-1]
    return t

# ---------------------------------------------
# Números inteiros e reais
# ---------------------------------------------
def t_NUMBER(t):
    r'\d+(\.\d+)?'
    if '.' in t.value:
        t.value = float(t.value)
    else:
        t.value = int(t.value)
    return t

# ---------------------------------------------
# Identificadores e palavras reservadas
# ---------------------------------------------
def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value.lower(), 'ID')
    return t

# ---------------------------------------------
# Contador de linhas (útil para erros)
# ---------------------------------------------
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# ---------------------------------------------
# Comentários no estilo { ... }
# ---------------------------------------------
def t_COMMENT(t):
    r'\{[^}]*\}'
    pass  # ignora

# ---------------------------------------------
# Tratamento de erros léxicos
# ---------------------------------------------
def t_error(t):
    print(f'Carácter ilegal: {t.value[0]!r} na linha {t.lineno}')
    t.lexer.skip(1)

# ---------------------------------------------
# Construção do analisador léxico
# ---------------------------------------------
lexer = lex.lex()