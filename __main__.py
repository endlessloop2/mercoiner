from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from bitcoinrpc.authproxy import AuthServiceProxy
from random import seed, randint
from os import urandom
import hashlib, logging
from config import *
from urllib.request import urlopen
from json import load
import codecs


logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

rpc = AuthServiceProxy("http://%s:%s@127.0.0.1:%i"%(RPCuser, RPCpassword, RPCport))

# Hashing de (string + salt) en algoritmo sha256
def hash(string):
	sha = hashlib.sha256()
	template = (str(string) + salt).encode('utf-8')
	sha.update(template)

	return sha.hexdigest()


# Lectura de address, o generación si no existe
def getaddress(name):
	addressList = rpc.getaddressesbyaccount(name)

	if len(addressList) == 0:
		address = rpc.getnewaddress(name)
	else:
		address = addressList[0]

	return address


def start(bot, update):
	user = update.message.from_user

	msg =  "Hola, soy Mercoiner Bot"
	msg += "\nPuedes interactuar conmigo con estos comandos:"
	msg += "\n\n/precio te permite ver el precio de la Mercoin"
	msg += "\n\n/address te permite crear una dirección asociada a tu usuario de Telegram, la cual sirve para enviar o recibir Mercoins."
	msg += "\n\n/balance muestra la cantidad de Mercoins que tienes dentro de esa dirección"
	msg += "\n\nel comando /send puedes enviar Mercoins hacia otras direcciones."
	msg += " Por ejemplo, si deseas enviarle 100 mercoins a la dirección MGrVDKunT76XGRfdv1KbJH78DYZXetwvVU debes usar el comando de la siguiente manera:"
	msg += "\n\n/send 100 MGrVDKunT76XGRfdv1KbJH78DYZXetwvVU"
	msg += "\n\nAdemás, puedes apostar las mercoins que tienes depositadas con /dice especificando la cantidad que quieres apostar. Ej: /dice 100"
	msg += "\n\ny para finalizar esta el comando /red, que resume el estado actual de la red."

	logger.info("start(%i)" % user.id)
	update.message.reply_text("%s" % msg)
	

# Enviar CHA
def send(bot, update, args):
	user = update.message.from_user
	userHash = hash(user.id)
	balance = float(rpc.getbalance(userHash))

	try:
		amount = float(args[0])
		receptor = args[1]

		if not len(receptor) == 34 and receptor[0] == 'M':
			sending = "Address inválida"

		elif not balance > amount:
			sending = "Balance insuficiente"

		elif not amount > 0:
				sending	= "Monto inválido"

		else:
			sending = rpc.sendfrom(userHash, receptor, float(amount))
			sending = "txid: " + sending

	except:
		amount = 0.0
		receptor = "invalid"
		sending = "syntax error\nUSO: /send monto address"

	logger.info("send(%i, %f, %s) => %s" % (user.id, amount, receptor, sending.replace('\n',' // ')))
	update.message.reply_text("%s" % sending)		


# TODO
def info(bot, update):
	address = getaddress("mercoiner")
	balance = float(rpc.getbalance("mercoiner"))

	logger.info("info() => (%s, %f)" % (address, balance))
	update.message.reply_text("Balance de Mercoiner: %f MRN" % balance)		


# Generar solo 1 address por usuario (user.id)
def address(bot, update):
	user = update.message.from_user
	userHash = hash(user.id)

	address = getaddress(userHash)

	logger.info("address(%i) => %s" % (user.id, address))
	update.message.reply_text("%s" % address)

# Mostrar balance de usuario
def balance(bot, update):
	user = update.message.from_user
	userHash = hash(user.id)
	address = getaddress(userHash)
	balance = float(rpc.getbalance(userHash))

	logger.info("balance(%i) => %f %s" % (user.id, balance, address))
	update.message.reply_text("Tu balance es de {0:.8f} MRN".format(balance))	
 
