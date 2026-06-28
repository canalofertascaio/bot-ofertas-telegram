import requests
import schedule
import time
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

TELEGRAM_TOKEN = "8859504173:AAGxsKZ5oa_66Pk1_iaTLkD-fm6BIED0hJI"
TELEGRAM_CANAL = "@ofertasrelampagotech"
ML_ID_AFILIADO = "cl20260628092446"
AMAZON_ID_AFILIADO = "caiomakemoney-20"

PRODUTOS_AMAZON = [
    "celular samsung",
    "notebook",
    "smart tv",
    "fone bluetooth",
    "tablet",
    "ssd",
    "monitor",
    "teclado mouse"
]

def buscar_amazon(termo, limite=2):
    print(f"[AMAZON] Buscando: {termo}")
    url = f"https://www.amazon.com.br/s"
    params = {"k": termo, "ref": "sr_pg_1"}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    try:
        r = requests.get(url, params=params, headers=headers, timeout=20)
        print(f"[AMAZON] Status: {r.status_code}")
        if r.status_code != 200:
            return []
        import re
        # Extrai ASINs (IDs de produtos Amazon)
        asins = re.findall(r'"asin":"([A-Z0-9]{10})"', r.text)
        titulos = re.findall(r'"title"\s*:\s*"([^"]{10,100})"', r.text)
        precos = re.findall(r'"price"\s*:\s*"?([\d,\.]+)"?', r.text)
        print(f"[AMAZON] ASINs: {len(asins)} | Titulos: {len(titulos)}")
        ofertas = []
        for i in range(min(len(asins), limite)):
            asin = asins[i]
            titulo = titulos[i] if i < len(titulos) else termo
            preco = precos[i] if i < len(precos) else ""
            link = f"https://www.amazon.com.br/dp/{asin}?tag={AMAZON_ID_AFILIADO}"
            ofertas.append({
                "titulo": titulo[:60],
                "preco": preco,
                "link": link,
            })
        return ofertas
    except Exception as e:
        print(f"[AMAZON] ERRO: {e}")
        return []

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CANAL, "text": mensagem, "disable_web_page_preview": False}
    try:
        r = requests.post(url, json=payload, timeout=20)
        print(f"[TG] Status: {r.status_code}")
        return r.status_code == 200
    except Exception as e:
        print(f"[TG] ERRO: {e}")
        return False

def postar_ofertas():
    print(f"\n{'='*40}\n[BOT] {datetime.now()}\n{'='*40}")
    total = 0
    for termo in PRODUTOS_AMAZON[:3]:
        ofertas = buscar_amazon(termo, limite=1)
        for o in ofertas:
            msg = (
                f"🛒 {o['titulo']}\n\n"
                f"💰 Preço: R$ {o['preco']}\n\n" if o['preco'] else f"🛒 {o['titulo']}\n\n"
            )
            msg += (
                f"🔗 Ver na Amazon:\n{o['link']}\n\n"
                f"⏰ Oferta por tempo limitado!\n"
                f"📢 @ofertasrelampagotech"
            )
            if enviar_telegram(msg):
                total += 1
            time.sleep(5)
    print(f"[BOT] Total: {total}")

def rodar_bot():
    print("[BOT] Iniciando!")
    time.sleep(3)
    enviar_telegram(
        "🔥 CANAL NO AR!\n\nBem-vindo ao Ofertas Relampago Tech!\n\n"
        "📱 Celulares | 💻 Notebooks | 📺 TVs\n\n"
        "✅ Melhores ofertas Amazon e ML todo dia\n"
        "✅ Frete Gratis selecionado\n\n"
        "Ative as notificacoes!\n📢 @ofertasrelampagotech"
    )
    time.sleep(5)
    postar_ofertas()
    schedule.every().day.at("08:00").do(postar_ofertas)
    schedule.every().day.at("12:00").do(postar_ofertas)
    schedule.every().day.at("18:00").do(postar_ofertas)
    schedule.every().day.at("21:00").do(postar_ofertas)
    while True:
        schedule.run_pending()
        time.sleep(60)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot rodando!")
    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    print("BOT OFERTAS RELAMPAGO TECH")
    bot_thread = threading.Thread(target=rodar_bot, daemon=True)
    bot_thread.start()
    server = HTTPServer(("0.0.0.0", 10000), Handler)
    print("[SERVER] Porta 10000!")
    server.serve_forever()
