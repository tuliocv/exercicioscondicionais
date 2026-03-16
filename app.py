import os
import csv
import random
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st


# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Jogo: Estruturas Condicionais (Java)",
    page_icon="🧠",
    layout="centered"
)

st.title("🧠 Jogo: Estruturas Condicionais em Java")
st.caption("Pratique if, if/else, else if e switch")


# =========================
# ADMIN CREDENTIALS
# =========================
def get_admin_credentials():
    try:
        user = st.secrets["admin"]["user"]
        pwd = st.secrets["admin"]["pass"]
        return user, pwd
    except Exception:
        return os.getenv("ADMIN_USER", "admin"), os.getenv("ADMIN_PASS", "admin")


ADMIN_USER, ADMIN_PASS = get_admin_credentials()


# =========================
# STORAGE (CSV)
# =========================
DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

SCORES_FILE = DATA_DIR / "condicionais_scores.csv"
ANSWERS_FILE = DATA_DIR / "condicionais_answers.csv"

SCORES_HEADERS = [
    "timestamp_utc",
    "student_name",
    "base_correct",
    "final_points",
    "total",
    "percent_official",
    "max_streak"
]

ANS_HEADERS = [
    "timestamp_utc",
    "student_name",
    "question_id",
    "level",
    "is_correct"
]


