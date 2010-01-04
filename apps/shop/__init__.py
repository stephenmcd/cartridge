
from thread import start_new_thread
from datetime import datetime, timedelta
from time import sleep
from shop.models import Cart
from shop.settings import CART_EXPIRY_AGE, CART_EXPIRY_INTERVAL


def remove_expired_carts():
	while True:
		expiry_time = datetime.now() - timedelta(minutes=CART_EXPIRY_AGE)
		Cart.objects.filter(timestamp__lt=expiry_time).delete()
		sleep(60 * CART_EXPIRY_INTERVAL)

start_new_thread(remove_expired_carts, ())

