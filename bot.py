import discord
from discord import app_commands, ButtonStyle
from discord.ui import Button, View
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

print("Iniciando bot.py...")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Views reutilizáveis
class MenuView(View):
    def __init__(self):
        super().__init__()
        self.add_item(Button(label="📅 Próximos Jogos", style=ButtonStyle.primary, custom_id="jogos"))
        self.add_item(Button(label="✅ Últimos Resultados", style=ButtonStyle.primary, custom_id="resultados"))
        self.add_item(Button(label="🧩 Conheça nossa Line-up", style=ButtonStyle.primary, custom_id="lineup"))
        self.add_item(Button(label="🌐 Redes Sociais", style=ButtonStyle.primary, custom_id="redes"))

class VoltarView(View):
    def __init__(self):
        super().__init__()
        self.add_item(Button(label="⬅️ Voltar", style=ButtonStyle.secondary, custom_id="voltar"))

# Evento ao iniciar o bot
@client.event
async def on_ready():
    print(f'Bot conectado como {client.user}')
    try:
        synced = await tree.sync()
        print(f'Comandos sincronizados: {synced}')
    except Exception as e:
        print(f'Erro ao sincronizar comandos: {e}')

# Comando /start
@tree.command(name="start", description="Inicia o bot da FURIA")
async def start(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🐾 FALA, FURIOSO(A)! Escolha uma opção abaixo:",
        view=MenuView()
    )

# Evento para interações com botões
@client.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type != discord.InteractionType.component:
        return

    custom_id = interaction.data.get("custom_id")

    if custom_id == "jogos":
        await interaction.response.edit_message(
            content="📅 **Próximos Jogos da FURIA**\n\n"
                    "Acesse:\n"
                    "🔗 [Próximos jogos no HLTV.org](https://www.hltv.org/team/8297/furia#tab-matchesBox)",
            view=VoltarView()
        )
    elif custom_id == "resultados":
        await interaction.response.edit_message(
            content="✅ **Últimos Resultados da FURIA**\n\n"
                    "Acesse:\n"
                    "🔗 [Últimos resultados no HLTV.org](https://www.hltv.org/team/8297/furia#tab-matchesBox)",
            view=VoltarView()
        )
    elif custom_id == "lineup":
        await interaction.response.edit_message(
            content="🧩 **Line-up atual da FURIA:**\n\n"
                    "🎯 **KSCERATO**: Rifler técnico e referência de consistência.\n"
                    "   [Twitch](https://www.twitch.tv/kscerato) | [Twitter](https://twitter.com/kscerato)\n\n"
                    "🔥 **yuurih**: Rifler versátil e extremamente confiável.\n"
                    "   [Twitch](https://www.twitch.tv/yuurih) | [Twitter](https://x.com/yuurih)\n\n"
                    "🎓 **FalleN**: Lenda brasileira, agora rifler e IGL da equipe.\n"
                    "   [Twitter](https://twitter.com/FalleNCS)\n\n"
                    "🧊 **molodoy**: AWPer do Cazaquistão, jovem promessa no cenário internacional.\n"
                    "   [Twitter](https://twitter.com/tvoy_molodoy)\n\n"
                    "⚡ **YEKINDAR**: Rifler agressivo da Letônia, trazendo experiência internacional.\n"
                    "   [Twitch](https://www.twitch.tv/yekindar) | [Twitter](https://twitter.com/yek1ndar)\n\n"
                    "🧠 **Lucid**: Coach e estrategista da FURIA.",
            view=VoltarView()
        )
    elif custom_id == "redes":
        await interaction.response.edit_message(
            content="🌐 **Redes Oficiais da FURIA:**\n\n"
                    "🐾 **Redes Gerais:**\n"
                    "🐦 [Twitter](https://twitter.com/FURIA)\n"
                    "▶️ [YouTube Principal](https://youtube.com/@furiagg?si=jhP3YWT30dE8d_Kx)\n"
                    "📸 [Instagram](https://www.instagram.com/furiagg/)\n\n"
                    "🎯 **CS:GO:**\n"
                    "▶️ [YouTube CS](https://www.youtube.com/@furiaggcs)\n"
                    "📺 [FURIA TV no Twitch](https://www.twitch.tv/furiatv)\n\n"
                    "🛒 **Loja Oficial:**\n"
                    "🛒 [Store FURIA](https://store.furia.gg/)\n",
            view=VoltarView()
        )
    elif custom_id == "voltar":
        await interaction.response.edit_message(
            content="🐾 FALA, FURIOSO(A)! Escolha uma opção abaixo:",
            view=MenuView()
        )

# Servidor HTTP para evitar inatividade no Render
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

def start_health_check_server():
    port = int(os.getenv("PORT", 8000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"Servidor de health check rodando na porta {port}")
    server.serve_forever()

threading.Thread(target=start_health_check_server, daemon=True).start()

# Rodar bot
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not TOKEN:
    raise ValueError("Erro: DISCORD_BOT_TOKEN não encontrado nas variáveis de ambiente.")
else:
    print("Token encontrado. Iniciando bot...")
    client.run(TOKEN)
