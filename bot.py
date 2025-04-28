import discord
from discord import app_commands, ButtonStyle
from discord.ui import Button, View
import os
import threading
import requests
import asyncio
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
import time
from bs4 import BeautifulSoup

# Log inicial para confirmar que o script começou
print("Iniciando bot.py...")

# Configura os intents
print("Configurando intents do Discord...")
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Inicializa o cliente do Discord
print("Inicializando cliente do Discord...")
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ID do time da FURIA na PandaScore
FURIA_ID = 124530
# Chave da API da PandaScore (obtida via variável de ambiente)
print("Obtendo PANDASCORE_API_KEY...")
PANDASCORE_API_KEY = os.getenv("PANDASCORE_API_KEY")
if not PANDASCORE_API_KEY:
    print("Erro: PANDASCORE_API_KEY não encontrado nas variáveis de ambiente.")
    raise ValueError("PANDASCORE_API_KEY not found in environment variables")
else:
    print("PANDASCORE_API_KEY encontrado com sucesso.")

# Canal onde as notificações serão enviadas (obtida via variável de ambiente)
print("Obtendo NOTIFICATION_CHANNEL_ID...")
NOTIFICATION_CHANNEL_ID = os.getenv("NOTIFICATION_CHANNEL_ID")
if not NOTIFICATION_CHANNEL_ID:
    print("Aviso: NOTIFICATION_CHANNEL_ID não encontrado nas variáveis de ambiente. Notificações automáticas serão desativadas.")
    NOTIFICATION_CHANNEL_ID = None
else:
    try:
        NOTIFICATION_CHANNEL_ID = int(NOTIFICATION_CHANNEL_ID)
        print(f"NOTIFICATION_CHANNEL_ID configurado como: {NOTIFICATION_CHANNEL_ID}")
    except ValueError:
        print("Erro: NOTIFICATION_CHANNEL_ID deve ser um número inteiro.")
        raise ValueError("NOTIFICATION_CHANNEL_ID must be an integer")

# Lista para rastrear jogos já notificados (evitar notificações duplicadas)
notified_matches = []

# Cache para armazenar resultados da API
cache = {
    "upcoming_matches": {"data": None, "timestamp": None},
    "recent_results": {"data": None, "timestamp": None}
}
CACHE_DURATION = 3600  # 1 hora em segundos

# Função para verificar se o cache está válido
def is_cache_valid(cache_entry):
    if cache_entry["data"] is None or cache_entry["timestamp"] is None:
        return False
    elapsed_time = (datetime.utcnow() - cache_entry["timestamp"]).total_seconds()
    return elapsed_time < CACHE_DURATION

# Função para validar o token da API na inicialização
def validate_api_token():
    try:
        url = f"https://api.pandascore.co/csgo/teams?filter[id]={FURIA_ID}&token={PANDASCORE_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        print("Token da API da PandaScore validado com sucesso.")
        return True
    except Exception as e:
        print(f"Falha ao validar o token da API da PandaScore: {str(e)}")
        return False

