
from os.path import basename
from django.template import loader, Context
from django.core.mail import EmailMultiAlternatives


def make_choices(choices):
	"""
	zips a list with itself for field choices
	"""
	return zip(choices, choices)

def set_shipping(request, shipping_type, shipping_total):
	"""
	stores the shipping type and total in the session
	"""
	request.session["shipping_type"] = shipping_type
	request.session["shipping_total"] = shipping_total

def send_mail_template(subject, template, addr_from, addr_to, context=None,
	attachments=None, fail_silently=False):
	"""
	send email rendering text and html versions for the specified template name
	using the context dictionary passed in
	"""
	if context is None:
		context = {}
	if attachments is None:
		attachments = []
	# allow for a single address to be passed in
	if not hasattr(addr_to, "__iter__"):
		addr_to = [addr_to]
	# loads a template passing in vars as context
	render = lambda type: loader.get_template("%s.%s" % 
		(template, type)).render(Context(context))
	# create and send email
	msg = EmailMultiAlternatives(subject, render("txt"), addr_from, addr_to)
	msg.attach_alternative(render("html"), "text/html")
	for attachment in attachments:
		msg.attach(attachment)
	msg.send(fail_silently=fail_silently)


