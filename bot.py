import discord
from discord import app_commands, ButtonStyle
from discord.ui import Button, View
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
from bs4 import BeautifulSoup

# Configura os intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Inicializa o cliente do Discord
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Função para buscar Próximos Jogos da HLTV.org
def get_upcoming_matches():
    try:
        url = "https://www.hltv.org/team/8297/furia#tab-matchesBox"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        upcoming_matches = soup.find_all('div', class_='upcomingMatch')
        if not upcoming_matches:
            return "Atualmente, não há partidas futuras agendadas para a FURIA.\n\nAcompanhe atualizações em: [HLTV.org](https://www.hltv.org/team/8297/furia)"

        matches_text = "📅 Próximos jogos da FURIA:\n\n"
        for match in upcoming_matches[:3]:  # Limita a 3 partidas
            teams = match.find_all('div', class_='matchTeamName')
            if len(teams) < 2:
                continue
            opponent = teams[1].text.strip() if teams[1].text.strip() != "FURIA" else teams[0].text.strip()
            date = match.find('div', class_='matchTime').text.strip()
            event = match.find('div', class_='matchEventName').text.strip()
            matches_text += f"- FURIA vs {opponent} | {date} | {event}\n"
        return matches_text
    except Exception as e:
        return f"Erro ao buscar próximos jogos: {str(e)}\nAcompanhe atualizações em: [HLTV.org](https://www.hltv.org/team/8297/furia)"

# Função para buscar Últimos Resultados da HLTV.org
def get_recent_results():
    try:
        url = "https://www.hltv.org/team/8297/furia#tab-matchesBox"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        recent_results = soup.find_all('div', class_='pastMatch')
        if not recent_results:
            return "Não há resultados recentes disponíveis.\n\nAcompanhe atualizações em: [HLTV.org](https://www.hltv.org/team/8297/furia)"

        results_text = "✅ Últimos resultados da FURIA:\n\n"
        for result in recent_results[:3]:  # Limita a 3 resultados
            teams = result.find_all('div', class_='matchTeamName')
            if len(teams) < 2:
                continue
            opponent = teams[1].text.strip() if teams[1].text.strip() != "FURIA" else teams[0].text.strip()
            score = result.find('span', class_='matchScore').text.strip()
            event = result.find('div', class_='matchEventName').text.strip()
            results_text += f"- FURIA {score} {opponent} | {event}\n"
        return results_text
    except Exception as e:
        return f"Erro ao buscar resultados recentes: {str(e)}\nAcompanhe atualizações em: [HLTV.org](https://www.hltv.org/team/8297/furia)"

# Evento que é chamado quando o bot está pronto
@client.event
async def on_ready():
    print(f'Bot connected as {client.user}')
    try:
        synced = await tree.sync()
        print(f'Commands synced: {synced}')
    except Exception as e:
        print(f'Error syncing commands: {e}')

# Comando /start
@tree.command(name="start", description="Inicia o bot da FURIA")
async def start(interaction: discord.Interaction):
    # Cria os botões
    jogos_button = Button(label="📅 Próximos Jogos", style=ButtonStyle.primary, custom_id="jogos")
    resultados_button = Button(label="✅ Últimos Resultados", style=ButtonStyle.primary, custom_id="resultados")
    lineup_button = Button(label="🧩 Conheça nossa Line-up", style=ButtonStyle.primary, custom_id="lineup")
    redes_button = Button(label="🌐 Redes Sociais", style=ButtonStyle.primary, custom_id="redes")

    # Cria a view e adiciona os botões
    view = View()
    view.add_item(jogos_button)
    view.add_item(resultados_button)
    view.add_item(lineup_button)
    view.add_item(redes_button)

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
        upcoming_matches = get_upcoming_matches()
        await interaction.response.edit_message(
            content=upcoming_matches,
            view=back_view
        )
    elif custom_id == "resultados":
        recent_results = get_recent_results()
        await interaction.response.edit_message(
            content=recent_results,
            view=back_view
        )
    elif custom_id == "lineup":
        await interaction.response.edit_message(
            content="🧩 Conheça a line-up atual da FURIA:\n\n"
                    "🎯 KSCERATO: Rifler técnico e referência de consistência.\n"
                    "🔥 yuurih: Jogador versátil e extremamente confiável.\n"
                    "🎓 FalleN: Lenda brasileira, IGL e AWPer da equipe.\n"
                    "🧊 molodoy: Novo AWP da equipe, jovem promessa do Cazaquistão.\n"
                    "⚡ drop: Promessa brasileira, campeão da IEM Fall 2021.\n"
                    "🧠 GuerrI: Coach e estrategista da FURIA.",
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
    elif custom_id == "voltar":
        jogos_button = Button(label="📅 Próximos Jogos", style=ButtonStyle.primary, custom_id="jogos")
        resultados_button = Button(label="✅ Últimos Resultados", style=ButtonStyle.primary, custom_id="resultados")
        lineup_button = Button(label="🧩 Conheça nossa Line-up", style=ButtonStyle.primary, custom_id="lineup")
        redes_button = Button(label="🌐 Redes Sociais", style=ButtonStyle.primary, custom_id="redes")

        view = View()
        view.add_item(jogos_button)
        view.add_item(resultados_button)
        view.add_item(lineup_button)
        view.add_item(redes_button)

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
threading.Thread(target=start_health_check_server, daemon=True).start()

# Obtém o token do bot a partir das variáveis de ambiente
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if not TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN not found in environment variables")

# Inicia o bot
client.run(TOKEN)