# Função para buscar resultados recentes do Flashscore (fallback)
def get_recent_results_flashscore():
    for attempt in range(3):  # Tenta até 3 vezes
        try:
            # URL da página de resultados da FURIA no Flashscore
            url = "https://www.flashscore.com/team/furia/6z2eC9tF/results/"
            print(f"Tentativa {attempt + 1}/3 de buscar resultados no Flashscore")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            print("Resposta recebida do Flashscore com sucesso.")
            soup = BeautifulSoup(response.text, 'html.parser')

            # Log do HTML para depuração
            print("HTML recebido (primeiros 500 caracteres):")
            print(str(soup)[:500])

            # Encontra os resultados
            matches = soup.find_all('div', class_='event__match')[:4]  # Limita a 4 resultados
            if not matches:
                print("Nenhum elemento 'event__match' encontrado no Flashscore")
                return "Não há resultados recentes disponíveis no Flashscore.\n\nAcompanhe atualizações em: [Flashscore](https://www.flashscore.com/team/furia/6z2eC9tF/results/)"

            results_text = "✅ Últimos resultados da FURIA (via Flashscore):\n\n"
            for match in matches:
                # Extrai a data
                date_div = match.find('div', class_='event__time')
                if not date_div:
                    print("Elemento de data não encontrado em um resultado")
                    date = "Data não disponível"
                else:
                    date = date_div.text.strip().split(' ')[0]  # Formato: "DD.MM. HH:MM" -> "DD.MM."

                # Extrai os times
                team1_div = match.find('div', class_='event__participant--home')
                team2_div = match.find('div', class_='event__participant--away')
                if not team1_div or not team2_div:
                    print("Elemento de times não encontrado")
                    continue
                team1 = team1_div.text.strip()
                team2 = team2_div.text.strip()

                # Extrai o placar
                score_div = match.find('div', class_='event__scores')
                if not score_div:
                    print("Elemento de placar não encontrado")
                    continue
                scores = score_div.find_all('span')
                if len(scores) < 2:
                    print("Placar incompleto encontrado")
                    continue
                score1 = scores[0].text.strip()
                score2 = scores[1].text.strip()
                score = f"{score1} - {score2}"

                # Determina o oponente e ajusta o placar
                if team1.lower() == "furia":
                    opponent = team2
                    score_display = score
                else:
                    opponent = team1
                    score_display = f"{score2} - {score1}"  # Inverte o placar

                # O Flashscore não fornece o nome do evento diretamente na página de resultados
                event = "Evento não disponível"

                results_text += f"- {date}: FURIA {score_display} {opponent} | {event}\n"

            if results_text == "✅ Últimos resultados da FURIA (via Flashscore):\n\n":
                print("Nenhum resultado válido foi extraído do Flashscore")
                return "Não há resultados recentes disponíveis no Flashscore.\n\nAcompanhe atualizações em: [Flashscore](https://www.flashscore.com/team/furia/6z2eC9tF/results/)"

            return results_text
        except requests.exceptions.HTTPError as e:
            print(f"Erro HTTP ao buscar resultados no Flashscore: {str(e)}")
            if e.response.status_code == 403:
                print("Acesso bloqueado pelo Flashscore (403 Forbidden)")
                return "⚠️ O Flashscore bloqueou o acesso. Tente novamente mais tarde.\nAcompanhe atualizações em: [Flashscore](https://www.flashscore.com/team/furia/6z2eC9tF/results/)"
            elif e.response.status_code == 429:
                print("Limite de requisições excedido no Flashscore (429 Too Many Requests)")
                if attempt < 2:  # Não espera na última tentativa
                    wait_time = (attempt + 1) * 5  # Espera 5s, 10s, 15s
                    print(f"Aguardando {wait_time} segundos antes de tentar novamente...")
                    time.sleep(wait_time)
                    continue
            return "⚠️ Não foi possível buscar os resultados recentes no Flashscore.\nAcompanhe atualizações em: [Flashscore](https://www.flashscore.com/team/furia/6z2eC9tF/results/)"
        except requests.exceptions.RequestException as e:
            print(f"Erro de requisição ao buscar resultados no Flashscore: {str(e)}")
            if attempt < 2:  # Não espera na última tentativa
                wait_time = (attempt + 1) * 5
                print(f"Aguardando {wait_time} segundos antes de tentar novamente...")
                time.sleep(wait_time)
                continue
            return "⚠️ Não foi possível buscar os resultados recentes no Flashscore.\nAcompanhe atualizações em: [Flashscore](https://www.flashscore.com/team/furia/6z2eC9tF/results/)"
        except Exception as e:
            print(f"Erro inesperado ao buscar resultados no Flashscore: {str(e)}")
            return "⚠️ Não foi possível buscar os resultados recentes no Flashscore.\nAcompanhe atualizações em: [Flashscore](https://www.flashscore.com/team/furia/6z2eC9tF/results/)"

