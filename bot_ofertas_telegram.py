import requests
import schedule
import time
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

TELEGRAM_TOKEN = "8859504173:AAGxsKZ5oa_66Pk1_iaTLkD-fm6BIED0hJI"
TELEGRAM_CANAL = "@ofertasrelampagotech"
ML_ID_AFILIADO = "cl20260628092446"

def buscar_ofertas():
    print(f"[BOT] Buscando ofertas...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }
    urls = [
        "https://www.promobit.com.br/api/offers?page=1&limit=10&category=eletronicos",
        "https://www.promobit.com.br/api/offers?page=1&limit=10",
    ]
    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            print(f"[BOT] Status {url}: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                ofertas = data.get("data", data.get("offers", data.get("results", [])))
                if ofertas:
                    print(f"[BOT] Ofertas encontradas: {len(ofertas)}")
                    return ofertas[:5]
        except Exception as e:
            print(f"[BOT] Erro: {e}")
    return []

def gerar_link(link):
    if "mercadolivre.com.br" in link or "mercadolibre.com" in link:
        sep = "&" if "?" in link else "?"
        return f"{link}{sep}partner_id={ML_ID_AFILIADO}"
    return link

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CANAL, "text": mensagem, "disable_web_page_preview": False}
    try:
        r = requests.post(url, json=payload, timeout=20)
        print(f"[TG] Status: {r.status_code} | Resposta: {r.text[:100]}")
        return r.status_code == 200
    except Exception as e:
        print(f"[TG] Erro: {e}")
        return False

def postar_ofertas():
    print(f"\n{'='*40}\n[BOT] Iniciando: {datetime.now()}\n{'='*40}")
    ofertas = buscar_ofertas()
    if not ofertas:
        print("[BOT] Nenhuma oferta encontrada!")
        enviar_telegram("🔍 Buscando as melhores ofertas do dia... Volte em breve! 📢 @ofertasrelampagotech")
        return
    total = 0
    for oferta in ofertas:
        titulo = str(oferta.get("title", oferta.get("name", oferta.get("titulo", ""))))[:60]
        link = str(oferta.get("url", oferta.get("link", oferta.get("href", ""))))
        preco = oferta.get("price", oferta.get("preco", ""))
        desconto = oferta.get("discount", oferta.get("desconto", ""))
        if not titulo or not link:
            continue
        link = gerar_link(link)
        msg = f"🔥 {titulo}\n\n"
        if preco:
            msg += f"💰 Preco: R$ {preco}\n"
        if desconto:
            msg += f"📉 Desconto: {desconto}% OFF\n"
        msg += f"\n🛒 COMPRAR AGORA:\n{link}\n\n⏰ Promocao por tempo limitado!\n📢 @ofertasrelampagotech"
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
        "✅ Melhores ofertas todo dia\n"
        "✅ Frete Gratis selecionado\n\n"
        "Ative as notificacoes!\n📢 @ofertasrelampagotech"
    )
    time.sleep(5)
    postar_ofertas()
    schedule.every().day.at("08:00").do(postar_ofertas)
    schedule.every().day.at("12:00").do(postar_ofertas)
    schedule.every().day.at("18:00").do(postar_ofertas)
    schedule.every().day.at("21:00").do(postar_ofertas)
    print("[BOT] Agendamento: 08h | 12h | 18h | 21h")
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
    print("="*40)
    print("BOT OFERTAS RELAMPAGO TECH")
    print("="*40)
    bot_thread = threading.Thread(target=rodar_bot, daemon=True)
    bot_thread.start()
    server = HTTPServer(("0.0.0.0", 10000), Handler)
    print("[SERVER] Pronto na porta 10000!")
    server.serve_forever()