# Lectura de precio de mercado
def precio(bot, update):

	web = urlopen('https://www.southxchange.com/api/price/mrn/btc')
	webu = urlopen('https://www.southxchange.com/api/price/mrn/usd')
	reader = codecs.getreader("utf-8")
	api = load(reader(web))
	apiu = load(reader(webu))	
	
	bid = '{0:.8f} BTC'.format(api['Bid'])
	ask = '{0:.8f} BTC'.format(api['Ask'])
	bidu = '%s USD' % round(apiu['Bid'], 4)
	asku = '%s USD' % round(apiu['Ask'], 4)
	var = api['Variation24Hr']
	
	msg = 'SOUTHXCHANGE:\nPrecio de compra: %s\nPrecio de venta: %s' % (bid, ask)
	msg += '\nPrecio de compra: %s\nPrecio de venta: %s' % (bidu, asku)
	msg += '\nVariación 24hr: %s%%' % (var)


	logger.info("precio() => %s" % msg.replace('\n',' // '))
	update.message.reply_text("%s" % msg)	


# Información de la red
def red(bot, update):
	info = rpc.getmininginfo()

	difficulty = float(info['difficulty']['proof-of-work'])
	blocks = info['blocks']
	power = info['netmhashps']

	#delta = difficulty * 2**32 / float(info['netmhashps']) * 1000000.0 / 60 / 60.0

	#if delta < 1:
	#	delta = str(round(delta*60, 3)) + " minutos"
	#else:
	#	delta = str(round(delta, 3)) + " horas"

	msg = "Bloques: %i\nDificultad: %f\nHashing Power: %f Mh/s\n"

	logger.info("red() => (%i, %f, %f)" % (blocks, difficulty, power))
	update.message.reply_text(msg % (blocks, difficulty, power))

	
# Dado
def dice(bot, update, args):
	user = update.message.from_user
	userHash = hash(user.id)
	userAddress = getaddress(userHash)
	userBalance = float(rpc.getbalance(userHash))
	rand = -1

	try:
		bet = float(args[0])

		if not bet > 0:
			result = "apuesta inválida"

		elif not bet < userBalance:
			result = "balance insuficiente"

		else:
			botAddress = getaddress("mercoiner")
			botBalance = float(rpc.getbalance("mercoiner"))

			prize = bet * 2
			maxNumber = 1000
			lucky = 515 # posibilidades de ganar 48,5% 

			if not botBalance > prize:
				result = "No tengo tantas mercoins :c"
			else:
				# Seed y generación de valor aleatorio
				seed(repr(urandom(64)))
				rand = randint(0,maxNumber)

				# Bonus
				if rand == 777:
					result = "BONUS x2 !! Ganaste %f MRN\nNúmero: %i" % (prize, lucky)
					rpc.sendfrom("mercoiner", userAddress, prize)

				# Ganar
				elif rand > lucky:
					result = "Ganaste %f MRN !\nNúmero: %i" % (bet, rand)
					rpc.sendfrom("mercoiner", userAddress, bet)

				# ???
				elif rand == int(bet):
					result = "Vale otro..."

				# Perder
				else:
					result = "Perdiste %f MRN\nNúmero: %i" % (bet, rand)
					rpc.sendfrom(userHash, botAddress, bet)
	except:
		bet = 0.0
		rand = 0
		result = "Syntax error\nUSO: /dice apuesta"
	
	logger.info("dice(%i, %f, %i) => %s" % (user.id, bet, rand, result.replace('\n',' // ')))
	update.message.reply_text("%s" % result)		

				

	
def error(bot, update, error):
	logger.warning('Update: "%s" - Error: "%s"', update, error)

# Main loop
def main():
	# Configuración
	updater = Updater(token)

	# Get the dispatcher to register handlers
	dp = updater.dispatcher

	# Listado de comandos
	dp.add_handler(CommandHandler("send", send, pass_args=True))
	dp.add_handler(CommandHandler("dice", dice, pass_args=True))
	dp.add_handler(CommandHandler("address", address))
	dp.add_handler(CommandHandler("balance", balance))
	dp.add_handler(CommandHandler("start", start))
	dp.add_handler(CommandHandler("help", start))
	dp.add_handler(CommandHandler("precio", precio))
	dp.add_handler(CommandHandler("red", red))
	dp.add_handler(CommandHandler("info", info))
	
	# log all errors
	dp.add_error_handler(error)


	# Inicio de bot
	botAddress = getaddress("mercoiner")
	logger.info("Mercoiner V 0.9")
	updater.start_polling()

	updater.idle()


if __name__ == '__main__':
	main()
