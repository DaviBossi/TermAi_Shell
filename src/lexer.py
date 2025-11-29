import ply.lex as lex   

reserved = {
    'help': 'HELP',
    'exit': 'EXIT',
    'echo': 'ECHO',
    'history': 'HISTORY',
    'pwd': 'PWD',
    'ls': 'LS',
    'show': 'SHOW',
    'cd': 'CD',
    'mkdir': 'MKDIR',
    'rmdir' : 'RMDIR',
    'rm' : 'RM',
    'touch': 'TOUCH',
    'ia_mode': 'IA',
    'cls': 'CLEAR',
    'history' : 'HISTORY'
}

tokens = [
    'STRING',   # "texto com espaços"
    'FLAG',     # -a, -la, --all, etc.
    'ID',       # palavras/paths
    'NEWLINE',
] + list(reserved.values())

t_ignore = ' \t'

def t_STRING(t):
    r'"[^"\n\r]*"'
    t.value = t.value[1:-1]  # remove aspas
    return t

def t_FLAG(t):
    r'--[a-zA-Z0-9_-]+|-{1}[a-zA-Z]+'
    return t

def t_ID(t):
    r'[A-Za-z0-9._/\-]+'
    t.type = reserved.get(t.value, 'ID')
    return t

def t_NEWLINE(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    return t

def t_error(t):
    print(f"[LEXER] Caractere inválido: {t.value[0]!r}")
    t.lexer.skip(1)

lexer = lex.lex()