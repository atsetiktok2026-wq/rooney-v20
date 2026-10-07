"""
Rooney V20 Ultra - COMPLET CORRIGE - 10$ SAFE - Abidjan
Bot: @rooney_v20_atse_bot
Trust Wallet: TEKWF5yh3Rs3PRd6aUvx6d3WxqLrySwMrx
Version Render 24h/24
"""
import asyncio
import websockets
import json
import os
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ================= CONFIG RENDER - NE TOUCHE PLUS =================
# Render va remplir tout seul avec tes Environment Variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DERIV_API_TOKEN = os.getenv("DERIV_API_TOKEN")

TRUST_WALLET_ADDRESS = "TEKWF5yh3Rs3PRd6aUvx6d3WxqLrySwMrx"
# =========================================================

# Config securisee 10$
STAKE = 0.35
OBJECTIF = 2.0
STOP_LOSS = 3.0
SYMBOL = "R_10"

is_trading = False
profit_total = 0.0
last_results = [] # memoire des pertes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🔥 **ROONEY V20 ULTRA - EN LIGNE 24h/24** 🔥\n\n"
        "Bot Abidjan - Pret !\n\n"
        f"💳 Depot: Trust Wallet USDT TRC20\n"
        f"💸 Retrait: {TRUST_WALLET_ADDRESS[:6]}...{TRUST_WALLET_ADDRESS[-4:]}\n"
        f"🎯 Mise: {STAKE}$ | Objectif: +{OBJECTIF}$/jour\n"
        f"🛑 Stop: -{STOP_LOSS}$/jour\n\n"
        "Commandes:\n"
        "/deposer - Comment deposer 10$ depuis Trust Wallet\n"
        "/retirer - Comment retirer en Wave / OM\n"
        "/balance - Voir solde Deriv\n"
        "/trade - Lancer / Arreter le bot\n"
        "/status - Voir profit du jour"
    )
    await update.message.reply_text(text, parse_mode='Markdown')

async def deposer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💰 **DEPOT 10$ - TRUST WALLET -> DERIV**\n\n"
        "1. Va sur **Deriv** > Caisse > Depot > **Crypto** > **USDT** > **TRC20**\n"
        "2. Copie l'adresse Deriv (commence par T...)\n"
        "3. Va dans **Trust Wallet** > USDT > **Envoyer**\n"
        "4. Colle l'adresse Deriv + Montant **11 USDT**\n"
        "5. Reseau: **TRC20** OBLIGATOIRE\n"
        "6. Valide. Arrive en 2 min.\n\n"
        "⚠️ TRC20 avec TRC20 seulement !\n"
        "Apres tape /balance",
        parse_mode='Markdown'
    )

async def retirer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"💸 **RETRAIT -> TRUST WALLET -> WAVE**\n\n"
        f"Ton adresse TRC20:\n`{TRUST_WALLET_ADDRESS}`\n\n"
        "1. Deriv > Caisse > Retrait > Crypto > **USDT TRC20**\n"
        f"2. Colle: `{TRUST_WALLET_ADDRESS}`\n"
        "3. Montant: tout ou partie\n"
        "4. Recois en 5 min sur Trust Wallet\n\n"
        "**Pour avoir en Wave:**\n"
        "5. Trust Wallet > Envoyer > vers Binance (TRC20)\n"
        "6. Binance P2P > Vends USDT > Recois Wave instant",
        parse_mode='Markdown'
    )

async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Connexion Deriv...")
    try:
        async with websockets.connect('wss://ws.derivws.com/websockets/v3?app_id=1089') as ws:
            await ws.send(json.dumps({"authorize": DERIV_API_TOKEN}))
            auth = json.loads(await ws.recv())
            if 'error' in auth:
                await update.message.reply_text(f"❌ Token Deriv invalide: {auth['error']['message']}")
                return
            await ws.send(json.dumps({"balance": 1}))
            bal = json.loads(await ws.recv())
            b = bal['balance']['balance']
            c = bal['balance']['currency']
            await update.message.reply_text(f"💰 Solde: **{b} {c}** | Profit jour: {round(profit_total,2)}$", parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {e}")

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"📊 Status:\nTrading: {'ON' if is_trading else 'OFF'}\nProfit jour: {round(profit_total,2)}$ / {OBJECTIF}$\nMise: {STAKE}$\nSymbole: {SYMBOL}\nMemoire: {last_results[-5:]}")

