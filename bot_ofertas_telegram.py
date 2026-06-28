import requests
import schedule
import time
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# ============================================================
# CONFIGURACOES
# ============================================================
TELEGRAM_TOKEN = "8859504173:AAGxsKZ5oa_66Pk1_iaTLkD-fm6BIED0hJI"
TELEGRAM_CANAL = "@ofertasrelampagotech"
ML_ID_AFILIADO = "cl20260628092446"

CATEGORIAS_ML = [
    {"id": "MLB1051", "nome": "Celulares", "emoji": "📱"},
    {"id": "MLB1648", "nome": "Computadores", "emoji": "💻"},
    {"id": "MLB3697", "nome": "TVs", "emoji": "📺"},
]

DESCONTO_MINIMO = 10
PRECO_MINIMO = 50
PRECO_MAXIMO = 5000

# ============================================================
# FUNCOES
# ============================================================

def buscar_ofertas_ml(categoria_id, limite=2):
    print(f"[ML] Buscando categoria {categoria_id}...")
    url = "https://api.mercadolibre.com/sites/MLB/search"
    params = {
        "category": categoria_id,
        "sort": "relevance",
        "limit": 50,
        "condition": "new"
    }
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, params=params, timeout=20, headers=headers)
        print(f"[ML] Status: {r.status_code}")
        if r.status_code != 200:
            print(f"[ML] Erro: {r.text[:200]}")
            return []
        items = r.json().get("results", [])
        print(f"[ML] Itens recebidos: {len(items)}")
        ofertas = []
        for item in items:
            preco_original = item.get("original_price")
            preco_atual = item.get("price", 0)
            if not preco_original or preco_atual <= 0:
                continue
            desconto = round((1 - preco_atual / preco_original) * 100)
            if desconto >= DESCONTO_MINIMO and PRECO_MINIMO <= preco_atual <= PRECO_MAXIMO:
                ofertas.append({
                    "titulo": item.get("title", "")[:55],
                    "preco_atual": preco_atual,
                    "preco_original": preco_original,
                    "desconto": desconto,
                    "link": item.get("permalink", ""),
                    "frete_gratis": item.get("shipping", {}).get("free_shipping", False),
                })
        ofertas.sort(key=lambda x: x["desconto"], reverse=True)
        print(f"[ML] Ofertas com desconto: {len(ofertas)}")
        return ofertas[:limite]
    except Exception as e:
        print(f"[ML] ERRO: {e}")
        return []


def gerar_link(link):
    sep = "&" if "?" in link else "?"
    return f"{link}{sep}partner_id={ML_ID_AFILIADO}"


def formatar_mensagem(produto, categoria):
    frete = "FRETE GRATIS ✅" if produto["frete_gratis"] else ""
    link = gerar_link(produto["link"])
    return (
        f"{categoria['emoji']} {produto['titulo']}\n\n"
        f"DE: R$ {produto['preco_original']:.2f}\n"
        f"POR: R$ {produto['preco_atual']:.2f}\n"
        f"DESCONTO: {produto['desconto']}% OFF\n"
        f"{frete}\n\n"
        f"COMPRAR AGORA:\n{link}\n\n"
        f"Promocao por tempo limitado!"
    )


def enviar_telegram(mensagem):
    print(f"[TG] Enviando mensagem...")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CANAL,
        "text": mensagem,
        "disable_web_page_preview": False
    }
    try:
        r = requests.post(url, json=payload, timeout=20)
        print(f"[TG] Status: {r.status_code}")
        if r.status_code != 200:
            print(f"[TG] Erro: {r.text[:300]}")
            return False
        print(f"[TG] Mensagem enviada com sucesso!")
        return True
    except Exception as e:
        print(f"[TG] ERRO: {e}")
        return False


def postar_ofertas():
    print(f"\n{'='*40}")
    print(f"[BOT] Iniciando postagem: {datetime.now()}")
    print(f"{'='*40}")
    total = 0
    for cat in CATEGORIAS_ML:
        produtos = buscar_ofertas_ml(cat["id"], limite=2)
        if not produtos:
            print(f"[BOT] Nenhuma oferta para {cat['nome']}")
            continue
        for p in produtos:
            msg = formatar_mensagem(p, cat)
            if enviar_telegram(msg):
                total += 1
            time.sleep(5)
    print(f"[BOT] Total postado: {total}")


def rodar_bot():
    print("[BOT] Thread iniciada!")
    time.sleep(3)
    # Mensagem de boas vindas
    enviar_telegram(
        "🔥 CANAL NO AR!\n\n"
        "Bem-vindo ao Ofertas Relampago Tech!\n\n"
        "📱 Celulares | 💻 Notebooks | 📺 TVs\n\n"
        "✅ Ate 70% OFF todo dia\n"
        "✅ Frete Gratis selecionado\n\n"
        "Ative as notificacoes para nao perder nada!"
    )
    time.sleep(5)
    # Primeira rodada de ofertas
    postar_ofertas()
    # Agendamento diario
    schedule.every().day.at("08:00").do(postar_ofertas)
    schedule.every().day.at("12:00").do(postar_ofertas)
    schedule.every().day.at("18:00").do(postar_ofertas)
    schedule.every().day.at("21:00").do(postar_ofertas)
    print("[BOT] Agendamento configurado!")
    while True:
        schedule.run_pending()
        time.sleep(60)


# ============================================================
# SERVIDOR WEB (necessario para o Render)
# ============================================================

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Ofertas Relampago Tech - Rodando!")

    def log_message(self, format, *args):
        pass  # Silencia logs do servidor HTTP


# ============================================================
# INICIO
# ============================================================

if __name__ == "__main__":
    print("=" * 40)
    print("BOT OFERTAS RELAMPAGO TECH")
    print("=" * 40)
    print(f"Canal: {TELEGRAM_CANAL}")
    print(f"Afiliado ML: {ML_ID_AFILIADO}")
    print(f"Categorias: {len(CATEGORIAS_ML)}")
    print("=" * 40)

    # Inicia o bot em thread separada
    bot_thread = threading.Thread(target=rodar_bot, daemon=True)
    bot_thread.start()

    # Inicia servidor HTTP na porta 10000
    print("[SERVER] Iniciando servidor HTTP na porta 10000...")
    server = HTTPServer(("0.0.0.0", 10000), Handler)
    print("[SERVER] Servidor pronto!")
    server.serve_forever()