# Função para buscar próximos jogos do Flashscore (fallback)
def get_upcoming_matches_flashscore():
    for attempt in range(3):  # Tenta até 3 vezes
        try:
            # URL da página de resultados da FURIA no Flashscore (também contém jogos futuros)
            url = "https://www.flashscore.com/team/furia/6z2eC9tF/results/"
            print(f"Tentativa {attempt + 1}/3 de buscar próximos jogos no Flashscore")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            print("Resposta recebida do Flashscore com sucesso.")
            soup = BeautifulSoup(response.text, 'html.parser')

            # Log do HTML para depuração
            print("HTML recebido (primeiros 500 caracteres):")
            print(str(soup)[:500])

            # Encontra os próximos jogos (elementos com classe 'event__match' e sem placar)
            matches = soup.find_all('div', class_='event__match')[:3]  # Limita a 3 jogos
            if not matches:
                print("Nenhum elemento 'event__match' encontrado no Flashscore")
                return "Atualmente, não há partidas futuras agendadas para a FURIA no Flashscore.\n\nAcompanhe atualizações em: [Flashscore](https://www.flashscore.com/team/furia/6z2eC9tF/results/)"

            matches_text = "📅 Próximos jogos da FURIA (via Flashscore):\n\n"
            has_upcoming = False
            for match in matches:
                # Verifica se é um jogo futuro (sem placar)
                score_div = match.find('div', class_='event__scores')
                if score_div and score_div.find('span'):  # Se há placar, é um jogo passado
                    continue

                # Extrai a data
                date_div = match.find('div', class_='event__time')
                if not date_div:
                    print("Elemento de data não encontrado em um jogo futuro")
                    date = "Data não disponível"
                else:
                    date = date_div.text.strip()  # Formato: "DD.MM. HH:MM"

                # Extrai os times
                team1_div = match.find('div', class_='event__participant--home')
                team2_div = match.find('div', class_='event__participant--away')
                if not team1_div or not team2_div:
                    print("Elemento de times não encontrado")
                    continue
                team1 = team1_div.text.strip()
                team2 = team2_div.text.strip()

                # Determina o oponente
                if team1.lower() == "furia":
                    opponent = team2
                else:
                    opponent = team1

                # O Flashscore não fornece o nome do evento diretamente na página de resultados
                event = "Evento não disponível"

                matches_text += f"- FURIA vs {opponent} | {date} | {event}\n"
                has_upcoming = True

            if has_upcoming:
                return matches_text
            else:
                print("Nenhum jogo futuro válido foi extraído do Flashscore")
                return "Atualmente, não há partidas futuras agendadas para a FURIA no Flashscore.\n\nAcompanhe atualizações em: [Flashscore](https://www.flashscore.com/team/furia/6z2eC9tF/results/)"

        except requests.exceptions.HTTPError as e:
            print(f"Erro HTTP ao buscar próximos jogos no Flashscore: {str(e)}")
            if e.response.status_code == 403:
                print("Acesso bloqueado pelo Flashscore (403 Forbidden)")
                return "⚠️ O Flashscore bloqueou o acesso. Tente novamente mais tarde.\nAcompanhe atualizações em: [Flashscore](https://www.flashscore.com/team/furia/6z2eC9tF/results/)"
            elif e.response.status_code == 429:
                print("Limite de requisições excedido no Flashscore (429 Too Many Requests)")
                if attempt < 2:  # Não espera na última tentativa
                    wait_time = (attempt + 1) * 5  # Espera 5s, 10s, 15s
                    print(f"Aguardando {wait_time} segundos antes de tentar novamente...")
                    time.sleep(wait_time)
                    continue
            return "⚠️ Não foi possível buscar os próximos jogos no Flashscore.\nAcompanhe atualizações em: [Flashscore](https://www.flashscore.com/team/furia/6z2eC9tF/results/)"
        except requests.exceptions.RequestException as e:
            print(f"Erro de requisição ao buscar próximos jogos no Flashscore: {str(e)}")
            if attempt < 2:  # Não espera na última tentativa
                wait_time = (attempt + 1) * 5
                print(f"Aguardando {wait_time} segundos antes de tentar novamente...")
                time.sleep(wait_time)
                continue
            return "⚠️ Não foi possível buscar os próximos jogos no Flashscore.\nAcompanhe atualizações em: [Flashscore](https://www.flashscore.com/team/furia/6z2eC9tF/results/)"
        except Exception as e:
            print(f"Erro inesperado ao buscar próximos jogos no Flashscore: {str(e)}")
            return "⚠️ Não foi possível buscar os próximos jogos no Flashscore.\nAcompanhe atualizações em: [Flashscore](https://www.flashscore.com/team/furia/6z2eC9tF/results/)"

