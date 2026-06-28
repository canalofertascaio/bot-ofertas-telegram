import requests
import schedule
import time
import threading
import re
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

TELEGRAM_TOKEN = "8859504173:AAGxsKZ5oa_66Pk1_iaTLkD-fm6BIED0hJI"
TELEGRAM_CANAL = "@ofertasrelampagotech"
ML_ID_AFILIADO = "cl20260628092446"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9",
}

def buscar_ofertas_ml():
    print("[ML] Buscando ofertas do dia...")
    try:
        r = requests.get("https://www.mercadolivre.com.br/ofertas", headers=HEADERS, timeout=20)
        print(f"[ML] Status: {r.status_code}")
        if r.status_code != 200:
            return []
        html = r.text
        # Extrai títulos
        titulos = re.findall(r'"title":"([^"]{10,80})"', html)
        # Extrai preços
        precos = re.findall(r'"price":(\d+\.?\d*)', html)
        # Extrai preços originais
        originais = re.findall(r'"original_price":(\d+\.?\d*)', html)
        # Extrai links
        links = re.findall(r'"permalink":"(https://www\.mercadolivre\.com\.br/[^"]+)"', html)
        print(f"[ML] Titulos: {len(titulos)} | Precos: {len(precos)} | Links: {len(links)}")
        ofertas = []
        for i in range(min(len(titulos), len(links), 6)):
            preco = float(precos[i]) if i < len(precos) else 0
            original = float(originais[i]) if i < len(originais) else 0
            desconto = round((1 - preco/original) * 100) if original > preco > 0 else 0
            ofertas.append({
                "titulo": titulos[i][:60],
                "preco": preco,
                "original": original,
                "desconto": desconto,
                "link": links[i],
            })
        return ofertas
    except Exception as e:
        print(f"[ML] ERRO: {e}")
        return []

def gerar_link(link):
    sep = "&" if "?" in link else "?"
    return f"{link}{sep}partner_id={ML_ID_AFILIADO}"

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
    ofertas = buscar_ofertas_ml()
    if not ofertas:
        print("[BOT] Nenhuma oferta encontrada!")
        return
    total = 0
    for o in ofertas:
        link = gerar_link(o["link"])
        msg = f"🔥 {o['titulo']}\n\n"
        if o["original"] > o["preco"] > 0:
            msg += f"💸 DE: R$ {o['original']:.2f}\n"
            msg += f"✅ POR: R$ {o['preco']:.2f}\n"
        if o["desconto"] > 0:
            msg += f"📉 {o['desconto']}% OFF\n"
        msg += f"\n🛒 COMPRAR AGORA:\n{link}\n\n⏰ Promocao por tempo limitado!\n📢 @ofertasrelampagotech"
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
        "✅ Melhores ofertas do ML todo dia\n"
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
    print("[SERVER] Porta 10000 pronta!")
    server.serve_forever()
