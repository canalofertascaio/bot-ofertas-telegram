"""
🤖 BOT DE OFERTAS - ELETRÔNICOS → TELEGRAM
============================================
Canal: Ofertas Relâmpago Tech 🔥
Plataformas: Mercado Livre, Shopee, Amazon
"""

import requests
import schedule
import time
from datetime import datetime

# ============================================================
# ⚙️ CONFIGURAÇÕES
# ============================================================

TELEGRAM_TOKEN = "8902136006:AAFjEQcnO2VDt99QTLYIroXTdpWKi78ArdM"
TELEGRAM_CANAL = "https://t.me/+fiA4XWAeARY2OGIx"
ML_ID_AFILIADO = "cl20260628092446"

# Categorias de eletrônicos no ML
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


# ============================================================
# 🔧 FUNÇÕES
# ============================================================

def buscar_ofertas_ml(categoria_id, limite=3):
    url = "https://api.mercadolibre.com/sites/MLB/search"
    params = {
        "category": categoria_id,
        "sort": "relevance",
        "limit": 30,
        "condition": "new",
    }
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
        print(f"❌ Erro ML: {e}")
        return []


def gerar_link_afiliado_ml(link):
    sep = "&" if "?" in link else "?"
    return f"{link}{sep}partner_id={ML_ID_AFILIADO}"


def formatar_mensagem(produto, categoria):
    frete = "✅ FRETE GRÁTIS" if produto["frete_gratis"] else "🚚 Consulte o frete"
    link = gerar_link_afiliado_ml(produto["link"])
    return f"""{categoria['emoji']} *{produto['titulo']}*

💸 *DE:* ~~R$ {produto['preco_original']:.2f}~~
🔥 *POR:* R$ {produto['preco_atual']:.2f}
📉 *{produto['desconto']}% OFF*
{frete}

🛒 [COMPRAR AGORA]({link})

⏰ _Promoção por tempo limitado!_
➡️ @OfertasRelâmpagoTech"""


def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CANAL,
        "text": mensagem,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        print(f"✅ Postado: {datetime.now().strftime('%H:%M:%S')}")
        return True
    except Exception as e:
        print(f"❌ Erro Telegram: {e}")
        return False


def postar_ofertas():
    print(f"\n🔍 Buscando ofertas... {datetime.now().strftime('%d/%m %H:%M')}")
    total = 0
    for cat in CATEGORIAS_ML:
        produtos = buscar_ofertas_ml(cat["id"], limite=2)
        for p in produtos:
            msg = formatar_mensagem(p, cat)
            if enviar_telegram(msg):
                total += 1
                time.sleep(4)
    print(f"✅ {total} ofertas postadas!")


def postar_boas_vindas():
    msg = """🔥 *BEM-VINDO AO OFERTAS RELÂMPAGO TECH!*

Aqui você recebe as melhores ofertas de eletrônicos todo dia:

📱 Celulares
💻 Notebooks  
📺 TVs
🎧 Fones e Áudio
⚡ Eletrônicos em geral

✅ Até 70% OFF
✅ Frete Grátis selecionado
✅ Atualizado 4x por dia
✅ Só produtos verificados

🔔 *Ative as notificações para não perder nada!*"""
    enviar_telegram(msg)


# ============================================================
# ⏰ AGENDAMENTO
# ============================================================

if __name__ == "__main__":
    print("🤖 Bot Ofertas Relâmpago Tech iniciado!")
    print("⏰ Postagens: 08h | 12h | 18h | 21h")
    print("Pressione Ctrl+C para parar.\n")

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