def ensure_file(path: Path, headers: list[str]):
    if not path.exists():
        with open(path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(headers)


def ensure_scores_file():
    ensure_file(SCORES_FILE, SCORES_HEADERS)


def ensure_answers_file():
    ensure_file(ANSWERS_FILE, ANS_HEADERS)


def clear_data_caches():
    load_scores.clear()
    load_answers.clear()


@st.cache_data(ttl=2)
def load_scores():
    ensure_scores_file()
    rows = []
    with open(SCORES_FILE, "r", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                row["base_correct"] = int(row.get("base_correct", 0))
                row["final_points"] = int(row.get("final_points", 0))
                row["total"] = int(row.get("total", 0))
                row["percent_official"] = float(row.get("percent_official", 0.0))
                row["max_streak"] = int(row.get("max_streak", 0))
                rows.append(row)
            except Exception:
                pass
    return rows


@st.cache_data(ttl=2)
def load_answers():
    ensure_answers_file()
    rows = []
    with open(ANSWERS_FILE, "r", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                row["is_correct"] = int(row.get("is_correct", 0))
                rows.append(row)
            except Exception:
                pass
    return rows


def append_score(student_name: str, base_correct: int, final_points: int, total: int, max_streak: int):
    ensure_scores_file()
    percent_official = (base_correct / total) * 100 if total else 0.0
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    with open(SCORES_FILE, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            ts,
            student_name,
            base_correct,
            final_points,
            total,
            f"{percent_official:.2f}",
            max_streak
        ])

    clear_data_caches()


def append_answer(student_name: str, question_id: str, level: str, is_correct: bool):
    ensure_answers_file()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    with open(ANSWERS_FILE, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            ts,
            student_name,
            question_id,
            level,
            int(is_correct)
        ])

    clear_data_caches()


def clear_all_data():
    for p, h in [
        (SCORES_FILE, SCORES_HEADERS),
        (ANSWERS_FILE, ANS_HEADERS),
    ]:
        if p.exists():
            p.unlink()
        ensure_file(p, h)

    clear_data_caches()


# =========================
# UI HELPERS
# =========================
def difficulty_bar(level: str):
    mapping = {
        "Fácil": 25,
        "Médio": 55,
        "Difícil": 80,
        "Ultra Difícil": 100
    }
    colors = {
        "Fácil": "🟩",
        "Médio": "🟨",
        "Difícil": "🟥",
        "Ultra Difícil": "🟪"
    }
    value = mapping.get(level, 50)
    st.markdown(f"**Dificuldade:** {colors.get(level, '🟨')} {level}")
    st.progress(value / 100)


def streak_bonus_points(streak: int) -> int:
    return max(0, streak - 1)


def get_fixed_options_for_question(qid: str, options: list[str], answer: str) -> list[str]:
    """
    Ordem determinística por questão:
    todos os alunos recebem a mesma ordem para a mesma questão.
    """
    key = f"opts_{qid}"
    if key not in st.session_state:
        rng = random.Random(qid)
        opts = options[:]
        rng.shuffle(opts)
        if answer not in opts:
            opts[-1] = answer
        st.session_state[key] = opts
    return st.session_state[key]


def show_alternative_feedback(q: dict, chosen: str):
    answer = q["answer"]
    rationale = q.get("rationale", {})

    if chosen == answer:
        st.success("✅ Correto!")
    else:
        st.error(f"❌ Incorreto. A resposta certa é: **{answer}**")

    st.markdown("#### ✅ Por que a correta é correta?")
    st.write(rationale.get(answer, q.get("explain", "A alternativa correta atende à regra do problema.")))

    if chosen != answer:
        st.markdown("#### ❌ Por que a sua escolha está errada?")
        st.write(rationale.get(chosen, "Essa alternativa não atende à lógica pedida."))

    st.markdown("#### 📌 Entenda as alternativas")
    for opt in q["options"]:
        tag = "✅" if opt == answer else "❌"
        st.write(f"- {tag} **{opt}** — {rationale.get(opt, 'Sem explicação cadastrada.')}")

    st.markdown("#### 🧠 Dica rápida")
    st.write(q.get("tip", "Leia o enunciado com atenção e teste mentalmente a condição."))


# =========================
# QUESTÕES
# =========================
QUESTIONS = [

    # =========================
    # 🟩 FÁCIL
    # =========================
    {
        "id": "Q01", "level": "Fácil",
        "prompt": "Qual estrutura usamos quando queremos tomar uma decisão simples em Java?",
        "options": ["for", "if", "switch", "while"],
        "answer": "if",
        "rationale": {
            "for": "❌ for é usado principalmente para repetição.",
            "if": "✅ if é a estrutura básica para decisão.",
            "switch": "❌ switch também decide, mas não é a estrutura mais simples e geral.",
            "while": "❌ while é usado para repetição."
        },
        "tip": "Quando o programa precisa decidir entre caminhos, pense primeiro em if."
    },
    {
        "id": "Q02", "level": "Fácil",
        "prompt": "O que este código imprime?",
        "code": 'int idade = 20;\nif (idade >= 18) {\n    System.out.println("Maior de idade");\n}',
        "options": ["Maior de idade", "Menor de idade", "20", "Nada"],
        "answer": "Maior de idade",
        "rationale": {
            "Maior de idade": "✅ 20 >= 18 é verdadeiro, então a mensagem é impressa.",
            "Menor de idade": "❌ Essa mensagem nem aparece no código.",
            "20": "❌ O código não imprime o valor da variável.",
            "Nada": "❌ A condição é verdadeira, então algo será impresso."
        },
        "tip": "Teste a condição mentalmente antes de pensar na saída."
    },
    {
        "id": "Q03", "level": "Fácil",
        "prompt": "Qual operador representa 'maior ou igual a' em Java?",
        "options": ["> = ", "= >", "= =", "< ="],
        "answer": "> =",
        "rationale": {
            ">=": "✅ Esse é o operador correto.",
            "=>": "❌ Essa ordem não existe em Java.",
            "==": "❌ == compara igualdade.",
            "<=": "❌ <= significa menor ou igual."
        },
        "tip": "Maior ou igual começa com >."
    },
    {
        "id": "Q04", "level": "Fácil",
        "prompt": "Se queremos executar um bloco quando a condição for falsa, usamos:",
        "options": ["case", "else", "break", "default"],
        "answer": "else",
        "rationale": {
            "case": "❌ case é usado dentro de switch.",
            "else": "✅ else executa quando o if for falso.",
            "break": "❌ break interrompe estruturas como switch ou laços.",
            "default": "❌ default é usado em switch."
        },
        "tip": "if trata o verdadeiro; else trata o contrário."
    },
    {
        "id": "Q05", "level": "Fácil",
        "prompt": "Qual saída esse código produz?",
        "code": 'int nota = 4;\nif (nota >= 5) {\n    System.out.println("Aprovado");\n} else {\n    System.out.println("Reprovado");\n}',
        "options": ["Aprovado", "Reprovado", "4", "Nada"],
        "answer": "Reprovado",
        "rationale": {
            "Aprovado": "❌ 4 >= 5 é falso.",
            "Reprovado": "✅ Como a condição é falsa, o else é executado.",
            "4": "❌ O código não imprime a nota.",
            "Nada": "❌ Sempre um dos blocos será executado."
        },
        "tip": "Se houver if/else, sempre haverá uma saída quando o código entrar nessa estrutura."
    },
    {
        "id": "Q06", "level": "Fácil",
        "prompt": "Quando o switch é mais indicado?",
        "options": [
            "Quando queremos repetir várias vezes",
            "Quando queremos comparar vários valores fixos",
            "Quando queremos trabalhar com laços",
            "Quando queremos declarar variáveis"
        ],
        "answer": "Quando queremos comparar vários valores fixos",
        "rationale": {
            "Quando queremos repetir várias vezes": "❌ Isso lembra for ou while.",
            "Quando queremos comparar vários valores fixos": "✅ switch é ótimo para comparar casos específicos.",
            "Quando queremos trabalhar com laços": "❌ switch não é laço.",
            "Quando queremos declarar variáveis": "❌ switch não serve para isso."
        },
        "tip": "switch combina bem com opções fixas: 1, 2, 3 ou nomes de dias, meses, menu etc."
    },

    # =========================
    # 🟨 MÉDIO
    # =========================
    {
        "id": "Q07", "level": "Médio",
        "prompt": "O que esse código imprime?",
        "code": 'int x = 10;\nif (x > 0) {\n    System.out.println("Positivo");\n} else if (x == 0) {\n    System.out.println("Zero");\n} else {\n    System.out.println("Negativo");\n}',
        "options": ["Positivo", "Zero", "Negativo", "Nada"],
        "answer": "Positivo",
        "rationale": {
            "Positivo": "✅ 10 > 0 é verdadeiro, então o primeiro bloco já é executado.",
            "Zero": "❌ x não vale 0.",
            "Negativo": "❌ x não é menor que 0.",
            "Nada": "❌ Uma das condições é satisfeita."
        },
        "tip": "No encadeamento if / else if / else, quando uma condição é verdadeira, as próximas não são testadas."
    },
    {
        "id": "Q08", "level": "Médio",
        "prompt": "Qual condição representa corretamente: 'o aluno está aprovado se a nota for maior ou igual a 6'?",
        "options": ["nota > 6", "nota >= 6", "nota == 6", "nota <= 6"],
        "answer": "nota >= 6",
        "rationale": {
            "nota > 6": "❌ Exclui a nota 6.",
            "nota >= 6": "✅ Inclui 6 e valores maiores.",
            "nota == 6": "❌ Aceita apenas exatamente 6.",
            "nota <= 6": "❌ Isso incluiria notas menores também."
        },
        "tip": "Leia com atenção quando o enunciado disser 'maior ou igual'."
    },
    {
        "id": "Q09", "level": "Médio",
        "prompt": "Qual estrutura seria melhor para um menu com opções 1, 2, 3 e 4?",
        "options": ["if simples", "if/else", "switch", "while"],
        "answer": "switch",
        "rationale": {
            "if simples": "❌ if simples trata apenas uma decisão.",
            "if/else": "❌ Até poderia ser usado, mas switch fica mais organizado para vários valores fixos.",
            "switch": "✅ É a estrutura mais adequada nesse caso.",
            "while": "❌ while é repetição."
        },
        "tip": "Quando há várias opções fixas, switch tende a deixar o código mais limpo."
    },
    {
        "id": "Q10", "level": "Médio",
        "prompt": "O que imprime?",
        "code": 'int dia = 2;\nswitch (dia) {\n    case 1:\n        System.out.println("Domingo");\n        break;\n    case 2:\n        System.out.println("Segunda");\n        break;\n    default:\n        System.out.println("Outro");\n}',
        "options": ["Domingo", "Segunda", "Outro", "Nada"],
        "answer": "Segunda",
        "rationale": {
            "Domingo": "❌ O valor de dia é 2.",
            "Segunda": "✅ O case 2 será executado.",
            "Outro": "❌ O default só roda se nenhum case combinar.",
            "Nada": "❌ Há um case correspondente."
        },
        "tip": "No switch, procure primeiro qual case combina com o valor da variável."
    },
    {
        "id": "Q11", "level": "Médio",
        "prompt": "Qual código representa melhor a lógica: 'Se a temperatura for maior que 30, escreva Calor'?",
        "options": [
            'if (temperatura > 30) { System.out.println("Calor"); }',
            'if (temperatura < 30) { System.out.println("Calor"); }',
            'switch (temperatura > 30) { case true: "Calor"; }',
            'while (temperatura > 30) { System.out.println("Calor"); }'
        ],
        "answer": 'if (temperatura > 30) { System.out.println("Calor"); }',
        "rationale": {
            'if (temperatura > 30) { System.out.println("Calor"); }': "✅ Expressa exatamente a condição pedida.",
            'if (temperatura < 30) { System.out.println("Calor"); }': "❌ A lógica ficou invertida.",
            'switch (temperatura > 30) { case true: "Calor"; }': "❌ Não é a forma adequada nesse contexto e ainda está incompleto.",
            'while (temperatura > 30) { System.out.println("Calor"); }': "❌ while repetiria várias vezes."
        },
        "tip": "Quando a situação é uma única decisão, if costuma ser a melhor escolha."
    },
    {
        "id": "Q12", "level": "Médio",
        "prompt": "O que imprime esse código?",
        "code": 'int media = 8;\nif (media >= 9) {\n    System.out.println("Excelente");\n} else if (media >= 7) {\n    System.out.println("Bom");\n} else if (media >= 5) {\n    System.out.println("Regular");\n} else {\n    System.out.println("Insuficiente");\n}',
        "options": ["Excelente", "Bom", "Regular", "Insuficiente"],
        "answer": "Bom",
        "rationale": {
            "Excelente": "❌ 8 não é maior ou igual a 9.",
            "Bom": "✅ 8 atende à condição media >= 7.",
            "Regular": "❌ Essa condição nem chega a ser testada, porque a anterior já foi verdadeira.",
            "Insuficiente": "❌ 8 não cai no else."
        },
        "tip": "Em else if, a ordem importa."
    },
    {
        "id": "Q13", "level": "Médio",
        "prompt": "Em um switch, para evitar que o programa continue executando os próximos casos, usamos:",
        "options": ["continue", "stop", "break", "return"],
        "answer": "break",
        "rationale": {
            "continue": "❌ continue é mais comum em laços.",
            "stop": "❌ stop não é palavra-chave do Java.",
            "break": "✅ break encerra o case atual.",
            "return": "❌ return sai do método, não é o objetivo aqui."
        },
        "tip": "Esqueceu o break? O switch pode continuar nos próximos casos."
    },
    {
        "id": "Q14", "level": "Médio",
        "prompt": "Qual alternativa representa melhor: 'Se o número for par, escreva Par; caso contrário, escreva Ímpar'?",
        "options": [
            'if (numero % 2 == 0) { System.out.println("Par"); } else { System.out.println("Ímpar"); }',
            'if (numero % 2 == 1) { System.out.println("Par"); }',
            'switch (numero) { case 0: System.out.println("Par"); }',
            'if (numero / 2 == 0) { System.out.println("Par"); }'
        ],
        "answer": 'if (numero % 2 == 0) { System.out.println("Par"); } else { System.out.println("Ímpar"); }',
        "rationale": {
            'if (numero % 2 == 0) { System.out.println("Par"); } else { System.out.println("Ímpar"); }': "✅ Usa a regra correta do resto da divisão por 2.",
            'if (numero % 2 == 1) { System.out.println("Par"); }': "❌ Isso indicaria ímpar, e ainda falta o else.",
            'switch (numero) { case 0: System.out.println("Par"); }': "❌ Não resolve corretamente para todos os números.",
            'if (numero / 2 == 0) { System.out.println("Par"); }': "❌ Dividir por 2 não testa se o número é par."
        },
        "tip": "Número par tem resto 0 na divisão por 2."
    },

    # =========================
    # 🟥 DIFÍCIL
    # =========================
    {
        "id": "Q15", "level": "Difícil",
        "prompt": "O que imprime esse código?",
        "code": 'int x = 5;\nif (x > 0) {\n    if (x < 10) {\n        System.out.println("A");\n    } else {\n        System.out.println("B");\n    }\n} else {\n    System.out.println("C");\n}',
        "options": ["A", "B", "C", "Nada"],
        "answer": "A",
        "rationale": {
            "A": "✅ x > 0 é verdadeiro e x < 10 também é verdadeiro.",
            "B": "❌ O else interno não executa porque x < 10 é verdadeiro.",
            "C": "❌ O else externo não executa porque x > 0 é verdadeiro.",
            "Nada": "❌ Há saída."
        },
        "tip": "Quando há if dentro de if, avalie de fora para dentro."
    },
    {
        "id": "Q16", "level": "Difícil",
        "prompt": "O que acontece nesse switch?",
        "code": 'int op = 1;\nswitch (op) {\n    case 1:\n        System.out.println("A");\n    case 2:\n        System.out.println("B");\n        break;\n    default:\n        System.out.println("C");\n}',
        "options": ["Imprime apenas A", "Imprime A e B", "Imprime B e C", "Imprime apenas C"],
        "answer": "Imprime A e B",
        "rationale": {
            "Imprime apenas A": "❌ Não há break após o case 1.",
            "Imprime A e B": "✅ Sem break no case 1, ocorre fall-through para o case 2.",
            "Imprime B e C": "❌ O case 1 também executa.",
            "Imprime apenas C": "❌ O default não será alcançado nesse caso."
        },
        "tip": "Sem break, o switch pode continuar executando os próximos casos."
    },
    {
        "id": "Q17", "level": "Difícil",
        "prompt": "Qual estrutura é mais adequada para classificar uma nota em faixas como 0-4, 5-6, 7-8, 9-10?",
        "options": ["switch", "if/else if", "for", "break"],
        "answer": "if/else if",
        "rationale": {
            "switch": "❌ switch funciona melhor com valores fixos, não com intervalos.",
            "if/else if": "✅ Intervalos são melhor tratados com comparações condicionais.",
            "for": "❌ for é laço de repetição.",
            "break": "❌ break não é estrutura de decisão."
        },
        "tip": "Intervalos combinam com if/else if; valores fixos combinam com switch."
    },
    {
        "id": "Q18", "level": "Difícil",
        "prompt": "O que imprime esse código?",
        "code": 'int idade = 18;\nboolean temDocumento = false;\nif (idade >= 18 && temDocumento) {\n    System.out.println("Entrada permitida");\n} else {\n    System.out.println("Entrada negada");\n}',
        "options": ["Entrada permitida", "Entrada negada", "18", "Nada"],
        "answer": "Entrada negada",
        "rationale": {
            "Entrada permitida": "❌ Embora idade >= 18 seja verdadeiro, temDocumento é false.",
            "Entrada negada": "✅ No operador &&, as duas condições precisam ser verdadeiras.",
            "18": "❌ O código não imprime a idade.",
            "Nada": "❌ O else será executado."
        },
        "tip": "No operador &&, basta uma condição ser falsa para o resultado ser falso."
    },
    {
        "id": "Q19", "level": "Difícil",
        "prompt": "Qual saída esse código produz?",
        "code": 'int a = 7;\nif (a >= 5)\n    if (a >= 8)\n        System.out.println("X");\n    else\n        System.out.println("Y");',
        "options": ["X", "Y", "Nada", "Erro"],
        "answer": "Y",
        "rationale": {
            "X": "❌ a >= 8 é falso.",
            "Y": "✅ a >= 5 é verdadeiro, então entra no segundo if; como a >= 8 é falso, imprime Y.",
            "Nada": "❌ Há saída.",
            "Erro": "❌ O código é válido."
        },
        "tip": "Mesmo sem chaves, o else se associa ao if mais próximo."
    },
    {
        "id": "Q20", "level": "Difícil",
        "prompt": "Qual alternativa resolve corretamente este problema: 'Leia um número. Se ele for positivo, escreva Positivo; se for zero, escreva Zero; caso contrário, escreva Negativo'?",
        "options": [
            'if (n > 0) { System.out.println("Positivo"); } else if (n == 0) { System.out.println("Zero"); } else { System.out.println("Negativo"); }',
            'if (n >= 0) { System.out.println("Positivo"); } else { System.out.println("Negativo"); }',
            'switch (n) { case 0: System.out.println("Zero"); default: System.out.println("Positivo"); }',
            'if (n < 0) { System.out.println("Positivo"); } else if (n == 0) { System.out.println("Zero"); }'
        ],
        "answer": 'if (n > 0) { System.out.println("Positivo"); } else if (n == 0) { System.out.println("Zero"); } else { System.out.println("Negativo"); }',
        "rationale": {
            'if (n > 0) { System.out.println("Positivo"); } else if (n == 0) { System.out.println("Zero"); } else { System.out.println("Negativo"); }': "✅ Trata corretamente as três situações.",
            'if (n >= 0) { System.out.println("Positivo"); } else { System.out.println("Negativo"); }': "❌ Zero seria classificado como positivo.",
            'switch (n) { case 0: System.out.println("Zero"); default: System.out.println("Positivo"); }': "❌ Números negativos seriam classificados como positivos.",
            'if (n < 0) { System.out.println("Positivo"); } else if (n == 0) { System.out.println("Zero"); }': "❌ A lógica está invertida e ainda falta o caso positivo."
        },
        "tip": "Quando há três caminhos possíveis, else if costuma ser uma boa solução."
    },

    # +6 DIFÍCEIS
    {
        "id": "Q21", "level": "Difícil",
        "prompt": "O que este código imprime?",
        "code": 'int n = 12;\nif (n % 2 == 0) {\n    if (n > 10) {\n        System.out.println("A");\n    } else {\n        System.out.println("B");\n    }\n} else {\n    System.out.println("C");\n}',
        "options": ["A", "B", "C", "Nada"],
        "answer": "A",
        "rationale": {
            "A": "✅ 12 é par e maior que 10.",
            "B": "❌ A segunda condição é verdadeira.",
            "C": "❌ O número é par.",
            "Nada": "❌ O código imprime algo."
        },
        "tip": "Avalie as condições de fora para dentro."
    },
    {
        "id": "Q22", "level": "Difícil",
        "prompt": "Qual saída o código produz?",
        "code": 'int x = 7;\nif (x > 10)\n    System.out.println("A");\nelse if (x > 5)\n    System.out.println("B");\nelse\n    System.out.println("C");',
        "options": ["A", "B", "C", "Nada"],
        "answer": "B",
        "rationale": {
            "A": "❌ 7 não é maior que 10.",
            "B": "✅ 7 é maior que 5.",
            "C": "❌ O segundo if já foi verdadeiro.",
            "Nada": "❌ Uma condição será executada."
        },
        "tip": "No encadeamento else if, apenas o primeiro verdadeiro executa."
    },
    {
        "id": "Q23", "level": "Difícil",
        "prompt": "O que acontece neste código?",
        "code": 'int dia = 3;\nswitch(dia) {\ncase 1:\ncase 2:\n    System.out.println("Início da semana");\n    break;\ncase 3:\ncase 4:\n    System.out.println("Meio da semana");\n    break;\ndefault:\n    System.out.println("Outro");\n}',
        "options": ["Início da semana", "Meio da semana", "Outro", "Nada"],
        "answer": "Meio da semana",
        "rationale": {
            "Início da semana": "❌ Esse caso vale apenas para 1 ou 2.",
            "Meio da semana": "✅ O valor 3 entra nesse grupo.",
            "Outro": "❌ Default não é usado.",
            "Nada": "❌ Sempre haverá saída."
        },
        "tip": "switch pode agrupar vários cases."
    },
    {
        "id": "Q24", "level": "Difícil",
        "prompt": "Qual código representa corretamente: 'Se o número for múltiplo de 3, escreva M3'?",
        "options": [
            'if (n % 3 == 0) { System.out.println("M3"); }',
            'if (n / 3 == 0) { System.out.println("M3"); }',
            'if (n % 3 == 1) { System.out.println("M3"); }',
            'if (n * 3 == 0) { System.out.println("M3"); }'
        ],
        "answer": 'if (n % 3 == 0) { System.out.println("M3"); }',
        "rationale": {
            'if (n % 3 == 0) { System.out.println("M3"); }': "✅ Essa é a regra correta.",
            'if (n / 3 == 0) { System.out.println("M3"); }': "❌ Divisão não testa múltiplo.",
            'if (n % 3 == 1) { System.out.println("M3"); }': "❌ Isso indicaria resto 1.",
            'if (n * 3 == 0) { System.out.println("M3"); }': "❌ Não verifica múltiplos."
        },
        "tip": "Múltiplos usam operador módulo %."
    },
    {
        "id": "Q25", "level": "Difícil",
        "prompt": "O que imprime?",
        "code": 'int a = 3;\nint b = 4;\nif (a > 2 && b > 5) {\n    System.out.println("A");\n} else {\n    System.out.println("B");\n}',
        "options": ["A", "B", "Nada", "Erro"],
        "answer": "B",
        "rationale": {
            "A": "❌ b > 5 é falso.",
            "B": "✅ No operador && ambas precisam ser verdadeiras.",
            "Nada": "❌ O else será executado.",
            "Erro": "❌ Código válido."
        },
        "tip": "&& exige duas condições verdadeiras."
    },
    {
        "id": "Q26", "level": "Difícil",
        "prompt": "O que imprime?",
        "code": 'int x = 5;\nif (x > 10) {\n    System.out.println("A");\n} else if (x > 3) {\n    if (x < 7) {\n        System.out.println("B");\n    }\n}',
        "options": ["A", "B", "Nada", "Erro"],
        "answer": "B",
        "rationale": {
            "A": "❌ x não é maior que 10.",
            "B": "✅ x > 3 e x < 7.",
            "Nada": "❌ A condição interna imprime algo.",
            "Erro": "❌ Código válido."
        },
        "tip": "Avalie todas as condições."
    },

    # ⚫ ULTRA DIFÍCIL
    {
        "id": "Q27", "level": "Ultra Difícil",
        "prompt": "O que este código imprime?",
        "code": 'int x = 4;\nif (x > 5)\n    if (x > 10)\n        System.out.println("A");\n    else\n        System.out.println("B");',
        "options": ["A", "B", "Nada", "Erro"],
        "answer": "Nada",
        "rationale": {
            "A": "❌ O primeiro if é falso.",
            "B": "❌ O else pertence ao if mais próximo, mas o primeiro if não executa.",
            "Nada": "✅ O primeiro if falha.",
            "Erro": "❌ Código válido."
        },
        "tip": "Cuidado com if sem chaves."
    },
    {
        "id": "Q28", "level": "Ultra Difícil",
        "prompt": "Qual saída ocorre?",
        "code": 'int x = 2;\nswitch(x) {\ncase 1:\ncase 2:\ncase 3:\n    System.out.println("Grupo 1");\n    break;\ncase 4:\n    System.out.println("Grupo 2");\n}',
        "options": ["Grupo 1", "Grupo 2", "Nada", "Erro"],
        "answer": "Grupo 1",
        "rationale": {
            "Grupo 1": "✅ O valor 2 pertence ao grupo.",
            "Grupo 2": "❌ O case 4 não é executado.",
            "Nada": "❌ Um case será executado.",
            "Erro": "❌ Código válido."
        },
        "tip": "Cases podem compartilhar bloco."
    },
    {
        "id": "Q29", "level": "Ultra Difícil",
        "prompt": "O que imprime?",
        "code": 'int x = 5;\nint y = 10;\nif (x > 3 && y < 20)\n    if (y > 15)\n        System.out.println("A");\n    else\n        System.out.println("B");',
        "options": ["A", "B", "Nada", "Erro"],
        "answer": "B",
        "rationale": {
            "A": "❌ y não é maior que 15.",
            "B": "✅ Primeira condição verdadeira, segunda falsa.",
            "Nada": "❌ Algo será impresso.",
            "Erro": "❌ Código válido."
        },
        "tip": "Analise && antes de entrar no segundo if."
    },
    {
        "id": "Q30", "level": "Ultra Difícil",
        "prompt": "O que imprime?",
        "code": 'int n = 0;\nif (n == 0)\n    System.out.println("Zero");\nelse if (n > 0)\n    System.out.println("Positivo");\nelse\n    System.out.println("Negativo");',
        "options": ["Zero", "Positivo", "Negativo", "Nada"],
        "answer": "Zero",
        "rationale": {
            "Zero": "✅ n é igual a 0.",
            "Positivo": "❌ n não é maior que 0.",
            "Negativo": "❌ n não é menor que 0.",
            "Nada": "❌ Uma condição será executada."
        },
        "tip": "Avalie na ordem if → else if → else."
    }
]


# =========================
# SESSION STATE
# =========================
def clear_fixed_option_states():
    for k in list(st.session_state.keys()):
        if str(k).startswith("opts_Q") or str(k).startswith("radio_Q"):
            del st.session_state[k]


def reset_quiz_order():
    """
    Ordem fixa, sem aleatoriedade entre questões.
    """
    st.session_state.q_order = list(range(len(QUESTIONS)))


def reset_quiz_progress():
    st.session_state.q_index = 0
    st.session_state.base_correct = 0
    st.session_state.final_points = 0
    st.session_state.streak = 0
    st.session_state.max_streak = 0
    st.session_state.show_feedback = False
    st.session_state.last_choice = None
    st.session_state.last_q = None
    st.session_state.last_bonus = 0
    st.session_state.saved_score = False
    clear_fixed_option_states()


def reset_all():
    reset_quiz_order()
    reset_quiz_progress()


if "student_name" not in st.session_state:
    st.session_state.student_name = ""
if "admin_authed" not in st.session_state:
    st.session_state.admin_authed = False
if "confirm_clear" not in st.session_state:
    st.session_state.confirm_clear = False
if "q_order" not in st.session_state:
    reset_all()


# =========================
# NAV
# =========================
st.sidebar.title("📌 Menu")
view = st.sidebar.radio("Ir para:", ["👤 Aluno", "🔐 Admin"], index=0)


# ==========================================================
# VIEW: STUDENT
# ==========================================================
if view == "👤 Aluno":
    st.subheader("👤 Área do aluno")

    if not st.session_state.student_name:
        nome = st.text_input("Nome do aluno:", placeholder="Ex.: Maria Silva")
        if st.button("🚀 Iniciar"):
            nome_limpo = (nome or "").strip()
            if len(nome_limpo) < 3:
                st.warning("⚠️ Informe um nome com pelo menos 3 caracteres.")
            else:
                st.session_state.student_name = nome_limpo
                reset_all()
                st.rerun()
        st.info("A atividade segue uma ordem fixa: fácil → médio → difícil → ultra difícil.")
    else:
        total = len(QUESTIONS)
        percent_official_live = (st.session_state.base_correct / total) * 100 if total else 0.0

        st.success(f"Aluno: **{st.session_state.student_name}**")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("✅ Acertos oficiais", f"{st.session_state.base_correct}/{total}")
        c2.metric("📈 % oficial", f"{percent_official_live:.1f}%")
        c3.metric("🏁 Pontuação final", st.session_state.final_points)
        c4.metric("🔥 Streak", st.session_state.streak)

        if st.session_state.q_index >= total:
            st.success("🎉 Atividade finalizada!")
            percent_official = (st.session_state.base_correct / total) * 100 if total else 0.0

            st.metric("📈 % oficial de acerto", f"{percent_official:.1f}%")
            st.metric("🏁 Pontuação final (com bônus)", st.session_state.final_points)
            st.metric("🏆 Maior streak", st.session_state.max_streak)

            if not st.session_state.saved_score:
                append_score(
                    st.session_state.student_name,
                    st.session_state.base_correct,
                    st.session_state.final_points,
                    total,
                    st.session_state.max_streak
                )
                st.session_state.saved_score = True

            col1, col2 = st.columns(2)
            if col1.button("🔁 Refazer"):
                reset_all()
                st.rerun()
            if col2.button("👤 Trocar aluno"):
                st.session_state.student_name = ""
                reset_all()
                st.rerun()

        else:
            qpos = st.session_state.q_order[st.session_state.q_index]
            q = QUESTIONS[qpos]

            st.progress(st.session_state.q_index / total)
            difficulty_bar(q["level"])

            st.markdown(f"### {q['id']} — {q['prompt']}")
            if q.get("code"):
                st.code(q["code"], language="java")

            disabled = st.session_state.show_feedback

            options = get_fixed_options_for_question(q["id"], q["options"], q["answer"])
            letters = ["A", "B", "C", "D"]
            labeled = [f"{letters[i]}) {opt}" for i, opt in enumerate(options)]
            label_to_value = {labeled[i]: options[i] for i in range(len(options))}

            choice_label = st.radio(
                "Escolha a alternativa:",
                labeled,
                index=0,
                disabled=disabled,
                key=f"radio_{q['id']}"
            )
            choice = label_to_value[choice_label]

            if not st.session_state.show_feedback:
                if st.button("✅ Confirmar"):
                    correct = (choice == q["answer"])

                    append_answer(
                        st.session_state.student_name,
                        q["id"],
                        q["level"],
                        correct
                    )

                    if correct:
                        st.session_state.base_correct += 1
                        st.session_state.streak += 1
                        st.session_state.max_streak = max(
                            st.session_state.max_streak,
                            st.session_state.streak
                        )
                        bonus = streak_bonus_points(st.session_state.streak)
                        st.session_state.final_points += 1 + bonus
                        st.session_state.last_bonus = bonus
                    else:
                        st.session_state.streak = 0
                        st.session_state.last_bonus = 0

                    st.session_state.last_choice = choice
                    st.session_state.last_q = q
                    st.session_state.show_feedback = True
                    st.rerun()

            if st.session_state.show_feedback:
                q_last = st.session_state.last_q
                chosen_last = st.session_state.last_choice

                show_alternative_feedback(q_last, chosen_last)

                if st.button("➡️ Próximo"):
                    rk = f"radio_{q['id']}"
                    if rk in st.session_state:
                        del st.session_state[rk]

                    st.session_state.q_index += 1
                    st.session_state.show_feedback = False
                    st.session_state.last_choice = None
                    st.session_state.last_q = None
                    st.rerun()


# ==========================================================
# VIEW: ADMIN
# ==========================================================
else:
    st.subheader("🔐 Área do administrador")

    if not st.session_state.admin_authed:
        user = st.text_input("Usuário")
        pwd = st.text_input("Senha", type="password")
        if st.button("🔓 Entrar"):
            if user == ADMIN_USER and pwd == ADMIN_PASS:
                st.session_state.admin_authed = True
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")
        st.info("Configure em `.streamlit/secrets.toml`.")
    else:
        st.success("✅ Admin autenticado.")

        col1, col2 = st.columns(2)
        if col1.button("🚪 Sair (logout)"):
            st.session_state.admin_authed = False
            st.session_state.confirm_clear = False
            st.rerun()
        if col2.button("🗑️ Limpar todos os dados"):
            st.session_state.confirm_clear = True

        if st.session_state.confirm_clear:
            st.warning("⚠️ Apagar tudo (pontuações e respostas)?")
            c1, c2 = st.columns(2)
            if c1.button("✅ Confirmar exclusão"):
                clear_all_data()
                st.session_state.confirm_clear = False
                st.success("✔️ Dados apagados.")
                st.rerun()
            if c2.button("❌ Cancelar"):
                st.session_state.confirm_clear = False
                st.rerun()

        rows = load_scores()
        answers = load_answers()

        st.markdown("## 📊 Taxa de acerto por dificuldade")
        if not answers:
            st.info("Ainda não há respostas registradas por questão.")
        else:
            stats = {
                "Fácil": {"correct": 0, "total": 0},
                "Médio": {"correct": 0, "total": 0},
                "Difícil": {"correct": 0, "total": 0},
                "Ultra Difícil": {"correct": 0, "total": 0},
            }

            for a in answers:
                level = a.get("level", "Médio")
                if level not in stats:
                    stats[level] = {"correct": 0, "total": 0}
                stats[level]["total"] += 1
                stats[level]["correct"] += 1 if a["is_correct"] == 1 else 0

            chart_data = []
            for level in ["Fácil", "Médio", "Difícil", "Ultra Difícil"]:
                total_r = stats[level]["total"]
                correct_r = stats[level]["correct"]
                rate = (correct_r / total_r) * 100 if total_r else 0.0
                chart_data.append({
                    "Dificuldade": level,
                    "Taxa (%)": round(rate, 1),
                    "Total respostas": total_r
                })

            chart_df = pd.DataFrame(chart_data).set_index("Dificuldade")
            st.bar_chart(chart_df["Taxa (%)"])
            st.dataframe(chart_data, use_container_width=True, hide_index=True)

        st.markdown("## 🏆 Ranking (finalizados)")
        if not rows:
            st.warning("Ainda não há pontuações finalizadas.")
        else:
            best_by_student = {}
            for r in rows:
                name = (r.get("student_name") or "").strip()
                if not name:
                    continue

                key = (
                    r["percent_official"],
                    r["final_points"],
                    r.get("max_streak", 0),
                    r["timestamp_utc"]
                )

                if name not in best_by_student:
                    best_by_student[name] = r
                else:
                    cur = best_by_student[name]
                    cur_key = (
                        cur["percent_official"],
                        cur["final_points"],
                        cur.get("max_streak", 0),
                        cur["timestamp_utc"]
                    )
                    if key > cur_key:
                        best_by_student[name] = r

            best_list = list(best_by_student.values())
            best_sorted = sorted(
                best_list,
                key=lambda x: (
                    x["percent_official"],
                    x["final_points"],
                    x.get("max_streak", 0),
                    x["timestamp_utc"]
                ),
                reverse=True
            )

            medals = {1: "🥇", 2: "🥈", 3: "🥉"}
            ranking_table = []

            for i, r in enumerate(best_sorted[:10], start=1):
                ranking_table.append({
                    "Posição": f"{medals.get(i, '🏅')} {i}",
                    "Aluno": r["student_name"],
                    "✅ Acertos": f"{r['base_correct']}/{r['total']}",
                    "📈 % oficial": f"{r['percent_official']:.1f}%",
                    "🏁 Pontos finais": r["final_points"],
                    "🔥 Max streak": r.get("max_streak", 0),
                    "Última (UTC)": r["timestamp_utc"],
                })

            st.dataframe(ranking_table, use_container_width=True, hide_index=True)

        st.markdown("## 📥 Exportar dados")
        ensure_scores_file()
        ensure_answers_file()

        with open(SCORES_FILE, "rb") as f:
            st.download_button(
                "📥 Baixar CSV de Pontuações (finalizados)",
                f,
                file_name="condicionais_scores.csv",
                mime="text/csv"
            )

        with open(ANSWERS_FILE, "rb") as f:
            st.download_button(
                "📥 Baixar CSV de Respostas por Questão",
                f,
                file_name="condicionais_answers.csv",
                mime="text/csv"
            )

        st.caption(
            f"Arquivos: `{SCORES_FILE.as_posix()}`, `{ANSWERS_FILE.as_posix()}`"
        )
