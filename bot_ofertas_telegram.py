import requests
import schedule
import time
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

TELEGRAM_TOKEN = "8902136006:AAFjEQcnO2VDt99QTLYIroXTdpWKi78ArdM"
TELEGRAM_CANAL = "https://t.me/+fiA4XWAeARY2OGIx"
ML_ID_AFILIADO = "cl20260628092446"

CATEGORIAS_ML = [
    {"id": "MLB1051", "nome": "Celulares", "emoji": "📱"},
    {"id": "MLB1648", "nome": "Computadores", "emoji": "💻"},
    {"id": "MLB3697", "nome": "TVs", "emoji": "📺"},
    {"id": "MLB1144", "nome": "Áudio", "emoji": "🎧"},
    {"id": "MLB1000", "nome": "Eletrônicos", "emoji": "⚡"},
]

DESCONTO_MINIMO = 20
PRECO_MINIMO = 50
PRECO_MAXIMO = 3000

def buscar_ofertas_ml(categoria_id, limite=3):
    url = "https://api.mercadolibre.com/sites/MLB/search"
    params = {"category": categoria_id, "sort": "relevance", "limit": 30, "condition": "new"}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        items = r.json().get("results", [])
        ofertas = []
        for item in items:
            preco_original = item.get("original_price")
            preco_atual = item.get("price", 0)
            if not preco_original or preco_atual <= 0:
                continue
            desconto = round((1 - preco_atual / preco_original) * 100)
            if desconto >= DESCONTO_MINIMO and PRECO_MINIMO <= preco_atual <= PRECO_MAXIMO:
                ofertas.append({
                    "titulo": item.get("title", "")[:60],
                    "preco_atual": preco_atual,
                    "preco_original": preco_original,
                    "desconto": desconto,
                    "link": item.get("permalink", ""),
                    "frete_gratis": item.get("shipping", {}).get("free_shipping", False),
                })
        ofertas.sort(key=lambda x: x["desconto"], reverse=True)
        return ofertas[:limite]
    except Exception as e:
        print(f"Erro ML: {e}")
        return []

def gerar_link_afiliado_ml(link):
    sep = "&" if "?" in link else "?"
    return f"{link}{sep}partner_id={ML_ID_AFILIADO}"

def formatar_mensagem(produto, categoria):
    frete = "✅ FRETE GRÁTIS" if produto["frete_gratis"] else "🚚 Consulte o frete"
    link = gerar_link_afiliado_ml(produto["link"])
    return f"""{categoria['emoji']} *{produto['titulo']}*

💸 *DE:* R$ {produto['preco_original']:.2f}
🔥 *POR:* R$ {produto['preco_atual']:.2f}
📉 *{produto['desconto']}% OFF*
{frete}

🛒 [COMPRAR AGORA]({link})

⏰ _Promoção por tempo limitado!_"""

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": "@OfertasRelâmpagoTech", "text": mensagem, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        print(f"✅ Postado: {datetime.now().strftime('%H:%M:%S')}")
        return True
    except Exception as e:
        print(f"Erro Telegram: {e}")
        return False

def postar_ofertas():
    print(f"Buscando ofertas... {datetime.now().strftime('%d/%m %H:%M')}")
    for cat in CATEGORIAS_ML:
        produtos = buscar_ofertas_ml(cat["id"], limite=2)
        for p in produtos:
            enviar_telegram(formatar_mensagem(p, cat))
            time.sleep(4)

def postar_boas_vindas():
    msg = """🔥 *BEM-VINDO AO OFERTAS RELÂMPAGO TECH!*

📱 Celulares | 💻 Notebooks | 📺 TVs | 🎧 Áudio

✅ Até 70% OFF
✅ Frete Grátis selecionado
✅ Atualizado 4x por dia

🔔 *Ative as notificações!*"""
    enviar_telegram(msg)

def rodar_bot():
    postar_boas_vindas()
    time.sleep(3)
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
    t = threading.Thread(target=rodar_bot)
    t.daemon = True
    t.start()
    print("🤖 Bot iniciado!")
    server = HTTPServer(("0.0.0.0", 10000), Handler)
    server.serve_forever()