# Função para buscar Últimos Resultados usando a PandaScore
def get_recent_results():
    # Verifica se o cache está válido
    if is_cache_valid(cache["recent_results"]):
        print("Usando cache para resultados recentes")
        return cache["recent_results"]["data"]

    # Tenta a requisição com reintentativas para erro 429
    for attempt in range(3):
        try:
            url = f"https://api.pandascore.co/csgo/matches/past?filter[opponent_id]={FURIA_ID}&sort=-begin_at&per_page=10&token={PANDASCORE_API_KEY}"
            response = requests.get(url)
            response.raise_for_status()
            matches = response.json()

            if not matches:
                print("Nenhuma partida encontrada na PandaScore, usando fallback Flashscore")
                result = get_recent_results_flashscore()
            else:
                results_text = "✅ Últimos resultados da FURIA:\n\n"
                all_invalid = True  # Flag para verificar se todos os resultados são inválidos
                for match in matches[:4]:  # Limita a 4 resultados
                    # Log para depuração
                    print(f"Partida {match['id']}: begin_at={match['begin_at']}, results={match['results']}")
                    
                    opponent = match['opponents'][1]['opponent']['name'] if match['opponents'][0]['opponent']['id'] == FURIA_ID else match['opponents'][0]['opponent']['name']
                    event = match['league']['name']
                    
                    # Verifica se begin_at é None
                    if match['begin_at'] is None:
                        date = "Data não disponível"
                    else:
                        date = datetime.strptime(match['begin_at'], "%Y-%m-%dT%H:%M:%SZ").strftime("%d/%m/%Y")
                        all_invalid = False  # Pelo menos uma partida tem data válida
                    
                    # Verifica o placar com mais cuidado
                    if match.get('results') and len(match['results']) == 2 and all('score' in team for team in match['results']):
                        score1 = match['results'][0]['score'] if match['results'][0]['score'] is not None else 0
                        score2 = match['results'][1]['score'] if match['results'][1]['score'] is not None else 0
                        if score1 == 0 and score2 == 0:
                            score = "N/A"
                        else:
                            score = f"{score1} : {score2}"
                            all_invalid = False  # Pelo menos uma partida tem placar válido
                    else:
                        score = "N/A"
                    
                    results_text += f"- {date}: FURIA {score} {opponent} | {event}\n"
                
                # Se todos os resultados forem inválidos (sem data e sem placar), usa o fallback
                if all_invalid:
                    print("Todos os resultados da PandaScore são inválidos, usando fallback Flashscore")
                    result = get_recent_results_flashscore()
                else:
                    result = results_text

            # Atualiza o cache
            cache["recent_results"]["data"] = result
            cache["recent_results"]["timestamp"] = datetime.utcnow()
            return result
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Too Many Requests
                wait_time = (attempt + 1) * 10  # Espera: 10s, 20s, 30s
                print(f"Limite de requisições excedido. Tentativa {attempt + 1}/3. Aguardando {wait_time} segundos...")
                time.sleep(wait_time)
                continue
            print(f"Erro ao buscar resultados recentes na PandaScore, usando fallback Flashscore: {str(e)}")
            result = get_recent_results_flashscore()
            cache["recent_results"]["data"] = result
            cache["recent_results"]["timestamp"] = datetime.utcnow()
            return result
        except Exception as e:
            print(f"Erro ao buscar resultados recentes na PandaScore, usando fallback Flashscore: {str(e)}")
            result = get_recent_results_flashscore()
            cache["recent_results"]["data"] = result
            cache["recent_results"]["timestamp"] = datetime.utcnow()
            return result

