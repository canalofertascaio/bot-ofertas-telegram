import requests
import schedule
import time
import threading
import xml.etree.ElementTree as ET
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

TELEGRAM_TOKEN = "8859504173:AAGxsKZ5oa_66Pk1_iaTLkD-fm6BIED0hJI"
TELEGRAM_CANAL = "@ofertasrelampagotech"
ML_ID_AFILIADO = "cl20260628092446"

FEEDS = [
    "https://www.promobit.com.br/feed/",
    "https://www.pelando.com.br/rss",
]

def buscar_ofertas_rss(limite=6):
    print(f"[RSS] Buscando ofertas...")
    ofertas = []
    headers = {"User-Agent": "Mozilla/5.0"}
    for feed_url in FEEDS:
        try:
            r = requests.get(feed_url, timeout=15, headers=headers)
            print(f"[RSS] {feed_url} - Status: {r.status_code}")
            if r.status_code != 200:
                continue
            root = ET.fromstring(r.content)
            items = root.findall(".//item")
            print(f"[RSS] Itens encontrados: {len(items)}")
            for item in items[:limite]:
                titulo = item.findtext("title", "").strip()
                link = item.findtext("link", "").strip()
                descricao = item.findtext("description", "").strip()
                if titulo and link:
                    ofertas.append({
                        "titulo": titulo[:60],
                        "link": link,
                        "descricao": descricao[:100] if descricao else "",
                    })
            if ofertas:
                break
        except Exception as e:
            print(f"[RSS] ERRO {feed_url}: {e}")
            continue
    print(f"[RSS] Total de ofertas: {len(ofertas)}")
    return ofertas[:limite]

def gerar_link_afiliado(link):
    if "mercadolivre.com.br" in link or "mercadolibre.com" in link:
        sep = "&" if "?" in link else "?"
        return f"{link}{sep}partner_id={ML_ID_AFILIADO}"
    return link

def formatar_mensagem(oferta):
    link = gerar_link_afiliado(oferta["link"])
    msg = f"🔥 {oferta['titulo']}\n\n"
    if oferta["descricao"]:
        msg += f"{oferta['descricao']}\n\n"
    msg += f"🛒 COMPRAR AGORA:\n{link}\n\n⏰ Promocao por tempo limitado!\n📢 @ofertasrelampagotech"
    return msg

def enviar_telegram(mensagem):
    print(f"[TG] Enviando mensagem...")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CANAL, "text": mensagem, "disable_web_page_preview": False}
    try:
        r = requests.post(url, json=payload, timeout=20)
        print(f"[TG] Status: {r.status_code}")
        if r.status_code != 200:
            print(f"[TG] Erro: {r.text[:200]}")
            return False
        print(f"[TG] Enviado com sucesso!")
        return True
    except Exception as e:
        print(f"[TG] ERRO: {e}")
        return False

def postar_ofertas():
    print(f"\n{'='*40}")
    print(f"[BOT] Postagem: {datetime.now()}")
    print(f"{'='*40}")
    ofertas = buscar_ofertas_rss(limite=5)
    if not ofertas:
        print("[BOT] Nenhuma oferta encontrada!")
        return
    total = 0
    for oferta in ofertas:
        msg = formatar_mensagem(oferta)
        if enviar_telegram(msg):
            total += 1
        time.sleep(5)
    print(f"[BOT] Total postado: {total}")

def rodar_bot():
    print("[BOT] Thread iniciada!")
    time.sleep(3)
    enviar_telegram(
        "🔥 CANAL NO AR!\n\nBem-vindo ao Ofertas Relampago Tech!\n\n"
        "📱 Celulares | 💻 Notebooks | 📺 TVs\n\n"
        "✅ Melhores ofertas todo dia\n✅ Frete Gratis selecionado\n\n"
        "Ative as notificacoes!\n📢 @ofertasrelampagotech"
    )
    time.sleep(5)
    postar_ofertas()
    schedule.every().day.at("08:00").do(postar_ofertas)
    schedule.every().day.at("12:00").do(postar_ofertas)
    schedule.every().day.at("18:00").do(postar_ofertas)
    schedule.every().day.at("21:00").do(postar_ofertas)
    print("[BOT] Agendamento configurado!")
    while True:
        schedule.run_pending()
        time.sleep(60)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Ofertas Relampago Tech - Rodando!")
    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    print("=" * 40)
    print("BOT OFERTAS RELAMPAGO TECH")
    print("=" * 40)
    bot_thread = threading.Thread(target=rodar_bot, daemon=True)
    bot_thread.start()
    print("[SERVER] Iniciando na porta 10000...")
    server = HTTPServer(("0.0.0.0", 10000), Handler)
    print("[SERVER] Pronto!")
    server.serve_forever()
