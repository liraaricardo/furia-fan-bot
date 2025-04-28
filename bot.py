import discord
from discord import app_commands, ButtonStyle
from discord.ui import Button, View
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

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

# Evento que é chamado quando o bot está pronto
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
        await interaction.response.edit_message(
            content="📅 **Próximos Jogos da FURIA**\n\n"
                    "Para ver os próximos jogos, acesse o site HLTV.org:\n"
                    "🔗 [Acompanhe os jogos da FURIA no HLTV.org](https://www.hltv.org/team/8297/furia#tab-matchesBox)",
            view=back_view
        )
    elif custom_id == "resultados":
        await interaction.response.edit_message(
            content="✅ **Últimos Resultados da FURIA**\n\n"
                    "Para ver os últimos resultados, acesse o site HLTV.org:\n"
                    "🔗 [Acompanhe os jogos da FURIA no HLTV.org](https://www.hltv.org/team/8297/furia#tab-matchesBox)",
            view=back_view
        )
    elif custom_id == "lineup":
        await interaction.response.edit_message(
            content="🧩 **Conheça a line-up atual da FURIA:**\n\n"
                    "🎯 **KSCERATO**: Rifler técnico e referência de consistência.\n"
                    "   [Twitch](https://www.twitch.tv/kscerato) | [Twitter](https://twitter.com/kscerato)\n\n"
                    "🔥 **yuurih**: Rifler versátil e extremamente confiável.\n"
                    "   [Twitch](https://www.twitch.tv/yuurih) | [Twitter](https://twitter.com/yuurihfps)\n\n"
                    "🎓 **FalleN**: Lenda brasileira, agora rifler e IGL da equipe.\n"
                    "   [Twitch](https://www.twitch.tv/fallen) | [Twitter](https://twitter.com/FalleNCS)\n\n"
                    "🧊 **molodoy**: AWPer do Cazaquistão, jovem promessa no cenário internacional.\n"
                    "   [Twitter](https://twitter.com/tvoy_molodoy)\n\n"
                    "⚡ **YEKINDAR**: Rifler agressivo da Letônia, trazendo experiência internacional.\n"
                    "   [Twitch](https://www.twitch.tv/yekindar) | [Twitter](https://twitter.com/yek1ndar)\n\n"
                    "🧠 **Lucid**: Coach e estrategista da FURIA.\n",
            view=back_view
        )
    elif custom_id == "redes":
        await interaction.response.edit_message(
            content="🌐 **Redes Oficiais da FURIA:**\n\n"
                    "🐾 **Redes Gerais:**\n"
                    "🐦 [Twitter](https://twitter.com/FURIA)\n"
                    "▶️ [YouTube Principal](https://www.youtube.com/@FURIA)\n"
                    "📸 [Instagram](https://www.instagram.com/furiagg/)\n\n"
                    "🎯 **CS:GO:**\n"
                    "▶️ [YouTube CS](https://www.youtube.com/@furiaggcs)\n"
                    "📺 [FURIA TV no Twitch](https://www.twitch.tv/furiatv)\n\n"
                    "🛒 **Loja Oficial:**\n"
                    "🛒 [Store FURIA](https://store.furia.gg/)\n",
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
    print(f"Servidor de health check rodando na porta {port}")
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




