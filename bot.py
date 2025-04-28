import cloudscraper

def get_recent_results_hltv():
    scraper = cloudscraper.create_scraper()
    for attempt in range(3):  # Tenta até 3 vezes
        try:
            # URL da página de resultados da FURIA no HLTV.org
            url = "https://www.hltv.org/results?team=8297"
            print(f"Tentativa {attempt + 1}/3 de buscar resultados no HLTV.org")
            response = scraper.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Encontra a seção de resultados
            results = soup.find_all('div', class_='result-con')[:4]  # Limita a 4 resultados
            if not results:
                print("Nenhum elemento 'result-con' encontrado no HLTV.org")
                return "Não há resultados recentes disponíveis no HLTV.org.\n\nAcompanhe atualizações em: [HLTV.org](https://www.hltv.org/team/8297/furia)"

            results_text = "✅ Últimos resultados da FURIA (via HLTV.org):\n\n"
            for result in results:
                # Extrai a data
                date_span = result.find('span', class_='match-date')
                if not date_span:
                    print("Elemento 'match-date' não encontrado em um resultado")
                    date = "Data não disponível"
                else:
                    date = date_span.text.strip()

                # Extrai os times e placar
                teams = result.find_all('td', class_='team-cell')
                if len(teams) != 2:
                    print(f"Esperava 2 times, mas encontrou {len(teams)}")
                    continue  # Pula este resultado se os times não forem encontrados corretamente

                team1_div = teams[0].find('div', class_='team')
                team2_div = teams[1].find('div', class_='team')
                if not team1_div or not team2_div:
                    print("Elemento 'team' não encontrado para um dos times")
                    continue  # Pula este resultado

                team1 = team1_div.text.strip()
                team2 = team2_div.text.strip()

                score_td = result.find('td', class_='result-score')
                if not score_td:
                    print("Elemento 'result-score' não encontrado")
                    continue  # Pula este resultado

                score = score_td.text.strip()

                # Determina o oponente e ajusta o placar
                if team1.lower() == "furia":
                    opponent = team2
                    score_display = score  # Ex.: "16 - 10"
                else:
                    opponent = team1
                    score_display = f"{score.split(' - ')[1]} - {score.split(' - ')[0]}"  # Inverte o placar

                # Extrai o evento
                event_span = result.find('span', class_='event-name')
                if not event_span:
                    print("Elemento 'event-name' não encontrado")
                    event = "Evento não disponível"
                else:
                    event = event_span.text.strip()

                results_text += f"- {date}: FURIA {score_display} {opponent} | {event}\n"

            if not results_text.endswith("\n\n"):
                print("Nenhum resultado válido foi extraído do HLTV.org")
                return "Não há resultados recentes disponíveis no HLTV.org.\n\nAcompanhe atualizações em: [HLTV.org](https://www.hltv.org/team/8297/furia)"

            return results_text
        except requests.exceptions.HTTPError as e:
            print(f"Erro HTTP ao buscar resultados no HLTV.org: {str(e)}")
            if e.response.status_code == 403:
                print("Acesso bloqueado pelo HLTV.org (403 Forbidden)")
                return "⚠️ O HLTV.org bloqueou o acesso. Tente novamente mais tarde.\nAcompanhe atualizações em: [HLTV.org](https://www.hltv.org/team/8297/furia)"
            elif e.response.status_code == 429:
                print("Limite de requisições excedido no HLTV.org (429 Too Many Requests)")
                if attempt < 2:  # Não espera na última tentativa
                    wait_time = (attempt + 1) * 5  # Espera 5s, 10s, 15s
                    print(f"Aguardando {wait_time} segundos antes de tentar novamente...")
                    time.sleep(wait_time)
                    continue
            return "⚠️ Não foi possível buscar os resultados recentes no HLTV.org.\nAcompanhe atualizações em: [HLTV.org](https://www.hltv.org/team/8297/furia)"
        except requests.exceptions.RequestException as e:
            print(f"Erro de requisição ao buscar resultados no HLTV.org: {str(e)}")
            if attempt < 2:  # Não espera na última tentativa
                wait_time = (attempt + 1) * 5
                print(f"Aguardando {wait_time} segundos antes de tentar novamente...")
                time.sleep(wait_time)
                continue
            return "⚠️ Não foi possível buscar os resultados recentes no HLTV.org.\nAcompanhe atualizações em: [HLTV.org](https://www.hltv.org/team/8297/furia)"
        except Exception as e:
            print(f"Erro inesperado ao buscar resultados no HLTV.org: {str(e)}")
            return "⚠️ Não foi possível buscar os resultados recentes no HLTV.org.\nAcompanhe atualizações em: [HLTV.org](https://www.hltv.org/team/8297/furia)"
