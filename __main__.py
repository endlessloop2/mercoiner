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

	msg = "Holi, soy Quirquincho :D"
	msg += "\nPuedes interactuar conmigo con estos cuatro simples comandos:"
	msg += "\n\n/address te permite crear una dirección especifica para tu usuario de Telegram, la cual sirve para enviar o recibir Chauchas."
	msg += "\n\n/balance enseña la cantidad de Chauchas que tienes dentro de esa dirección"
	msg += "\n\nel comando /send puedes enviar Chauchas hacia otras direcciones."
	msg += " Por ejemplo, si deseas enviarle 100 chauchas a la dirección cfBifAmAK3h9Ke4wE2auXaEbfPqeMV44GQ debes usar el comando de la siguiente manera:"
	msg += "\n\n/send 100 cfBifAmAK3h9Ke4wE2auXaEbfPqeMV44GQ"
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

		if not len(receptor) == 34 and receptor[0] == 'c':
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


# Mostrar saldo y address de Quirquincho
def info(bot, update):
	address = getaddress("quirquincho")
	balance = float(rpc.getbalance("quirquincho"))

	logger.info("info() => (%s, %f)" % (address, balance))
	update.message.reply_text("Balance de Quirquincho: %f CHA" % balance)		


# Generar solo 1 address por usuario (user.id)
def address(bot, update):
	user = update.message.from_user
	userHash = hash(user.id)

	address = getaddress(userHash)

	logger.info("address(%i) => %s" % (user.id, address))
	update.message.reply_text("%s" % address)


# Lectura de precio de mercado
def precio(bot, update):

	web = urlopen('https://www.southxchange.com/api/price/mrn/btc')
	reader = codecs.getreader("utf-8")
	api = load(reader(web))

	bid = '{0:.8f} BTC'.format(api['Bid'])
	ask = '{0:.8f} BTC'.format(api['Ask'])
	var = api['Variation24Hr']
	
	msg = 'SOUTHXCHANGE:\nPrecio de compra: %s\nPrecio de venta: %s' % (ask, bid)


	logger.info("precio() => %s" % msg.replace('\n',' // '))
	update.message.reply_text("%s" % msg)	


# Mostrar balance de usuario
def balance(bot, update):
	user = update.message.from_user
	userHash = hash(user.id)

	balance = float(rpc.getbalance(userHash))

	logger.info("balance(%i) => %f" % (user.id, balance))
	update.message.reply_text("{0:.8f} CHA".format(balance))


# Información de la red
def red(bot, update):
	info = rpc.getmininginfo()

	difficulty = float(info['difficulty'])
	blocks = info['blocks']
	power = info['networkhashps'] / 1000000.0

	delta = difficulty * 2**32 / float(info['networkhashps']) / 60 / 60.0

	if delta < 1:
		delta = str(round(delta*60, 3)) + " minutos"
	else:
		delta = str(round(delta, 3)) + " horas"

	msg = "Bloques: %i\nDificultad: %f\nHashing Power: %f Mh/s\n\nEl siguiente bloque se creará en %s"

	logger.info("red() => (%i, %f, %f, %s)" % (blocks, difficulty, power, delta))
	update.message.reply_text(msg % (blocks, difficulty, power, delta))

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
	dp.add_handler(CommandHandler("address", address))
	dp.add_handler(CommandHandler("balance", balance))
	dp.add_handler(CommandHandler("start", start))
	dp.add_handler(CommandHandler("help", start))
	dp.add_handler(CommandHandler("info", info))
	dp.add_handler(CommandHandler("precio", precio))
	dp.add_handler(CommandHandler("red", red))

	# log all errors
	dp.add_error_handler(error)


	# Inicio de bot
	botAddress = getaddress("quirquincho")
	logger.info("Quirquincho V 1.0 - %s" % botAddress)
	updater.start_polling()

	updater.idle()


if __name__ == '__main__':
	main()
