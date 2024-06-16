import json
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from statistics import mean, median, stdev

app = FastAPI()

# Caminho para o arquivo do "banco de dados"
banco_dados = 'bd.json'

# Classe de modelo de dados
class Aluno(BaseModel):
    id_aluno: int
    nome_aluno: str
    notas: dict[str, float]

# Função para carregar o "banco de dados"
def carregar_bd():
    if os.path.exists(banco_dados):
        with open(banco_dados, 'r') as file:
            return json.load(file)
    return []

# Função para salvar o "banco de dados"
def salvar_bd(bd):
    with open(banco_dados, 'w') as file:
        json.dump(bd, file, indent=4)

@app.post('/adicionar_aluno/')
def adicionar_aluno(aluno: Aluno):
    bd = carregar_bd()

    # Verificar se já existe um aluno com o mesmo ID
    for a in bd:
        if a["id_aluno"] == aluno.id_aluno:
            raise HTTPException(status_code=400, detail="ID de aluno já existente")

    # Validação das notas
    for nota in aluno.notas.values():
        if not 0 <= nota <= 10:
            raise HTTPException(status_code=400, detail="As notas devem estar entre 0 e 10")
    
    # Arredonda as notas para terem no maximo 1 casa decimal
    for materia in aluno.notas.keys():
        aluno.notas[materia] = round(aluno.notas[materia],1)
    
    bd.append(aluno.model_dump())
    salvar_bd(bd)
    return aluno

# Esse get vai verificar todas as matérias e alunos de um determinado aluno pelo ID dele
@app.get('/notas/{id_aluno}')
def notas_aluno(id_aluno: int):
    bd = carregar_bd()
    for aluno in bd:
        if aluno["id_aluno"] == id_aluno:
            return {
                "nome_aluno": aluno["nome_aluno"],
                "notas": aluno["notas"]
            }
    raise HTTPException(status_code=404, detail="Aluno não encontrado")

# Esse get vai verificar todas as notas e alunos de uma determinada matéria pelo nome da matéria
@app.get('/disciplina/{disciplina}')
def notas_disciplina(disciplina: str):
    bd = carregar_bd()
    notas_disciplina = {}
    for aluno in bd:
        if "notas" in aluno and disciplina in aluno["notas"]:
            notas_disciplina[aluno["nome_aluno"]] = aluno["notas"][disciplina]
    
    if notas_disciplina:
        # Ordenar notas em ordem crescente
        notas_ordenadas = dict(sorted(notas_disciplina.items(), key=lambda item: item[1]))
        return notas_ordenadas
    
    raise HTTPException(status_code=404, detail="Disciplina não encontrada")

# Esse get vai verificar estátisticas (moda, média e mediana) de uma determinada matéria pelo nome da matéria
@app.get('/estatisticas/{disciplina}')
def estatisticas_disciplina(disciplina: str):
    bd = carregar_bd()
    notas_disciplina = []
    for aluno in bd:
        if "notas" in aluno and disciplina in aluno["notas"]:
            notas_disciplina.append(aluno["notas"][disciplina])
    if notas_disciplina:
        media = round(mean(notas_disciplina), 1)
        mediana = round(median(notas_disciplina), 1)
        desvio_padrao = round(stdev(notas_disciplina), 1)
        return {
            "media": media,
            "mediana": mediana,
            "desvio_padrao": desvio_padrao
        }
    raise HTTPException(status_code=404, detail="Disciplina não encontrada")

# Esse get vai verificar os alunos que possuem uma nota inferior a 6.0 em uma ou mais matérias
def desempenho_baixo():
    nota_minima = 6.0
    bd = carregar_bd()
    alunos_desempenho_baixo = []
    for aluno in bd:
        desempenho_baixo = False
        if "notas" in aluno:
            for disciplina, nota in aluno["notas"].items():
                if nota < nota_minima:
                    desempenho_baixo = True
                    break
        if desempenho_baixo:
            alunos_desempenho_baixo.append(aluno)
    if alunos_desempenho_baixo:
        return alunos_desempenho_baixo
    raise HTTPException(status_code=404, detail="Nenhum aluno com desempenho abaixo da nota mínima")

# Esse 'get' vai verificar os alunos que não possuem notas, vai deletar esse aluno da lista de alunos
@app.delete('/remover_alunos_sem_notas')
def remover_alunos_sem_notas():
    bd = carregar_bd()
    # Alunos que tem notas
    alunos_com_notas = [aluno for aluno in bd if "notas" in aluno and aluno["notas"]]
    # Alunos que não tem notas
    alunos_sem_notas = [aluno for aluno in bd if "notas" not in aluno or not aluno["notas"]]
    if alunos_sem_notas:
        salvar_bd(alunos_com_notas)
        return {"message": "Alunos sem notas removidos com sucesso"}
    raise HTTPException(status_code=404, detail="Nenhum aluno sem notas encontrado")
