import sqlite3
import os
from datetime import datetime, timedelta

class StudyDB:
    def __init__(self, db_path="data/studyup.db"):
        self.db_path = db_path
        self._criar_diretorio()
        self.init_db()

    def _criar_diretorio(self):
        """Cria a pasta data se não existir."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def _conectar(self):
        """Método interno para abrir conexão (Context Manager)."""
        return sqlite3.connect(self.db_path)

    def init_db(self):
        """Cria todas as tabelas necessárias para o StudyUp."""
        with self._conectar() as conn:
            cursor = conn.cursor()
            
            # 1. Tabela Disciplinas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS disciplinas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    nome TEXT NOT NULL UNIQUE
                )
            ''')

            # 2. Tabela Tópicos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS topicos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    disciplina_id INTEGER, 
                    nome TEXT NOT NULL, 
                    concluido BOOLEAN DEFAULT 0,
                    FOREIGN KEY (disciplina_id) REFERENCES disciplinas (id)
                )
            ''')

            # 3. Tabela Sessões
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    topico_id INTEGER, 
                    questoes_total INTEGER, 
                    questoes_acerto INTEGER, 
                    percentual REAL,
                    proxima_revisao DATE,
                    data_sessao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (topico_id) REFERENCES topicos (id)
                )
            ''')

            # 4. Tabela Flashcards
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS flashcards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topico_id INTEGER,
                    pergunta TEXT NOT NULL,
                    resposta TEXT NOT NULL,
                    FOREIGN KEY (topico_id) REFERENCES topicos (id)
                )
            ''')
            conn.commit()

    # --- MÉTODOS DE DISCIPLINAS ---
    def adicionar_disciplina(self, nome):
        try:
            with self._conectar() as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO disciplinas (nome) VALUES (?)', (nome,))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False

    def listar_disciplinas(self):
        with self._conectar() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM disciplinas')
            return cursor.fetchall()

    # --- MÉTODOS DE TÓPICOS ---
    def adicionar_topico(self, disciplina_id, nome_topico):
        with self._conectar() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO topicos (disciplina_id, nome) VALUES (?, ?)', (disciplina_id, nome_topico))
            conn.commit()

    def listar_topicos_por_disciplina(self, disciplina_id):
        with self._conectar() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM topicos WHERE disciplina_id = ?', (disciplina_id,))
            return cursor.fetchall()

    # --- MÉTODOS DE DESEMPENHO ---
    def registrar_desempenho(self, topico_id, questoes, acertos):
        percentual = (acertos / questoes) * 100 if questoes > 0 else 0
        dias_revisao = 7 if percentual >= 75 else 1
        data_revisao = (datetime.now() + timedelta(days=dias_revisao)).date()
        
        with self._conectar() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sessoes (topico_id, questoes_total, questoes_acerto, percentual, proxima_revisao) 
                VALUES (?, ?, ?, ?, ?)
            ''', (topico_id, questoes, acertos, percentual, data_revisao))
            conn.commit()

    # --- MÉTODOS DE FLASHCARDS ---
    def adicionar_flashcard(self, topico_id, pergunta, resposta):
        with self._conectar() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO flashcards (topico_id, pergunta, resposta) VALUES (?, ?, ?)', 
                           (topico_id, pergunta, resposta))
            conn.commit()

    def listar_flashcards_por_topico(self, topico_id):
        with self._conectar() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM flashcards WHERE topico_id = ?', (topico_id,))
            return cursor.fetchall()