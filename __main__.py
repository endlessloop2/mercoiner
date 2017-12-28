from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from bitcoinrpc.authproxy import AuthServiceProxy
#from random import seed, randint
#from os import urandom
import hashlib, logging
from config import *
from urllib.request import urlopen
from json import load
import codecs


logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

rpc = AuthServiceProxy("http://%s:%s@127.0.0.1:%i"%(RPCuser, RPCpassword, RPCport))

# Hashing de (string + salt) en algoritmo sha256
#def hash(string):
#	sha = hashlib.sha256()
#	template = (str(string) + salt).encode('utf-8')
#	sha.update(template)

#	return sha.hexdigest()


def start(bot, update):
	user = update.message.from_user

	msg =  "Hola, soy Mercoiner Bot"
	msg += "\nPuedes interactuar conmigo con estos comandos:"
	msg += "\n\n/precio te permite ver el precio de la Mercoin"
	msg += "\n\ny para finalizar esta el comando /red, que resume el estado actual de la red."

	logger.info("start(%i)" % user.id)
	update.message.reply_text("%s" % msg)		


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


# Información de la red
def red(bot, update):
	info = rpc.getmininginfo()

	difficulty = float(info['difficulty']['proof-of-work'])
	blocks = info['blocks']
	power = info['netmhashps']

	delta = difficulty * 2**32 / float(info['netmhashps']) * 1000000.0 / 60 / 60.0

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
	dp.add_handler(CommandHandler("start", start))
	dp.add_handler(CommandHandler("help", start))
	dp.add_handler(CommandHandler("precio", precio))
	dp.add_handler(CommandHandler("red", red))

	# log all errors
	dp.add_error_handler(error)


	# Inicio de bot
	#botAddress = getaddress("quirquincho")
	logger.info("Mercoiner V 0.9")
	updater.start_polling()

	updater.idle()


if __name__ == '__main__':
	main()
