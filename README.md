# FURIA CS Fan Bot - Challenge #1: Experiência Conversacional

Bem-vindo ao projeto **FURIA CS Fan Bot**, desenvolvido como parte do **Challenge #1: Experiência Conversacional**!

Este projeto tem como objetivo criar uma experiência interativa para fãs da FURIA Esports no cenário de Counter-Strike, permitindo que eles acompanhem a equipe de forma prática e rápida.

## Sobre o Projeto

O **FURIA CS Fan Bot** é um bot de Discord que permite aos fãs interagirem com informações importantes sobre o time, como:

- **🧩 Conheça nossa Line-up**: Informações atualizadas dos jogadores da FURIA, com links diretos para suas redes sociais.
- **🌐 Redes Sociais**: Acesso às redes oficiais da FURIA, como Twitter, YouTube, Instagram e Loja Oficial.
- **📅 Próximos Jogos**: Link para consultar a agenda de jogos da FURIA no HLTV.org.
- **✅ Últimos Resultados**: Link para acompanhar os últimos resultados no HLTV.org.

Tudo isso por meio de botões interativos, criando uma experiência conversacional fluída dentro do Discord.

## Funcionalidades Implementadas

- Navegação através de botões (sem digitar comandos).
- Acesso rápido às redes sociais dos jogadores e da organização.
- Links diretos para consulta de jogos e resultados.
- Opção de voltar ao menu principal a qualquer momento.

### Observação Importante

⚠️ Devido a restrições de scraping de sites como HLTV.org, a consulta de resultados e jogos futuros é feita através de links externos, e não de forma automática dentro do bot.

## Como Funciona

1. Adicione o bot ao seu servidor do Discord:
   👉 [Clique aqui para convidar o bot](https://discord.com/oauth2/authorize?client_id=1366216478302408736&permissions=84992&integration_type=0&scope=bot+applications.commands)
2. Use o comando `/start` para iniciar.
3. Escolha entre os botões disponíveis:
   - Ver próximos jogos
   - Ver últimos resultados
   - Conhecer a line-up
   - Acessar redes sociais
4. Navegue pelas opções livremente!

A experiência foi pensada para ser **intuitiva** e **fácil**, proporcionando uma sensação de estar mais próximo do time.

## Tecnologias Utilizadas

- **Python 3.11**
- **discord.py** e **discord.ui** para criação do bot.
- **Render** para hospedagem contínua.
- **HTTPServer** para health check e manter o bot sempre online.

## Deploy no Render

O bot é hospedado usando a plataforma Render. Para replicar:

1. Faça o fork deste repositório.
2. Crie um serviço Web no Render.
3. Configure a variável de ambiente:
   - `DISCORD_BOT_TOKEN` (token do bot do Discord)
4. Faça o deploy.

O projeto possui um servidor interno de health check que responde "OK" para manter a instância ativa.

## Licença

Este projeto é licenciado sob a **MIT License**.  
Sinta-se livre para utilizar, modificar e contribuir!

---

**Desenvolvido por Ricardo Lira Silva.**


