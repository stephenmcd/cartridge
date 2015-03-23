from __future__ import unicode_literals
# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    depends_on = [
        ("pages", "0001_initial"),
    ]

    def forwards(self, orm):

        # Adding model 'ProductOption'
        db.create_table('shop_productoption', (
            ('type', self.gf('django.db.models.fields.IntegerField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('cartridge.shop.fields.OptionField')(max_length=50, null=True)),
        ))
        db.send_create_signal('shop', ['ProductOption'])

        # Adding model 'Category'
        db.create_table('shop_category', (
            ('content', self.gf('mezzanine.core.fields.HtmlField')()),
            ('page_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['pages.Page'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('shop', ['Category'])

        # Adding model 'Product'
        db.create_table('shop_product', (
            ('status', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('sale_to', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('available', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('description', self.gf('mezzanine.core.fields.HtmlField')(blank=True)),
            ('_keywords', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('short_url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('image', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('sale_id', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('unit_price', self.gf('cartridge.shop.fields.MoneyField')(null=True, max_digits=10, decimal_places=2, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content', self.gf('mezzanine.core.fields.HtmlField')()),
            ('expiry_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('publish_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('date_added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('sale_price', self.gf('cartridge.shop.fields.MoneyField')(null=True, max_digits=10, decimal_places=2, blank=True)),
            ('slug', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('sale_from', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('shop', ['Product'])

        # Adding M2M table for field keywords on 'Product'
        db.create_table('shop_product_keywords', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('product', models.ForeignKey(orm['shop.product'], null=False)),
            ('keyword', models.ForeignKey(orm['core.keyword'], null=False))
        ))
        db.create_unique('shop_product_keywords', ['product_id', 'keyword_id'])

        # Adding M2M table for field categories on 'Product'
        db.create_table('shop_product_categories', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('product', models.ForeignKey(orm['shop.product'], null=False)),
            ('category', models.ForeignKey(orm['shop.category'], null=False))
        ))
        db.create_unique('shop_product_categories', ['product_id', 'category_id'])

        # Adding model 'ProductImage'
        db.create_table('shop_productimage', (
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(related_name='images', to=orm['shop.Product'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('file', self.gf('django.db.models.fields.files.ImageField')(max_length=100)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
        ))
        db.send_create_signal('shop', ['ProductImage'])

        # Adding model 'ProductVariation'
        db.create_table('shop_productvariation', (
            ('sale_to', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('sku', self.gf('cartridge.shop.fields.SKUField')(unique=True, max_length=20)),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(related_name='variations', to=orm['shop.Product'])),
            ('sale_from', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('default', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('image', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['shop.ProductImage'], null=True, blank=True)),
            ('sale_id', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('unit_price', self.gf('cartridge.shop.fields.MoneyField')(null=True, max_digits=10, decimal_places=2, blank=True)),
            ('num_in_stock', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('sale_price', self.gf('cartridge.shop.fields.MoneyField')(null=True, max_digits=10, decimal_places=2, blank=True)),
            ('option2', self.gf('cartridge.shop.fields.OptionField')(max_length=50, null=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('option1', self.gf('cartridge.shop.fields.OptionField')(max_length=50, null=True)),
        ))
        db.send_create_signal('shop', ['ProductVariation'])

        # Adding model 'Order'
        db.create_table('shop_order', (
            ('status', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('shipping_detail_country', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('additional_instructions', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('billing_detail_city', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('shipping_type', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('billing_detail_country', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('shipping_detail_phone', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('shipping_detail_city', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('total', self.gf('cartridge.shop.fields.MoneyField')(null=True, max_digits=10, decimal_places=2, blank=True)),
            ('shipping_detail_postcode', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('billing_detail_phone', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('shipping_detail_last_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('billing_detail_street', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('shipping_detail_first_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('billing_detail_last_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('discount_code', self.gf('cartridge.shop.fields.DiscountCodeField')(max_length=20, blank=True)),
            ('billing_detail_postcode', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('shipping_total', self.gf('cartridge.shop.fields.MoneyField')(null=True, max_digits=10, decimal_places=2, blank=True)),
            ('shipping_detail_state', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('item_total', self.gf('cartridge.shop.fields.MoneyField')(null=True, max_digits=10, decimal_places=2, blank=True)),
            ('billing_detail_state', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('user_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('billing_detail_first_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('shipping_detail_street', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('billing_detail_email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('discount_total', self.gf('cartridge.shop.fields.MoneyField')(null=True, max_digits=10, decimal_places=2, blank=True)),
        ))
        db.send_create_signal('shop', ['Order'])

        # Adding model 'Cart'
        db.create_table('shop_cart', (
            ('last_updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('shop', ['Cart'])

        # Adding model 'CartItem'
        db.create_table('shop_cartitem', (
            ('sku', self.gf('cartridge.shop.fields.SKUField')(max_length=20)),
            ('total_price', self.gf('cartridge.shop.fields.MoneyField')(default='0', null=True, max_digits=10, decimal_places=2, blank=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('image', self.gf('django.db.models.fields.CharField')(max_length=200, null=True)),
            ('unit_price', self.gf('cartridge.shop.fields.MoneyField')(default='0', null=True, max_digits=10, decimal_places=2, blank=True)),
            ('cart', self.gf('django.db.models.fields.related.ForeignKey')(related_name='items', to=orm['shop.Cart'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('quantity', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('shop', ['CartItem'])

        # Adding model 'OrderItem'
        db.create_table('shop_orderitem', (
            ('sku', self.gf('cartridge.shop.fields.SKUField')(max_length=20)),
            ('total_price', self.gf('cartridge.shop.fields.MoneyField')(default='0', null=True, max_digits=10, decimal_places=2, blank=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('unit_price', self.gf('cartridge.shop.fields.MoneyField')(default='0', null=True, max_digits=10, decimal_places=2, blank=True)),
            ('order', self.gf('django.db.models.fields.related.ForeignKey')(related_name='items', to=orm['shop.Order'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('quantity', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('shop', ['OrderItem'])

        # Adding model 'ProductAction'
        db.create_table('shop_productaction', (
            ('timestamp', self.gf('django.db.models.fields.IntegerField')()),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(related_name='actions', to=orm['shop.Product'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('total_purchase', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('total_cart', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('shop', ['ProductAction'])

        # Adding unique constraint on 'ProductAction', fields ['product', 'timestamp']
        db.create_unique('shop_productaction', ['product_id', 'timestamp'])

        # Adding model 'Sale'
        db.create_table('shop_sale', (
            ('valid_from', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('valid_to', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('discount_percent', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=4, decimal_places=2, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('discount_exact', self.gf('cartridge.shop.fields.MoneyField')(null=True, max_digits=10, decimal_places=2, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('discount_deduct', self.gf('cartridge.shop.fields.MoneyField')(null=True, max_digits=10, decimal_places=2, blank=True)),
        ))
        db.send_create_signal('shop', ['Sale'])

        # Adding M2M table for field products on 'Sale'
        db.create_table('shop_sale_products', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('sale', models.ForeignKey(orm['shop.sale'], null=False)),
            ('product', models.ForeignKey(orm['shop.product'], null=False))
        ))
        db.create_unique('shop_sale_products', ['sale_id', 'product_id'])

        # Adding M2M table for field categories on 'Sale'
        db.create_table('shop_sale_categories', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('sale', models.ForeignKey(orm['shop.sale'], null=False)),
            ('category', models.ForeignKey(orm['shop.category'], null=False))
        ))
        db.create_unique('shop_sale_categories', ['sale_id', 'category_id'])

        # Adding model 'DiscountCode'
        db.create_table('shop_discountcode', (
            ('free_shipping', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('valid_from', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('valid_to', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('code', self.gf('cartridge.shop.fields.DiscountCodeField')(unique=True, max_length=20)),
            ('min_purchase', self.gf('cartridge.shop.fields.MoneyField')(null=True, max_digits=10, decimal_places=2, blank=True)),
            ('discount_percent', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=4, decimal_places=2, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('discount_exact', self.gf('cartridge.shop.fields.MoneyField')(null=True, max_digits=10, decimal_places=2, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('discount_deduct', self.gf('cartridge.shop.fields.MoneyField')(null=True, max_digits=10, decimal_places=2, blank=True)),
        ))
        db.send_create_signal('shop', ['DiscountCode'])

        # Adding M2M table for field products on 'DiscountCode'
        db.create_table('shop_discountcode_products', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('discountcode', models.ForeignKey(orm['shop.discountcode'], null=False)),
            ('product', models.ForeignKey(orm['shop.product'], null=False))
        ))
        db.create_unique('shop_discountcode_products', ['discountcode_id', 'product_id'])

        # Adding M2M table for field categories on 'DiscountCode'
        db.create_table('shop_discountcode_categories', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('discountcode', models.ForeignKey(orm['shop.discountcode'], null=False)),
            ('category', models.ForeignKey(orm['shop.category'], null=False))
        ))
        db.create_unique('shop_discountcode_categories', ['discountcode_id', 'category_id'])

    def backwards(self, orm):

        # Deleting model 'ProductOption'
        db.delete_table('shop_productoption')

        # Deleting model 'Category'
        db.delete_table('shop_category')

        # Deleting model 'Product'
        db.delete_table('shop_product')

        # Removing M2M table for field keywords on 'Product'
        db.delete_table('shop_product_keywords')

        # Removing M2M table for field categories on 'Product'
        db.delete_table('shop_product_categories')

        # Deleting model 'ProductImage'
        db.delete_table('shop_productimage')

        # Deleting model 'ProductVariation'
        db.delete_table('shop_productvariation')

        # Deleting model 'Order'
        db.delete_table('shop_order')

        # Deleting model 'Cart'
        db.delete_table('shop_cart')

        # Deleting model 'CartItem'
        db.delete_table('shop_cartitem')

        # Deleting model 'OrderItem'
        db.delete_table('shop_orderitem')

        # Deleting model 'ProductAction'
        db.delete_table('shop_productaction')

        # Removing unique constraint on 'ProductAction', fields ['product', 'timestamp']
        db.delete_unique('shop_productaction', ['product_id', 'timestamp'])

        # Deleting model 'Sale'
        db.delete_table('shop_sale')

        # Removing M2M table for field products on 'Sale'
        db.delete_table('shop_sale_products')

        # Removing M2M table for field categories on 'Sale'
        db.delete_table('shop_sale_categories')

        # Deleting model 'DiscountCode'
        db.delete_table('shop_discountcode')

        # Removing M2M table for field products on 'DiscountCode'
        db.delete_table('shop_discountcode_products')

        # Removing M2M table for field categories on 'DiscountCode'
        db.delete_table('shop_discountcode_categories')


    models = {
        'core.keyword': {
            'Meta': {'object_name': 'Keyword'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'pages.page': {
            'Meta': {'object_name': 'Page'},
            '_keywords': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            '_order': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'content_model': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'description': ('mezzanine.core.fields.HtmlField', [], {'blank': 'True'}),
            'expiry_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_footer': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'in_navigation': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'keywords': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Keyword']", 'symmetrical': 'False', 'blank': 'True'}),
            'login_required': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['pages.Page']"}),
            'publish_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'short_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'titles': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True'})
        },
        'shop.cart': {
            'Meta': {'object_name': 'Cart'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
        },
        'shop.cartitem': {
            'Meta': {'object_name': 'CartItem'},
            'cart': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': "orm['shop.Cart']"}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'quantity': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'sku': ('cartridge.shop.fields.SKUField', [], {'max_length': '20'}),
            'total_price': ('cartridge.shop.fields.MoneyField', [], {'default': "'0'", 'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'unit_price': ('cartridge.shop.fields.MoneyField', [], {'default': "'0'", 'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'shop.category': {
            'Meta': {'object_name': 'Category', '_ormbases': ['pages.Page']},
            'content': ('mezzanine.core.fields.HtmlField', [], {}),
            'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['pages.Page']", 'unique': 'True', 'primary_key': 'True'})
        },
        'shop.discountcode': {
            'Meta': {'object_name': 'DiscountCode'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['shop.Category']", 'symmetrical': 'False', 'blank': 'True'}),
            'code': ('cartridge.shop.fields.DiscountCodeField', [], {'unique': 'True', 'max_length': '20'}),
            'discount_deduct': ('cartridge.shop.fields.MoneyField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'discount_exact': ('cartridge.shop.fields.MoneyField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'discount_percent': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '4', 'decimal_places': '2', 'blank': 'True'}),
            'free_shipping': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'min_purchase': ('cartridge.shop.fields.MoneyField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'products': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['shop.Product']", 'symmetrical': 'False', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'valid_from': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'valid_to': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        'shop.order': {
            'Meta': {'object_name': 'Order'},
            'additional_instructions': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'billing_detail_city': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'billing_detail_country': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'billing_detail_email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'billing_detail_first_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'billing_detail_last_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'billing_detail_phone': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'billing_detail_postcode': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'billing_detail_state': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'billing_detail_street': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'discount_code': ('cartridge.shop.fields.DiscountCodeField', [], {'max_length': '20', 'blank': 'True'}),
            'discount_total': ('cartridge.shop.fields.MoneyField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item_total': ('cartridge.shop.fields.MoneyField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'shipping_detail_city': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'shipping_detail_country': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'shipping_detail_first_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'shipping_detail_last_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'shipping_detail_phone': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'shipping_detail_postcode': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'shipping_detail_state': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'shipping_detail_street': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'shipping_total': ('cartridge.shop.fields.MoneyField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'shipping_type': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'total': ('cartridge.shop.fields.MoneyField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'user_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'shop.orderitem': {
            'Meta': {'object_name': 'OrderItem'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': "orm['shop.Order']"}),
            'quantity': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'sku': ('cartridge.shop.fields.SKUField', [], {'max_length': '20'}),
            'total_price': ('cartridge.shop.fields.MoneyField', [], {'default': "'0'", 'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'unit_price': ('cartridge.shop.fields.MoneyField', [], {'default': "'0'", 'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'})
        },
        'shop.product': {
            'Meta': {'object_name': 'Product'},
            '_keywords': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'available': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'products'", 'blank': 'True', 'to': "orm['shop.Category']"}),
            'content': ('mezzanine.core.fields.HtmlField', [], {}),
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'description': ('mezzanine.core.fields.HtmlField', [], {'blank': 'True'}),
            'expiry_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'keywords': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['core.Keyword']", 'symmetrical': 'False', 'blank': 'True'}),
            'publish_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'sale_from': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'sale_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'sale_price': ('cartridge.shop.fields.MoneyField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'sale_to': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'short_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'unit_price': ('cartridge.shop.fields.MoneyField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'})
        },
        'shop.productaction': {
            'Meta': {'unique_together': "(('product', 'timestamp'),)", 'object_name': 'ProductAction'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'actions'", 'to': "orm['shop.Product']"}),
            'timestamp': ('django.db.models.fields.IntegerField', [], {}),
            'total_cart': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'total_purchase': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'shop.productimage': {
            'Meta': {'object_name': 'ProductImage'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'file': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'images'", 'to': "orm['shop.Product']"})
        },
        'shop.productoption': {
            'Meta': {'object_name': 'ProductOption'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('cartridge.shop.fields.OptionField', [], {'max_length': '50', 'null': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {})
        },
        'shop.productvariation': {
            'Meta': {'object_name': 'ProductVariation'},
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['shop.ProductImage']", 'null': 'True', 'blank': 'True'}),
            'num_in_stock': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'option1': ('cartridge.shop.fields.OptionField', [], {'max_length': '50', 'null': 'True'}),
            'option2': ('cartridge.shop.fields.OptionField', [], {'max_length': '50', 'null': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'variations'", 'to': "orm['shop.Product']"}),
            'sale_from': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'sale_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'sale_price': ('cartridge.shop.fields.MoneyField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'sale_to': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'sku': ('cartridge.shop.fields.SKUField', [], {'unique': 'True', 'max_length': '20'}),
            'unit_price': ('cartridge.shop.fields.MoneyField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'})
        },
        'shop.sale': {
            'Meta': {'object_name': 'Sale'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['shop.Category']", 'symmetrical': 'False', 'blank': 'True'}),
            'discount_deduct': ('cartridge.shop.fields.MoneyField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'discount_exact': ('cartridge.shop.fields.MoneyField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'discount_percent': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '4', 'decimal_places': '2', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'products': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['shop.Product']", 'symmetrical': 'False', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'valid_from': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'valid_to': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['shop']