# Função para buscar Próximos Jogos usando a PandaScore, com fallback para Flashscore
def get_upcoming_matches():
    # Verifica se o cache está válido
    if is_cache_valid(cache["upcoming_matches"]):
        print("Usando cache para próximos jogos")
        return cache["upcoming_matches"]["data"]

    # Tenta a requisição com reintentativas para erro 429
    for attempt in range(3):
        try:
            url = f"https://api.pandascore.co/csgo/matches/upcoming?filter[opponent_id]={FURIA_ID}&sort=begin_at&per_page=10&token={PANDASCORE_API_KEY}"
            response = requests.get(url)
            response.raise_for_status()
            matches = response.json()

            if not matches:
                print("Nenhuma partida futura encontrada na PandaScore, usando fallback Flashscore")
                result = get_upcoming_matches_flashscore()
            else:
                matches_text = "📅 Próximos jogos da FURIA:\n\n"
                all_invalid = True  # Flag para verificar se todos os jogos são inválidos
                for match in matches[:3]:  # Limita a 3 partidas
                    opponent = match['opponents'][1]['opponent']['name'] if match['opponents'][0]['opponent']['id'] == FURIA_ID else match['opponents'][0]['opponent']['name']
                    # Verifica se begin_at é None
                    if match['begin_at'] is None:
                        date = "Data não disponível"
                    else:
                        date = datetime.strptime(match['begin_at'], "%Y-%m-%dT%H:%M:%SZ").strftime("%d/%m/%Y %H:%M UTC")
                        all_invalid = False  # Pelo menos um jogo tem data válida
                    event = match['league']['name']
                    matches_text += f"- FURIA vs {opponent} | {date} | {event}\n"
                
                # Se todos os jogos forem inválidos (sem data), usa o fallback
                if all_invalid:
                    print("Todos os jogos futuros da PandaScore são inválidos, usando fallback Flashscore")
                    result = get_upcoming_matches_flashscore()
                else:
                    result = matches_text

            # Atualiza o cache
            cache["upcoming_matches"]["data"] = result
            cache["upcoming_matches"]["timestamp"] = datetime.utcnow()
            return result
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Too Many Requests
                wait_time = (attempt + 1) * 10  # Espera: 10s, 20s, 30s
                print(f"Limite de requisições excedido. Tentativa {attempt + 1}/3. Aguardando {wait_time} segundos...")
                time.sleep(wait_time)
                continue
            print(f"Erro ao buscar próximos jogos na PandaScore, usando fallback Flashscore: {str(e)}")
            result = get_upcoming_matches_flashscore()
            cache["upcoming_matches"]["data"] = result
            cache["upcoming_matches"]["timestamp"] = datetime.utcnow()
            return result
        except Exception as e:
            print(f"Erro ao buscar próximos jogos na PandaScore, usando fallback Flashscore: {str(e)}")
            result = get_upcoming_matches_flashscore()
            cache["upcoming_matches"]["data"] = result
            cache["upcoming_matches"]["timestamp"] = datetime.utcnow()
            return result

# Função para verificar e notificar sobre próximos jogos
async def check_upcoming_matches():
    while True:
        try:
            # Verifica se NOTIFICATION_CHANNEL_ID está definido
            if NOTIFICATION_CHANNEL_ID is None:
                print("NOTIFICATION_CHANNEL_ID não está definido. Notificações automáticas desativadas.")
                await asyncio.sleep(21600)  # Verifica a cada 6 horas
                continue

            # Usa a função get_upcoming_matches para aproveitar o cache
            upcoming_matches_text = get_upcoming_matches()
            # Verifica se há jogos no cache
            if "Atualmente, não há partidas futuras agendadas" in upcoming_matches_text:
                print("Nenhum jogo futuro encontrado.")
                await asyncio.sleep(21600)  # Verifica a cada 6 horas
                continue

            channel = client.get_channel(NOTIFICATION_CHANNEL_ID)
            if not channel:
                print(f"Canal de notificação {NOTIFICATION_CHANNEL_ID} não encontrado.")
                await asyncio.sleep(21600)
                continue

            # Faz uma nova requisição para obter os dados brutos (necessário para notificações)
            url = f"https://api.pandascore.co/csgo/matches/upcoming?filter[opponent_id]={FURIA_ID}&sort=begin_at&per_page=10&token={PANDASCORE_API_KEY}"
            response = requests.get(url)
            response.raise_for_status()
            matches = response.json()

            for match in matches:
                match_id = match['id']
                if match_id in notified_matches:
                    continue  # Pula jogos já notificados

                # Obtém a data do jogo
                if match['begin_at'] is None:
                    print(f"Partida {match_id} não tem data definida, pulando notificação.")
                    continue  # Pula partidas sem data

                match_time = datetime.strptime(match['begin_at'], "%Y-%m-%dT%H:%M:%SZ")
                now = datetime.utcnow()
                time_until_match = match_time - now

                # Notifica se o jogo for nas próximas 24 horas
                if 0 < time_until_match.total_seconds() <= 86400:  # 24 horas em segundos
                    opponent = match['opponents'][1]['opponent']['name'] if match['opponents'][0]['opponent']['id'] == FURIA_ID else match['opponents'][0]['opponent']['name']
                    event = match['league']['name']
                    date = match_time.strftime("%d/%m/%Y %H:%M UTC")
                    notification_message = (
                        f"@Notificações FURIA\n"
                        f"📅 Jogo da FURIA em breve!\n"
                        f"FURIA vs {opponent} | {date} | {event}\n"
                        f"Acompanhe em: [Flashscore](https://www.flashscore.com/team/furia/6z2eC9tF/results/)"
                    )
                    await channel.send(notification_message)
                    notified_matches.append(match_id)
                    print(f"Notificação enviada para o jogo {match_id}")

            # Limpa jogos antigos da lista de notificados
            notified_matches[:] = [match_id for match_id in notified_matches if match_id in [m['id'] for m in matches]]

        except Exception as e:
            print(f"Erro ao verificar próximos jogos: {str(e)}")
            # Se houver erro na PandaScore, não tentamos Flashscore aqui, pois get_upcoming_matches() já lida com isso
        
        await asyncio.sleep(21600)  # Verifica a cada 6 horas

