#Davi Pereira Bossi - 2024014355

from dotenv import load_dotenv
from executor import Executor
from grammar import parser
from lexer import lexer
from gui import TermIAGUI

if __name__ == "__main__":
    # Carrega variáveis de ambiente (segurança)
    load_dotenv() 

    # Instancia o Executor
    executor_instance = Executor()
    
    # Inicia a Interface Gráfica em vez do repl()
    app = TermIAGUI(parser, lexer, executor_instance)
    app.start()
