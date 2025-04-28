import discord
from discord import app_commands, ButtonStyle
from discord.ui import Button, View
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# Configura os intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Inicializa o cliente do Discord
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

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
    twitter_button = Button(label="🐦 Twitter", style=ButtonStyle.link, url="https://twitter.com/FURIA")
    youtube_button = Button(label="▶️ YouTube", style=ButtonStyle.link, url="https://youtube.com/@furiaggcs?si=xtcq9u5MZGFzg2G-")
    instagram_button = Button(label="📸 Instagram", style=ButtonStyle.link, url="https://www.instagram.com/furiagg/")
    loja_button = Button(label="🛒 Loja Oficial", style=ButtonStyle.link, url="https://store.furia.gg/")

    # Cria a view e adiciona os botões
    view = View()
    view.add_item(jogos_button)
    view.add_item(resultados_button)
    view.add_item(lineup_button)
    view.add_item(twitter_button)
    view.add_item(youtube_button)
    view.add_item(instagram_button)
    view.add_item(loja_button)

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
        await interaction.response.edit_message(
            content="📅 Próximos jogos da FURIA:\n\n"
                    "Atualmente, não há partidas futuras agendadas para a FURIA.\n\n"
                    "Acompanhe atualizações em: [HLTV.org](https://www.hltv.org/team/8297/furia)",
            view=back_view
        )
    elif custom_id == "resultados":
        await interaction.response.edit_message(
            content="✅ Últimos resultados da FURIA:\n\n"
                    "- FURIA 2×0 Legacy (IEM Dallas 2025)\n"
                    "- FURIA 0×2 Team Liquid (IEM Dallas 2025)\n"
                    "- FURIA 1×2 G2 Esports (ESL Pro League 2025)",
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
    elif custom_id == "voltar":
        jogos_button = Button(label="📅 Próximos Jogos", style=ButtonStyle.primary, custom_id="jogos")
        resultados_button = Button(label="✅ Últimos Resultados", style=ButtonStyle.primary, custom_id="resultados")
        lineup_button = Button(label="🧩 Conheça nossa Line-up", style=ButtonStyle.primary, custom_id="lineup")
        twitter_button = Button(label="🐦 Twitter", style=ButtonStyle.link, url="https://twitter.com/FURIA")
        youtube_button = Button(label="▶️ YouTube", style=ButtonStyle.link, url="https://youtube.com/@furiaggcs?si=xtcq9u5MZGFzg2G-")
        instagram_button = Button(label="📸 Instagram", style=ButtonStyle.link, url="https://www.instagram.com/furiagg/")
        loja_button = Button(label="🛒 Loja Oficial", style=ButtonStyle.link, url="https://store.furia.gg/")

        view = View()
        view.add_item(jogos_button)
        view.add_item(resultados_button)
        view.add_item(lineup_button)
        view.add_item(twitter_button)
        view.add_item(youtube_button)
        view.add_item(instagram_button)
        view.add_item(loja_button)

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