# Evento que é chamado quando o bot está pronto
@client.event
async def on_ready():
    print(f'Bot connected as {client.user}')
    # Valida o token da API na inicialização
    if not validate_api_token():
        print("Atenção: O bot pode não funcionar corretamente devido a problemas com o token da API.")
    try:
        synced = await tree.sync()
        print(f'Commands synced: {synced}')
    except Exception as e:
        print(f'Error syncing commands: {e}')
    
    # Inicia a verificação de jogos em segundo plano
    client.loop.create_task(check_upcoming_matches())

# Comando /start
@tree.command(name="start", description="Inicia o bot da FURIA")
async def start(interaction: discord.Interaction):
    # Cria os botões
    jogos_button = Button(label="📅 Próximos Jogos", style=ButtonStyle.primary, custom_id="jogos")
    resultados_button = Button(label="✅ Últimos Resultados", style=ButtonStyle.primary, custom_id="resultados")
    lineup_button = Button(label="🧩 Conheça nossa Line-up", style=ButtonStyle.primary, custom_id="lineup")
    redes_button = Button(label="🌐 Redes Sociais", style=ButtonStyle.primary, custom_id="redes")
    notificacoes_button = Button(label="🔔 Ativar Notificações", style=ButtonStyle.primary, custom_id="notificacoes")

    # Cria a view e adiciona os botões
    view = View()
    view.add_item(jogos_button)
    view.add_item(resultados_button)
    view.add_item(lineup_button)
    view.add_item(redes_button)
    view.add_item(notificacoes_button)

    # Envia a mensagem com os botões
    await interaction.response.send_message("🐾 FALA, FURIOSO(A)! Escolha uma opção abaixo:", view=view)

