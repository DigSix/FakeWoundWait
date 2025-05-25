import threading
import time
import tkinter as tk
from tkinter import ttk
import random
from datetime import datetime

class MinhaThread(threading.Thread):
    def __init__(self, nome, prioridade=None, label_status=None, progress_bar=None):
        super().__init__()
        self.nome = nome
        # Se não for fornecido timestamp, usa o atual
        self.prioridade = prioridade if prioridade is not None else time.time()
        self.resultado = None
        self.esta_ativa = False
        self.label_status = label_status
        self.progress_bar = progress_bar
        # Tempo total de execução em segundos
        self.tempo_total = self.prioridade
    
    def run(self):
        self.esta_ativa = True
        tempo_inicio = time.time()
        
        while self.esta_ativa:
            # Calcula o tempo decorrido
            tempo_decorrido = time.time() - tempo_inicio
            # Calcula o progresso baseado no tempo
            progresso = (tempo_decorrido / self.tempo_total) * 100
            
            # Formata o timestamp para exibição em segundos
            status = f"Thread {self.nome} (Tempo: {self.tempo_total:.1f}s): {progresso:.1f}%"
            
            if self.label_status:
                self.label_status.config(text=status)
            if self.progress_bar:
                self.progress_bar["value"] = progresso
            
            # Se atingiu o tempo total, finaliza
            if tempo_decorrido >= self.tempo_total:
                break
                
            time.sleep(0.1)  # Intervalo para atualizar a interface
        
        # Garante que chegue a 100% no final
        if self.label_status:
            self.label_status.config(text=f"Thread {self.nome}: 100%")
        if self.progress_bar:
            self.progress_bar["value"] = 100
        
        self.esta_ativa = False
        self.resultado = f"Thread {self.nome} finalizou com sucesso!"
        if self.label_status:
            self.label_status.config(text=self.resultado)

class Aplicacao:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador de Threads Aleatórias")
        self.root.geometry("500x600")
        
        # Frame principal
        self.frame = ttk.Frame(root, padding="10")
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame de configuração
        self.frame_config = ttk.LabelFrame(self.frame, text="Configuração", padding="5")
        self.frame_config.pack(fill=tk.X, pady=5)
        
        # Botão para gerar threads aleatórias
        self.btn_gerar = ttk.Button(
            self.frame_config,
            text="Gerar Threads Aleatórias",
            command=self.gerar_threads_aleatorias
        )
        self.btn_gerar.pack(pady=5)
        
        # Frame para threads
        self.frame_threads = ttk.Frame(self.frame)
        self.frame_threads.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Botões
        self.frame_botoes = ttk.Frame(self.frame)
        self.frame_botoes.pack(pady=10)
        
        self.btn_iniciar = ttk.Button(
            self.frame_botoes,
            text="Iniciar Threads",
            command=self.iniciar_threads,
            state='disabled'
        )
        self.btn_iniciar.pack(side=tk.LEFT, padx=5)
        
        self.btn_status = ttk.Button(
            self.frame_botoes,
            text="Verificar Status",
            command=self.verificar_status,
            state='disabled'
        )
        self.btn_status.pack(side=tk.LEFT, padx=5)
        
        # Label para resultado do status
        self.label_resultado = ttk.Label(self.frame, text="")
        self.label_resultado.pack(pady=10)
        
        # Lista para armazenar as threads e seus componentes
        self.threads = []
        self.thread_frames = []
        self.thread_labels = []
        self.thread_progress = []
    
    def gerar_tempo_aleatorio(self):
        # Gera um tempo aleatório entre 10 e 60 segundos
        return random.randint(10, 60)
    
    def gerar_threads_aleatorias(self):
        # Limpa threads existentes
        self.limpar_threads()
        
        # Gera número aleatório de threads (entre 1 e 5)
        num_threads = random.randint(1, 5)
        
        # Cria novas threads
        for i in range(num_threads):
            # Gera tempo aleatório
            tempo = self.gerar_tempo_aleatorio()
            
            # Cria frame para a thread
            frame = ttk.LabelFrame(self.frame_threads, text=f"Thread {i+1}", padding="5")
            frame.pack(fill=tk.X, pady=5)
            
            # Cria label para status
            label = ttk.Label(frame, text=f"Thread {i+1}: Aguardando...")
            label.pack(pady=5)
            
            # Cria barra de progresso
            progress = ttk.Progressbar(
                frame,
                orient="horizontal",
                length=300,
                mode="determinate"
            )
            progress.pack(pady=5)
            
            # Cria thread com tempo aleatório
            thread = MinhaThread(
                str(i+1),
                prioridade=tempo,
                label_status=label,
                progress_bar=progress
            )
            
            # Armazena os componentes
            self.thread_frames.append(frame)
            self.thread_labels.append(label)
            self.thread_progress.append(progress)
            self.threads.append(thread)
        
        # Habilita botões
        self.btn_iniciar.config(state='normal')
        self.btn_status.config(state='normal')
        
        # Mostra informações sobre as threads geradas
        info = f"Geradas {num_threads} threads:\n"
        for i, thread in enumerate(self.threads):
            info += f"Thread {i+1}: tempo = {thread.tempo_total:.1f}s\n"
        self.label_resultado.config(text=info)
    
    def limpar_threads(self):
        # Para todas as threads em execução
        for thread in self.threads:
            if thread.is_alive():
                thread.esta_ativa = False
                # Dá um pequeno tempo para a thread encerrar
                thread.join(timeout=0.01)
        
        # Remove todos os frames
        for frame in self.thread_frames:
            frame.destroy()
        
        # Limpa as listas
        self.threads.clear()
        self.thread_frames.clear()
        self.thread_labels.clear()
        self.thread_progress.clear()
        
        # Pequeno delay para garantir que tudo foi limpo
        self.root.update()
        time.sleep(0.01)
    
    def iniciar_threads(self):
        # Reseta as barras de progresso
        for progress in self.thread_progress:
            progress["value"] = 0
        
        # Inicia todas as threads
        for thread in self.threads:
            thread.start()
        
        self.btn_iniciar.config(state='disabled')
    
    def verificar_status(self):
        resultado = ""
        for i, thread in enumerate(self.threads):
            resultado += f"Thread {i+1}: {'Ativa' if thread.esta_ativa else 'Inativa'} (Tempo: {thread.tempo_total:.1f}s)\n"
        
        self.label_resultado.config(text=resultado)

# Criar e iniciar a aplicação
janela = tk.Tk()
app = Aplicacao(janela)
janela.mainloop()