import json
import pandas as pd
import requests
import streamlit as st
from datetime import datetime

# ============ CONFIGURAÇÃO ============
OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO = "gpt-oss"

# ============ CARREGAR DADOS ============
perfil = json.load(open('./data/perfil_pessoal.json'))
agenda = pd.read_csv('./data/agenda_tarefas.csv')
historico = pd.read_csv('./data/historico_conversas.csv', sep=';')
base_conhecimento = json.load(open('./data/base_conhecimento.json'))

# ============ MONTAR CONTEXTO ============
# Filtra apenas tarefas pendentes e dos próximos dias
hoje = datetime.now().strftime('%Y-%m-%d')
agenda_proximos = agenda[agenda['data'] >= hoje].head(10)  # próximos 10 compromissos

contexto = f"""
PERFIL PESSOAL:
Nome: {perfil['nome']}
Idade: {perfil['idade']} anos
Cidade: {perfil['cidade']}
Profissão: {perfil['profissao']}
Hobbies: {', '.join(perfil['hobbies'])}
Objetivos: {', '.join(perfil['objetivos'])}

PREFERÊNCIAS:
Comida favorita: {perfil['preferencias']['comida']}
Filme favorito: {perfil['preferencias']['filme']}
Música favorita: {perfil['preferencias']['musica']}

CONTATOS IMPORTANTES:
{', '.join([f"{c['nome']} (aniversário: {c['aniversario']})" for c in perfil['contatos_importantes']])}

AGENDA E TAREFAS PRÓXIMAS:
{agenda_proximos.to_string(index=False)}

CONVERSAS ANTERIORES:
{historico.tail(5).to_string(index=False)}

BASE DE CONHECIMENTO PESSOAL:
Regras da casa: {json.dumps(base_conhecimento.get('regras_casa', {}), indent=2, ensure_ascii=False)}
Locais favoritos: {json.dumps(base_conhecimento.get('locais_favoritos', {}), indent=2, ensure_ascii=False)}
Receitas favoritas: {json.dumps(base_conhecimento.get('receitas_favoritas', {}), indent=2, ensure_ascii=False)}
Filmes recomendados: {json.dumps(base_conhecimento.get('filmes_recomendados', {}), indent=2, ensure_ascii=False)}
Lembretes recorrentes: {json.dumps(base_conhecimento.get('lembretes_recorrentes', {}), indent=2, ensure_ascii=False)}
"""

# ============ SYSTEM PROMPT ============
SYSTEM_PROMPT = """Você é o Fred, um assistente pessoal amigável, atencioso e organizado.

OBJETIVO:
Ajudar o usuário a gerenciar sua rotina, lembrando compromissos, sugerindo com base nas preferências pessoais e tornando o dia a dia mais produtivo.

REGRAS:
- Use os dados fornecidos (perfil, agenda, base de conhecimento) para personalizar as respostas;
- Seja proativo: se o usuário perguntar sobre o dia, mencione compromissos próximos;
- Use tom amigável e informal, como um amigo que conhece bem o usuário;
- Nunca invente informações: se não encontrar nos dados, diga "Não tenho essa informação no momento";
- Para perguntas sobre preferências, consulte a base de conhecimento;
- Para perguntas sobre agenda, consulte os dados de tarefas e compromissos;
- Lembre de aniversários e datas importantes dos contatos;
- Responda de forma sucinta e direta, com no máximo 3 parágrafos;
- Use emojis moderadamente para tornar a conversa mais leve (📅, ✅, ☕, 🎂, 🎬).
"""

# ============ CHAMAR OLLAMA ============
def perguntar(msg):
    prompt = f"""
    {SYSTEM_PROMPT}

    CONTEXTO DO USUÁRIO:
    {contexto}

    Data atual: {datetime.now().strftime('%d/%m/%Y')}
    Horário atual: {datetime.now().strftime('%H:%M')}

    Pergunta: {msg}"""

    r = requests.post(OLLAMA_URL, json={"model": MODELO, "prompt": prompt, "stream": False})
    return r.json()['response']

# ============ INTERFACE ============
st.title("🧑‍💼 Fred, seu Assistente Pessoal")
st.caption("Pergunte sobre sua agenda, receitas, locais favoritos ou peça lembretes!")

# Inicializar histórico no session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibir mensagens do histórico
for message in st.session_state.messages:
    st.chat_message(message["role"]).write(message["content"])

# Campo de input
if pergunta := st.chat_input("O que você precisa, Fred? (ex: 'O que tenho hoje?' ou 'Qual restaurante você recomenda?')"):
    st.chat_message("user").write(pergunta)
    st.session_state.messages.append({"role": "user", "content": pergunta})
    
    with st.spinner("🤔 Pensando..."):
        resposta = perguntar(pergunta)
        st.chat_message("assistant").write(resposta)
        st.session_state.messages.append({"role": "assistant", "content": resposta})