# Handler para interações com botões
@client.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type != discord.InteractionType.component:
        return

    custom_id = interaction.data['custom_id'] if 'custom_id' in interaction.data else None

    # Botão "Voltar"
    back_button = Button(label="⬅️ Voltar", style=ButtonStyle.secondary, custom_id="voltar")
    back_view = View()
    back_view.add_item(back_button)

    if custom_id == "jogos":
        # Diferir a resposta para evitar timeout
        await interaction.response.defer()
        upcoming_matches = get_upcoming_matches()
        await interaction.edit_original_response(
            content=upcoming_matches,
            view=back_view
        )
    elif custom_id == "resultados":
        # Diferir a resposta para evitar timeout
        await interaction.response.defer()
        recent_results = get_recent_results()
        await interaction.edit_original_response(
            content=recent_results,
            view=back_view
        )
    elif custom_id == "lineup":
        await interaction.response.edit_message(
            content="🧩 Conheça a line-up atual da FURIA:\n\n"
                    "🎯 KSCERATO: Rifler técnico e referência de consistência.\n"
                    "🔥 yuurih: Rifler versátil e extremamente confiável.\n"
                    "🎓 FalleN: Lenda brasileira, agora rifler e IGL da equipe.\n"
                    "🧊 molodoy: AWPer do Cazaquistão, jovem promessa no cenário internacional.\n"
                    "⚡ YEKINDAR: Rifler agressivo da Letônia, trazendo experiência internacional.\n"
                    "🛡️ skullz: Rifler brasileiro, nova adição ao time.\n"
                    "🧠 guerri: Coach e estrategista da FURIA.",
            view=back_view
        )
    elif custom_id == "redes":
        await interaction.response.edit_message(
            content="🌐 Redes Sociais da FURIA:\n\n"
                    "🐦 [Twitter](https://twitter.com/FURIA)\n"
                    "▶️ [YouTube](https://youtube.com/@furiaggcs?si=xtcq9u5MZGFzg2G-)\n"
                    "📸 [Instagram](https://www.instagram.com/furiagg/)\n"
                    "🛒 [Loja Oficial](https://store.furia.gg/)",
            view=back_view
        )
    elif custom_id == "notificacoes":
        # Botões para ativar/desativar notificações
        ativar_button = Button(label="Ativar Notificações", style=ButtonStyle.green, custom_id="ativar_notificacoes")
        desativar_button = Button(label="Desativar Notificações", style=ButtonStyle.red, custom_id="desativar_notificacoes")
        notificacoes_view = View()
        notificacoes_view.add_item(ativar_button)
        notificacoes_view.add_item(desativar_button)
        notificacoes_view.add_item(back_button)

        await interaction.response.edit_message(
            content="🔔 Notificações de Jogos:\n\nVocê gostaria de receber notificações para os próximos jogos da FURIA?",
            view=notificacoes_view
        )
    elif custom_id == "ativar_notificacoes":
        role = discord.utils.get(interaction.guild.roles, name="Notificações FURIA")
        if not role:
            role = await interaction.guild.create_role(name="Notificações FURIA", mentionable=True)
        if role not in interaction.user.roles:
            await interaction.user.add_roles(role)
            await interaction.response.edit_message(
                content="🔔 Notificações ativadas! Você será avisado sobre os próximos jogos da FURIA.",
                view=back_view
            )
        else:
            await interaction.response.edit_message(
                content="🔔 Você já tem as notificações ativadas!",
                view=back_view
            )
    elif custom_id == "desativar_notificacoes":
        role = discord.utils.get(interaction.guild.roles, name="Notificações FURIA")
        if role and role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.edit_message(
                content="🔔 Notificações desativadas! Você não será mais avisado sobre os próximos jogos da FURIA.",
                view=back_view
            )
        else:
            await interaction.response.edit_message(
                content="🔔 Você não tem as notificações ativadas!",
                view=back_view
            )
    elif custom_id == "voltar":
        jogos_button = Button(label="📅 Próximos Jogos", style=ButtonStyle.primary, custom_id="jogos")
        resultados_button = Button(label="✅ Últimos Resultados", style=ButtonStyle.primary, custom_id="resultados")
        lineup_button = Button(label="🧩 Conheça nossa Line-up", style=ButtonStyle.primary, custom_id="lineup")
        redes_button = Button(label="🌐 Redes Sociais", style=ButtonStyle.primary, custom_id="redes")
        notificacoes_button = Button(label="🔔 Ativar Notificações", style=ButtonStyle.primary, custom_id="notificacoes")

        view = View()
        view.add_item(jogos_button)
        view.add_item(resultados_button)
        view.add_item(lineup_button)
        view.add_item(redes_button)
        view.add_item(notificacoes_button)

        await interaction.response.edit_message(
            content="🐾 FALA, FURIOSO(A)! Escolha uma opção abaixo:",
            view=view
        )

# Endpoint de health check para evitar inatividade no Render
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

def start_health_check_server():
    port = int(os.getenv("PORT", 8000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"Health check server running on port {port}")
    server.serve_forever()

# Inicia o servidor de health check em uma thread separada
print("Iniciando servidor de health check...")
threading.Thread(target=start_health_check_server, daemon=True).start()

# Obtém o token do bot a partir das variáveis de ambiente
print("Obtendo DISCORD_BOT_TOKEN...")
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if not TOKEN:
    print("Erro: DISCORD_BOT_TOKEN não encontrado nas variáveis de ambiente.")
    raise ValueError("DISCORD_BOT_TOKEN not found in environment variables")
else:
    print("DISCORD_BOT_TOKEN encontrado com sucesso.")

# Inicia o bot
if __name__ == "__main__":
    print("Iniciando o bot com client.run()...")
    try:
        client.run(TOKEN)
    except Exception as e:
        print(f"Erro ao iniciar o bot: {str(e)}")
        raise