async def trade_logic(app):
    global is_trading, profit_total, last_results
    is_trading = True
    profit_total = 0.0
    last_results = []
    
    chat_id = app.bot_data.get('chat_id')
    
    while is_trading:
        try:
            async with websockets.connect('wss://ws.derivws.com/websockets/v3?app_id=1089') as ws:
                await ws.send(json.dumps({"authorize": DERIV_API_TOKEN}))
                await ws.recv()

                await ws.send(json.dumps({"ticks": SYMBOL}))
                ticks = []
                while len(ticks) < 3:
                    msg = json.loads(await ws.recv())
                    if 'tick' in msg:
                        ticks.append(msg['tick']['quote'])
                
                last_digit = int(str(ticks[-1]).split('.')[-1][-1])

                # LOGIQUE AUTO-LEARNING : s'il perd 2 fois, il inverse
                if last_results[-2:] == ['LOSS', 'LOSS']:
                    prediction = "UNDER" if last_digit < 5 else "OVER"
                else:
                    prediction = "OVER" if last_digit < 5 else "UNDER"
                
                barrier = 4
                contract_type = "DIGITOVER" if prediction == "OVER" else "DIGITUNDER"

                proposal = {
                    "proposal": 1, "amount": STAKE, "basis": "stake",
                    "contract_type": contract_type, "currency": "USD",
                    "duration": 1, "duration_unit": "t", "symbol": SYMBOL, "barrier": barrier
                }
                await ws.send(json.dumps(proposal))
                prop_resp = json.loads(await ws.recv())
                
                if 'error' in prop_resp:
                    await asyncio.sleep(5)
                    continue

                await ws.send(json.dumps({"buy": prop_resp['proposal']['id'], "price": STAKE}))
                buy_resp = json.loads(await ws.recv())
                
                if 'error' in buy_resp:
                    await asyncio.sleep(5)
                    continue

                contract_id = buy_resp['buy']['contract_id']
                
                # Attend le resultat reel
                await asyncio.sleep(3)
                while True:
                    await ws.send(json.dumps({"proposal_open_contract": 1, "contract_id": contract_id}))
                    result_msg = json.loads(await ws.recv())
                    if 'proposal_open_contract' in result_msg and result_msg['proposal_open_contract']['is_sold']:
                        profit = result_msg['proposal_open_contract']['profit']
                        break
                    await asyncio.sleep(1)

                profit_total += profit
                if profit > 0:
                    last_results.append('WIN')
                    status_emoji = "✅"
                else:
                    last_results.append('LOSS')
                    status_emoji = "❌"

                if chat_id:
                    await app.bot.send_message(chat_id=chat_id, text=f"{status_emoji} {contract_type} | Digit: {last_digit} | Profit: {profit}$ | Total jour: {round(profit_total,2)}$")

                if profit_total >= OBJECTIF:
                    is_trading = False
                    if chat_id:
                        await app.bot.send_message(chat_id=chat_id, text=f"🎯 OBJECTIF ATTEINT ! +{round(profit_total,2)}$ Le bot s'arrete pour securiser.")
                    break
                if profit_total <= -STOP_LOSS:
                    is_trading = False
                    if chat_id:
                        await app.bot.send_message(chat_id=chat_id, text=f"🛑 STOP LOSS ATTEINT {round(profit_total,2)}$. Arret pour proteger ton capital.")
                    break

                await asyncio.sleep(5)

        except Exception as e:
            await asyncio.sleep(10)
            continue

async def trade_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_trading
    context.application.bot_data['chat_id'] = update.effective_chat.id
    if is_trading:
        is_trading = False
        await update.message.reply_text(f"🛑 Bot arrete. Profit final: {round(profit_total,2)} $")
    else:
        await update.message.reply_text(f"🚀 Lancement avec {STAKE}$ sur {SYMBOL}\nObjectif {OBJECTIF}$ - Stop {STOP_LOSS}$\nMode AUTO-LEARNING actif...")
        asyncio.create_task(trade_logic(context.application))

def main():
    if not TELEGRAM_TOKEN or not DERIV_API_TOKEN:
        print("❌ ERREUR: Mets tes 2 tokens dans Render > Environment Variables")
        return
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("deposer", deposer))
    app.add_handler(CommandHandler("retirer", retirer))
    app.add_handler(CommandHandler("balance", balance_cmd))
    app.add_handler(CommandHandler("trade", trade_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    print("Bot lance - va sur Telegram /start")
    app.run_polling()

if __name__ == "__main__":
    main()
