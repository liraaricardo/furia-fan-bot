import discord
from discord import app_commands, ButtonStyle
from discord.ui import Button, View
import os
import threading
import requests
import asyncio
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer

# Configura os intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Inicializa o cliente do Discord
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ID do time da FURIA na PandaScore
FURIA_ID = 8297
# Chave da API da PandaScore (obtida via variável de ambiente)
PANDASCORE_API_KEY = os.getenv("PANDASCORE_API_KEY")
if not PANDASCORE_API_KEY:
    raise ValueError("PANDASCORE_API_KEY not found in environment variables")
# Canal onde as notificações serão enviadas (obtida via variável de ambiente)
NOTIFICATION_CHANNEL_ID = int(os.getenv("NOTIFICATION_CHANNEL_ID", "123456789"))
# Lista para rastrear jogos já notificados (evitar notificações duplicadas)
notified_matches = []

# Função para buscar Próximos Jogos usando a PandaScore
def get_upcoming_matches():
    try:
        url = f"https://api.pandascore.co/csgo/matches/upcoming?filter[opponent_id]={FURIA_ID}&token={PANDASCORE_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        matches = response.json()

        if not matches:
            return "Atualmente, não há partidas futuras agendadas para a FURIA.\n\nAcompanhe atualizações em: [HLTV.org](https://www.hltv.org/team/8297/furia)"

        matches_text = "📅 Próximos jogos da FURIA:\n\n"
        for match in matches[:3]:  # Limita a 3 partidas
            opponent = match['opponents'][1]['opponent']['name'] if match['opponents'][0]['opponent']['id'] == FURIA_ID else match['opponents'][0]['opponent']['name']
            date = datetime.strptime(match['begin_at'], "%Y-%m-%dT%H:%M:%SZ").strftime("%d/%m/%Y %H:%M UTC")
            event = match['league']['name']
            matches_text += f"- FURIA vs {opponent} | {date} | {event}\n"
        return matches_text
    except Exception as e:
        return f"⚠️ Não foi possível buscar os próximos jogos no momento.\nAcompanhe atualizações em: [HLTV.org](https://www.hltv.org/team/8297/furia)"

# Função para buscar Últimos Resultados usando a PandaScore
def get_recent_results():
    try:
        url = f"https://api.pandascore.co/csgo/matches/past?filter[opponent_id]={FURIA_ID}&token={PANDASCORE_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        matches = response.json()

        if not matches:
            return "Não há resultados recentes disponíveis.\n\nAcompanhe atualizações em: [HLTV.org](https://www.hltv.org/team/8297/furia)"

        results_text = "✅ Últimos resultados da FURIA:\n\n"
        for match in matches[:4]:  # Limita a 4 resultados
            opponent = match['opponents'][1]['opponent']['name'] if match['opponents'][0]['opponent']['id'] == FURIA_ID else match['opponents'][0]['opponent']['name']
            score = f"{match['results'][0]['score']} : {match['results'][1]['score']}" if match['results'] else "N/A"
            event = match['league']['name']
            date = datetime.strptime(match['begin_at'], "%Y-%m-%dT%H:%M:%SZ").strftime("%d/%m/%Y")
            results_text += f"- {date}: FURIA {score} {opponent} | {event}\n"
        return results_text
    except Exception as e:
        return f"⚠️ Não foi possível buscar os resultados recentes no momento.\nAcompanhe atualizações em: [HLTV.org](https://www.hltv.org/team/8297/furia)"

# Função para verificar e notificar sobre próximos jogos
async def check_upcoming_matches():
    while True:
        try:
            url = f"https://api.pandascore.co/csgo/matches/upcoming?filter[opponent_id]={FURIA_ID}&token={PANDASCORE_API_KEY}"
            response = requests.get(url)
            response.raise_for_status()
            matches = response.json()

            if not matches:
                print("Nenhum jogo futuro encontrado.")
                await asyncio.sleep(3600)  # Verifica a cada hora
                continue

            channel = client.get_channel(NOTIFICATION_CHANNEL_ID)
            if not channel:
                print(f"Canal de notificação {NOTIFICATION_CHANNEL_ID} não encontrado.")
                await asyncio.sleep(3600)
                continue

            for match in matches:
                match_id = match['id']
                if match_id in notified_matches:
                    continue  # Pula jogos já notificados

                # Obtém a data do jogo
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
                        f"Acompanhe em: [HLTV.org](https://www.hltv.org/team/8297/furia)"
                    )
                    await channel.send(notification_message)
                    notified_matches.append(match_id)
                    print(f"Notificação enviada para o jogo {match_id}")

            # Limpa jogos antigos da lista de notificados
            notified_matches[:] = [match_id for match_id in notified_matches if match_id in [m['id'] for m in matches]]

        except Exception as e:
            print(f"Erro ao verificar próximos jogos: {str(e)}")
        
        await asyncio.sleep(3600)  # Verifica a cada hora

# Evento que é chamado quando o bot está pronto
@client.event
async def on_ready():
    print(f'Bot connected as {client.user}')
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
                    "🔥 yuurih: Rifler versátil e extremamente confiável.\n"
                    "🎓 FalleN: Lenda brasileira, agora rifler e IGL da equipe.\n"
                    "🧊 molodoy: AWPer do Cazaquistão, jovem promessa no cenário internacional.\n"
                    "⚡ YEKINDAR: Rifler agressivo da Letônia, trazendo experiência internacional.\n"
                    "🧠 sidde: Coach e estrategista da FURIA.",
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
threading.Thread(target=start_health_check_server, daemon=True).start()

# Obtém o token do bot a partir das variáveis de ambiente
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if not TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN not found in environment variables")

# Inicia o bot
client.run(TOKEN)
