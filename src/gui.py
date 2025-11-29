import tkinter as tk
from tkinter import font
import sys
import io
import os

class ClearScreenSignal(Exception):
    """Sinal para a GUI limpar a tela"""
    pass

class TermIAGUI:
    def __init__(self, parser, lexer, executor):
        self.parser = parser
        self.lexer = lexer
        self.executor = executor
        self.is_ia_mode = False # Para controlar se estamos no "sub-shell" da IA

        # --- Configuração da Janela ---
        self.root = tk.Tk()
        self.root.title("TermIA - Terminal Inteligente")
        self.root.geometry("800x600")
        self.root.configure(bg="black")

        # Configuração de Fonte (Estilo Console)
        self.console_font = font.Font(family="Consolas", size=10) # Consolas, Courier ou Lucida Console

        # --- Área de Saída (Onde aparece o texto) ---
        self.output_area = tk.Text(
            self.root, 
            bg="black", 
            fg="white", 
            insertbackground="white",
            font=self.console_font,
            state="disabled", # Começa bloqueado para edição
            wrap="word"
        )
        self.output_area.pack(expand=True, fill="both", padx=5, pady=5)
        
        # Tag para colorir coisas diferentes (opcional)
        self.output_area.tag_config("prompt", foreground="#00ff00") # Verde hacker
        self.output_area.tag_config("error", foreground="red")
        self.output_area.tag_config("ia", foreground="cyan")

        # --- Área de Entrada (Onde você digita) ---
        self.input_entry = tk.Entry(
            self.root, 
            bg="#1e1e1e", # Um cinza bem escuro para diferenciar levemente
            fg="white", 
            insertbackground="white",
            font=self.console_font,
            bd=0 # Sem borda
        )
        self.input_entry.pack(fill="x", padx=5, pady=5)
        self.input_entry.bind("<Return>", self.process_input) # Liga o ENTER à função
        self.input_entry.focus_set() # Já começa focado para digitar

        # --- Mensagem Inicial ---
        self.write_to_console("Bem-vindo ao TermIA [Versão 1.0]\n", "prompt")
        self.write_to_console("Copyright (c) 2025 Universidade Federal de Itajubá.\n\n")
        self.update_prompt()
        
        #Controle de Histórico para navegação ---
        self.command_history = [] # Guarda as strings digitadas
        self.history_index = 0    # Ponteiro de onde estamos na lista
        
        # Bind das Teclas de Seta ---
        self.input_entry.bind("<Up>", self.navigate_history_up)
        self.input_entry.bind("<Down>", self.navigate_history_down)

    def start(self):
        """Inicia o loop da interface gráfica"""
        self.root.mainloop()

    def write_to_console(self, text, tag=None):
        """Escreve texto na área de saída e rola para baixo"""
        self.output_area.configure(state="normal") # Destrava
        self.output_area.insert("end", text, tag)
        self.output_area.see("end") # Rola para o final
        self.output_area.configure(state="disabled") # Trava de novo

    def update_prompt(self):
        """Mostra o prompt atual"""
        if self.is_ia_mode:
            self.write_to_console("TermIA-GPT> ", "ia")
        else:
            path = os.getcwd()
            self.write_to_console(f"TermIA {path}> ", "prompt")

    def process_input(self, event):
        """Ocorre quando aperta ENTER"""
        command_text = self.input_entry.get() # Pega o texto
        self.input_entry.delete(0, "end")     # Limpa o input

        # Escreve o comando que o usuário digitou na tela (para ficar no histórico)
        self.write_to_console(command_text + "\n")

        # Se estiver vazio, só mostra o prompt de novo
        if not command_text.strip():
            self.update_prompt()
            return

        # Salva no histórico de navegação (visual) ---
        if command_text.strip():
            self.command_history.append(command_text)
            self.history_index = len(self.command_history) # Reseta ponteiro pro final
            
        # --- Lógica de Captura do Print ---
        # Aqui fazemos a mágica: Desviamos o sys.stdout para uma variável
        # Assim, tudo que seu Executor der 'print', nós pegamos.
        
        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()

        try:
            # 1. TRATAMENTO DO MODO IA (Estado)
            if self.is_ia_mode:
                if command_text.strip().lower() in ['sair', 'exit', 'voltar']:
                    self.is_ia_mode = False
                    print("Saindo do modo IA...")
                else:
                    # Chama direto a API
                    resp = self.executor.chamar_api_ia(command_text)
                    print(f"🤖 IA: {resp}")
            
            # 2. TRATAMENTO NORMAL (Parser -> Executor)
            else:
                # Pequeno ajuste manual para detectar entrada no modo IA
                # (já que o parser funciona melhor com comandos completos)
                if command_text.strip().lower() == 'ia_mode':
                    self.is_ia_mode = True
                    print("="*40)
                    print("🤖 MODO IA ATIVADO (GUI)")
                    print("Digite 'sair' para voltar.")
                    print("="*40)
                    print("Faça perguntas livremente e receba respostas em tempo real.")
                    print("="*40)
                else:
                    # Adiciona \n para o lexer funcionar (fix do newline)
                    line_to_parse = command_text
                    if not line_to_parse.endswith("\n"):
                        line_to_parse += "\n"
                    
                    ast_node = self.parser.parse(line_to_parse, lexer=self.lexer)
                    try:
                        self.executor.execute(ast_node)
                    except ClearScreenSignal:
                    # --- A MÁGICA DO CLEAR ACONTECE AQUI ---
                        self.output_area.configure(state="normal")
                        self.output_area.delete("1.0", "end") # Apaga tudo
                        self.output_area.configure(state="disabled")
                    

        except Exception as e:
            print(f"Erro Crítico: {e}")
        
        finally:
            # Recupera o que foi impresso
            sys.stdout = old_stdout # Devolve o controle para o terminal real
            output_content = buffer.getvalue()
            
            # Escreve na tela preta
            self.write_to_console(output_content)
            
            # Prepara para o próximo comando
            self.update_prompt()
            
    def navigate_history_up(self, event):
        """Volta no histórico (Seta Cima)"""
        if not self.command_history: return
        
        # Decrementa o índice (sem passar de 0)
        self.history_index = max(0, self.history_index - 1)
        
        # Atualiza o input
        self.input_entry.delete(0, "end")
        self.input_entry.insert(0, self.command_history[self.history_index])

    def navigate_history_down(self, event):
        """Avança no histórico (Seta Baixo)"""
        if not self.command_history: return
        
        # Incrementa o índice
        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.input_entry.delete(0, "end")
            self.input_entry.insert(0, self.command_history[self.history_index])
        else:
            # Se passar do último, limpa a linha (volta pro comando novo)
            self.history_index = len(self.command_history)
            self.input_entry.delete(0, "end")