import threading
import time
import tkinter as tk
from tkinter import ttk
import random
from datetime import datetime
from queue import Queue

class RecursoCompartilhavel:
    def __init__(self, item_id):
        self.item_id = item_id
        self.lock = "unlock"  # Pode ser "read_lock", "write_lock" ou "unlock"
        self.operation = None  # Pode ser "ler" ou "escrever"
        self.thread_acessando = None
        self.timestamp_thread = None
        self.fila = Queue()
        self.label = None  # Será configurado pela aplicação
    
    def acessar(self, thread, operation):
        # Se o recurso está desbloqueado, permite o acesso imediatamente
        if self.lock == "unlock":
            self.thread_acessando = thread
            self.timestamp_thread = thread.prioridade
            self.operation = operation
            self.lock = "read_lock" if operation == "ler" else "write_lock"
            # Atualiza o label
            if self.label:
                self.label.config(text=f"Recurso {self.item_id}: {self.lock} (Thread {thread.nome})")
            return True
        
        # Se já existe uma thread acessando, adiciona na fila
        self.fila.put({
            'thread': thread,
            'operation': operation,
            'timestamp': thread.prioridade
        })
        return False
    
    def liberar(self):
        # Primeiro reseta os valores padrão
        self.thread_acessando = None
        self.timestamp_thread = None
        self.operation = None
        self.lock = "unlock"
        
        # Atualiza o label
        if self.label:
            self.label.config(text=f"Recurso {self.item_id}: Desbloqueado")
        
        # Verifica se tem thread na fila
        if not self.fila.empty():
            # Pega a próxima thread da fila
            proxima_thread = self.fila.get()
            # Chama acessar com os parâmetros da próxima thread
            self.acessar(proxima_thread['thread'], proxima_thread['operation'])

class MinhaThread(threading.Thread):
    def __init__(self, nome, prioridade=None, label_status=None, progress_bar=None, recursos=None):
        super().__init__()
        self.nome = nome
        self.prioridade = prioridade if prioridade is not None else time.time()
        self.resultado = None
        self.esta_ativa = False
        self.label_status = label_status
        self.progress_bar = progress_bar
        self.tempo_total = self.prioridade
        self.recursos = recursos or []
        self.recursos_acesso = []
        self.tempos_acesso = {}
        self.tempo_pausa = 0
        self.recursos_desejados = []
        self.estado = "executando"
        self.ultima_tentativa_acesso = 0
        self.intervalo_min_acesso = 1  # Reduzido para 1 segundo
        self.intervalo_max_acesso = 3  # Reduzido para 3 segundos
        self.proximo_intervalo_acesso = random.uniform(self.intervalo_min_acesso, self.intervalo_max_acesso)
        self.primeira_tentativa = True  # Nova flag para primeira tentativa
        # Tempos de acesso aos recursos
        self.tempo_min_acesso = 15  # Tempo mínimo de acesso a um recurso
        self.tempo_max_acesso = 30  # Tempo máximo de acesso a um recurso
        # Ordem fixa de recursos para aumentar chance de deadlock
        self.ordem_recursos = ['X', 'Y']
    
    def atualizar_cor_barra(self):
        """Atualiza a cor da barra de progresso baseado no estado"""
        if self.progress_bar:
            if self.estado == "aguardando_recursos":
                self.progress_bar["style"] = "Yellow.Horizontal.TProgressbar"
            else:
                self.progress_bar["style"] = "Horizontal.TProgressbar"
    
    def reset_recursos_acesso(self):
        """Reseta todos os recursos que esta thread está acessando"""
        for recurso in self.recursos_acesso:
            recurso.liberar()
        self.recursos_acesso.clear()
        self.tempos_acesso.clear()
        self.recursos_desejados.clear()
        self.estado = "executando"
        self.atualizar_cor_barra()
        self.proximo_intervalo_acesso = random.uniform(self.intervalo_min_acesso, self.intervalo_max_acesso)
    
    def verificar_tempo_acesso(self):
        """Verifica se algum recurso precisa ser liberado por tempo"""
        recursos_para_liberar = []
        tempo_atual = time.time()
        
        for recurso in self.recursos_acesso:
            tempo_inicio = self.tempos_acesso[recurso]['inicio']
            tempo_duracao = self.tempos_acesso[recurso]['duracao']
            
            if (tempo_atual - tempo_inicio) >= tempo_duracao:
                recursos_para_liberar.append(recurso)
        
        for recurso in recursos_para_liberar:
            recurso.liberar()
            self.recursos_acesso.remove(recurso)
            del self.tempos_acesso[recurso]
            status = f"Thread {self.nome} liberou recurso {recurso.item_id}"
            if self.label_status:
                self.label_status.config(text=status)
        
        # Se liberou todos os recursos, volta ao estado de execução
        if not self.recursos_acesso:
            self.estado = "executando"
            self.atualizar_cor_barra()
            self.proximo_intervalo_acesso = random.uniform(self.intervalo_min_acesso, self.intervalo_max_acesso)
    
    def tentar_acessar_recursos(self):
        """Tenta acessar todos os recursos desejados"""
        if not self.recursos_desejados or self.primeira_tentativa:
            # Sempre tenta acessar os primeiros 2 recursos na ordem fixa
            recursos_disponiveis = [r for r in self.recursos if r.lock == "unlock" and r not in self.recursos_acesso]
            if len(recursos_disponiveis) >= 2:
                # Pega os dois primeiros recursos disponíveis na ordem fixa
                recursos_ordenados = sorted(recursos_disponiveis, key=lambda x: self.ordem_recursos.index(x.item_id))
                self.recursos_desejados = recursos_ordenados[:2]
                self.primeira_tentativa = False
        
        # Tenta acessar cada recurso na ordem
        recursos_acessados = False
        recursos_ainda_desejados = []
        
        for recurso in self.recursos_desejados[:]:
            if recurso.lock == "unlock":
                if recurso.acessar(self, "ler"):
                    self.recursos_acesso.append(recurso)
                    # Gera um tempo aleatório entre tempo_min_acesso e tempo_max_acesso
                    duracao = random.uniform(self.tempo_min_acesso, self.tempo_max_acesso)
                    self.tempos_acesso[recurso] = {
                        'inicio': time.time(),
                        'duracao': duracao
                    }
                    recursos_acessados = True
                    status = f"Thread {self.nome} acessou recurso {recurso.item_id} por {duracao:.1f}s"
                    if self.label_status:
                        self.label_status.config(text=status)
                else:
                    recursos_ainda_desejados.append(recurso)
            else:
                recursos_ainda_desejados.append(recurso)
        
        # Atualiza a lista de recursos desejados
        self.recursos_desejados = recursos_ainda_desejados
        
        # Atualiza o estado baseado nos recursos
        if self.recursos_acesso:
            self.estado = "acessando_recursos"
            self.atualizar_cor_barra()
        
        if self.recursos_desejados:
            self.estado = "aguardando_recursos"
            self.atualizar_cor_barra()
        elif not self.recursos_acesso:
            self.estado = "executando"
            self.atualizar_cor_barra()
        
        return recursos_acessados
    
    def deve_tentar_acesso(self):
        """Verifica se deve tentar acessar recursos baseado no tempo"""
        tempo_atual = time.time()
        if (tempo_atual - self.ultima_tentativa_acesso) >= self.proximo_intervalo_acesso:
            self.ultima_tentativa_acesso = tempo_atual
            self.proximo_intervalo_acesso = random.uniform(self.intervalo_min_acesso, self.intervalo_max_acesso)
            return True
        return False
    
    def run(self):
        self.esta_ativa = True
        tempo_inicio = time.time()
        ultimo_tempo = tempo_inicio
        self.ultima_tentativa_acesso = tempo_inicio
        
        try:
            # Tenta acessar recursos logo no início
            self.tentar_acessar_recursos()
            
            while self.esta_ativa:
                tempo_atual = time.time()
                
                if self.estado == "executando":
                    tempo_decorrido = (tempo_atual - tempo_inicio) - self.tempo_pausa
                    progresso = (tempo_decorrido / self.tempo_total) * 100
                    
                    status = f"Thread {self.nome} (Tempo: {self.tempo_total:.1f}s): {progresso:.1f}%"
                    if self.label_status:
                        self.label_status.config(text=status)
                    if self.progress_bar:
                        self.progress_bar["value"] = progresso
                    
                    if tempo_decorrido >= self.tempo_total:
                        break
                    
                    if self.deve_tentar_acesso():
                        self.tentar_acessar_recursos()
                
                elif self.estado == "aguardando_recursos":
                    recursos_aguardando = [r.item_id for r in self.recursos_desejados]
                    recursos_acessando = [r.item_id for r in self.recursos_acesso]
                    status = f"Thread {self.nome}:\nAguardando: {', '.join(recursos_aguardando)}\nAcessando: {', '.join(recursos_acessando) if recursos_acessando else 'Nenhum'}"
                    if self.label_status:
                        self.label_status.config(text=status)
                    # Tenta acessar os recursos disponíveis
                    self.tentar_acessar_recursos()
                
                elif self.estado == "acessando_recursos":
                    self.tempo_pausa += (tempo_atual - ultimo_tempo)
                    recursos_acessando = [r.item_id for r in self.recursos_acesso]
                    recursos_aguardando = [r.item_id for r in self.recursos_desejados]
                    status = f"Thread {self.nome}:\nAcessando: {', '.join(recursos_acessando)}\nAguardando: {', '.join(recursos_aguardando) if recursos_aguardando else 'Nenhum'}"
                    if self.label_status:
                        self.label_status.config(text=status)
                
                self.verificar_tempo_acesso()
                ultimo_tempo = tempo_atual
                time.sleep(0.1)
        finally:
            self.reset_recursos_acesso()
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
        self.root.title("Simulador de Threads com Recursos")
        self.root.geometry("600x600")  # Reduzindo a altura da janela
        
        # Configura o estilo para a barra de progresso amarela
        style = ttk.Style()
        style.configure("Yellow.Horizontal.TProgressbar", 
                       troughcolor='white',
                       background='yellow',
                       thickness=20)
        
        # Frame principal
        self.frame = ttk.Frame(root, padding="10")
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame de configuração
        self.frame_config = ttk.LabelFrame(self.frame, text="Configuração", padding="5")
        self.frame_config.pack(fill=tk.X, pady=5)
        
        # Configuração de tempo das threads
        self.frame_tempo = ttk.Frame(self.frame_config)
        self.frame_tempo.pack(fill=tk.X, pady=5)
        
        # Tempo mínimo das threads
        ttk.Label(self.frame_tempo, text="Tempo mínimo (s):").pack(side=tk.LEFT, padx=5)
        self.tempo_min = ttk.Entry(self.frame_tempo, width=5)
        self.tempo_min.insert(0, "15")
        self.tempo_min.pack(side=tk.LEFT, padx=5)
        
        # Tempo máximo das threads
        ttk.Label(self.frame_tempo, text="Tempo máximo (s):").pack(side=tk.LEFT, padx=5)
        self.tempo_max = ttk.Entry(self.frame_tempo, width=5)
        self.tempo_max.insert(0, "30")
        self.tempo_max.pack(side=tk.LEFT, padx=5)
        
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
        
        # Cria recursos
        self.recursos = {}
        for letra in ['X', 'Y']:
            self.recursos[letra] = RecursoCompartilhavel(letra)
    
    def reset_recursos(self):
        """Reinicia todos os recursos para o estado inicial"""
        for recurso in self.recursos.values():
            # Limpa a fila de espera
            while not recurso.fila.empty():
                recurso.fila.get()
            
            # Reseta os atributos do recurso
            recurso.lock = "unlock"
            recurso.operation = None
            recurso.thread_acessando = None
            recurso.timestamp_thread = None
    
    def gerar_tempo_aleatorio(self):
        try:
            tempo_min = float(self.tempo_min.get())
            tempo_max = float(self.tempo_max.get())
            if tempo_min > tempo_max:
                tempo_min, tempo_max = tempo_max, tempo_min
            return random.uniform(tempo_min, tempo_max)
        except ValueError:
            # Se houver erro na conversão, usa valores padrão
            return random.uniform(10, 30)
    
    def gerar_threads_aleatorias(self):
        # Limpa threads existentes
        self.limpar_threads()
        
        # Reinicia os recursos
        self.reset_recursos()
        
        # Gera número aleatório de threads (entre 2 e 3)
        num_threads = random.randint(2, 3)
        
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
                mode="determinate",
                style="Horizontal.TProgressbar"
            )
            progress.pack(pady=5)
            
            # Cria thread com tempo aleatório
            thread = MinhaThread(
                str(i+1),
                prioridade=tempo,
                label_status=label,
                progress_bar=progress,
                recursos=list(self.recursos.values())
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
        resultado = "Status das Threads:\n"
        for i, thread in enumerate(self.threads):
            resultado += f"Thread {i+1}: {'Ativa' if thread.esta_ativa else 'Inativa'} (Tempo: {thread.tempo_total:.1f}s)\n"
            if thread.recursos_acesso:
                resultado += f"  Recursos acessados: {[r.item_id for r in thread.recursos_acesso]}\n"
            if thread.recursos_desejados:
                resultado += f"  Recursos aguardados: {[r.item_id for r in thread.recursos_desejados]}\n"
        
        resultado += "\nStatus dos Recursos:\n"
        for letra, recurso in self.recursos.items():
            resultado += f"Recurso {letra}: {recurso.lock}"
            if recurso.thread_acessando:
                resultado += f" (Thread {recurso.thread_acessando.nome})"
            resultado += "\n"
        
        self.label_resultado.config(text=resultado)

# Criar e iniciar a aplicação
janela = tk.Tk()
app = Aplicacao(janela)
janela.mainloop()