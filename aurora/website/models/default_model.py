#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author Zhett
@email stratos33290@gmail.com
@version 0.1
@copyright 2013 Zhett
"""

from django.contrib.auth.models import User
from django.db import models
from website.models import *

#!/usr/bin/env python
# -*- coding: utf-8 -*-


from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _
from webstore.models import *
from compta.models import Account


class Entities(models.Model):
    """Define Partner model to bdd"""
    user = models.ForeignKey(User, unique=True, related_name='profile')
    parent = models.ForeignKey("Entities", related_name="Parent", null=True, blank=True)
    TYPE_CHOICES = (('RE', 'Reseller'),
                    ('SA', 'SubAccount'),
                    ('TR', 'Trader'),
                    ('CU', 'Customer'),)

    shop = models.ForeignKey('Shop', null=True, blank=True)
    type_of = models.CharField(max_length=2, choices=TYPE_CHOICES, null=True, blank=True)

    contact_phone = models.CharField(_('phone fix'.decode("utf8")), max_length=14, null=True, blank=True)
    contact_gsm = models.CharField(_('phone mobile'.decode("utf8")), max_length=60, null=True, blank=True)
    contact_fax = models.CharField(_('fax'.decode("utf8")), max_length=14, null=True, blank=True)

    email_confirm = models.BooleanField(_("email confirmation".decode('utf8')), default=False)
    optin = models.BooleanField(_("Newsletter ?".decode('utf8')), default=False)
    subscribe_by = models.ForeignKey(User, null=True, blank=True, related_name="agent_subscriber")
    follow_by = models.ForeignKey(User, null=True, blank=True, related_name="agent_follower")

    def get_fullname(self):
        return unicode(self.user.get_full_name())

    def get_linked_account(self):
        if self.type_of == "RE":
            return Reseller.objects.get(entity=self)
        elif self.type_of == "SA":
            return SubAccount.objects.get(entity=self)
        elif self.type_of == "TR":
            return Trader.objects.get(entity=self)
        elif self.type_of == "CU":
            return Customer.objects.get(entity=self)
        else:
            return False

    def get_addresses(self):
        """Return list of all addresses to current Partner"""
        try:
            list_adr = Addresse.objects.filter(entities=self)
        except:
            return None
        else:
            return list_adr

    def get_address_toString(self):
        account = self.get_linked_account()
        address = account.invoice_addresse
        txt = address.street
        if address.street2 is not None:
            txt += ' ' + address.street2
            if address.street3 is not None:
                txt += ' ' + address.street3
        txt += ' ' + address.zipcode + ' ' + address.city
        return txt

    def get_parent(self):
        """this method is used to pick the parent of a partner"""
        tab_parent = [self]
        tmp = self

        while True:
            try:
                tab_parent.append(tmp.parent)
                tmp = tmp.parent
            except:
                break

        tab_parent.reverse()

        return tab_parent

    def __unicode__(self):
        return self.id

    class Meta:
        app_label = "webstore"


class Addresse(models.Model):
    """Define model of addresse to partner"""
    # We fill this name with full partner name
    entities = models.ForeignKey("Entities", null=True, blank=True)

    name = models.CharField(_("address name"), max_length=60, null=True, blank=True)
    street = models.CharField(_("Address"), max_length=38, null=True, blank=True)
    street2 = models.CharField(_("Address2".decode("utf8")), max_length=38, blank=True, null=True)
    street3 = models.CharField(_("Address3".decode("utf8")), max_length=38, blank=True, null=True)

    zipcode = models.CharField(_("ZipCode"), max_length=10, null=True, blank=True)
    city = models.CharField(_("City"), max_length=60, null=True, blank=True)
    country = models.CharField(_("Country"), max_length=60, null=True, blank=True)
    comment = models.CharField(_("Comment"), max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def get_datas(self):
        all_datas = self.street, self.street2, self.street3, self.zipcode, self.city, self.country

        return all_datas

    def to_string(self):
        addresse = unicode(self.street + "\n" + self.street2 + "\n" + self.street3 + "\n" + self.zipcode + " " + self.city + "\n" + self.country)
        return addresse

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = "webstore"


class Reseller(models.Model):
    entity = models.ForeignKey("Entities", related_name='entity', null=True, blank=True)
    rib_iban = models.CharField(_('RIB ou IBAN'), max_length=60, null=True, blank=True)
    bic = models.CharField(_('BIC'), max_length=65, null=True, blank=True)
    owner_bank = models.CharField(_('compt owner'), max_length=60, null=True, blank=True)
    owner_addresse = models.ForeignKey("Addresse", related_name='Owner Addresse', null=True, blank=True)
    siege_addresse = models.ForeignKey("Addresse", related_name='Siege Addresse', null=True, blank=True)
    invoice_addresse = models.ForeignKey("Addresse", related_name='Invoice Addresse', null=True, blank=True)
    domiciliation = models.CharField(_('Domiciliation du compte'), max_length=24, null=True, blank=True)

    assujetti_tva = models.BooleanField(_("Assujetti à la tva".decode("utf8")))
    company = models.CharField(_('Raison sociale'), max_length=60, null=True, blank=True)
    siret = models.CharField(_('SIRET'), max_length=18, null=True, blank=True, unique=False, help_text=_("Pour modifier votre numéro de SIRET, merci de nous contacter.".decode('utf8')))
    vat_number = models.CharField(_('Numéro T.V.A'.decode("utf8")), max_length=60, null=True, blank=True, help_text=_("Pour modifier votre numéro de TVA, merci de nous contacter.".decode('utf8')))
    ape_code = models.CharField(_('Code APE'), max_length=5, null=True, blank=True)
    activity = models.CharField(_("Métier de l'entreprise".decode("utf8")), max_length=60, null=True, blank=True)
    website = models.CharField(_('Site web'), max_length=60, null=True, blank=True)
    compta_account_ac = models.ForeignKey("compta.Account", related_name='reseller_account_ac', null=True, blank=True)
    compta_account_ve = models.ForeignKey("compta.Account", related_name='reseller_account_ve', null=True, blank=True)

    def get_fullname(self):
        return unicode(self.entity.user.get_full_name())

    def get_user(self):
        return self.entity.user

    def __unicode__(self):
        return self.company

    class Meta:
        app_label = "webstore"


class Customer(models.Model):
    entity = models.ForeignKey("Entities", related_name='entity1', null=True, blank=True)
    rib_iban = models.CharField(_('RIB ou IBAN'), max_length=60, null=True, blank=True)
    bic = models.CharField(_('BIC'), max_length=65, null=True, blank=True)
    owner_bank = models.CharField(_('Titulaire du compte'), max_length=60, null=True, blank=True)
    owner_addresse = models.ForeignKey("Addresse", related_name='Owner Addresse1', null=True, blank=True)
    siege_addresse = models.ForeignKey("Addresse", related_name='Siege Addresse1', null=True, blank=True)
    invoice_addresse = models.ForeignKey("Addresse", related_name='Invoice Addresse1', null=True, blank=True)
    domiciliation = models.CharField(_('Domiciliation du compte'), max_length=24, null=True, blank=True)

    company = models.CharField(_('Raison sociale'), max_length=60, null=True, blank=True)
    siret = models.CharField(_('SIRET'), max_length=18, null=True, blank=True, unique=False, help_text=_("Pour modifier votre numéro de SIRET, merci de nous contacter.".decode('utf8')))
    assujetti_tva = models.BooleanField(_("Assujetti à la tva".decode("utf8")))
    vat_number = models.CharField(_('VAT number'.decode("utf8")), max_length=60, null=True, blank=True, help_text=_("Pour modifier votre numéro de TVA, merci de nous contacter.".decode('utf8')))
    ape_code = models.CharField(_('Code APE'), max_length=5, null=True, blank=True)
    activity = models.CharField(_("job".decode("utf8")), max_length=60, null=True, blank=True)
    website = models.CharField(_('Website'), max_length=60, null=True, blank=True)

    compta_account_ac = models.ForeignKey("compta.Account", related_name='customer_account_ac', null=True, blank=True)
    compta_account_ve = models.ForeignKey("compta.Account", related_name='customer_account_ve', null=True, blank=True)

    def get_fullname(self):
        return unicode(self.entity.user.get_full_name())

    def get_user(self):
        return self.entity.user

    def __unicode__(self):
        return str(self.id)

    class Meta:
        app_label = "webstore"


class Trader(models.Model):
    entity = models.ForeignKey("Entities", related_name='entity2', null=True, blank=True)
    shop = models.ForeignKey("Shop", related_name='trader_shop', null=True, blank=True)

    def get_gestco_groups(self):
        list_groups = GestcoAssociates.objects.filter(trader=self)
        return list_groups

    def get_fullname(self):
        return unicode(self.entity.user.get_full_name())

    def get_user(self):
        return self.entity.user

    def __unicode__(self):
        return str(self.id)
        # return "-".join([str(self.id), str(self.shop.name)])

    class Meta:
        app_label = "webstore"


class SubAccount(models.Model):
    entity = models.ForeignKey("Entities", related_name='entity3', null=True, blank=True)
    reseller = models.ForeignKey("Reseller", related_name='Reseller', null=True, blank=True)
    shop = models.ForeignKey("Shop", related_name='sub_shop', null=True, blank=True)

    def get_fullname(self):
        return str(self.entity.user.get_full_name())

    def get_user(self):
        return self.entity.user

    def __unicode__(self):
        # return "-".join([str(self.id), self.entity])
        return str(self.id)

    class Meta:
        app_label = "webstore"


class Supplier(models.Model):
    """Define model of suppliers"""
    company = models.CharField(_('Societe'), max_length=60, help_text="", null=True, blank=True)
    user = models.ForeignKey(User, unique=False)
    is_active = models.BooleanField(_("Est actif"))
    compta_account_ac = models.ForeignKey("compta.Account", related_name='supplier_account_ac', null=True, blank=True)
    compta_account_ve = models.ForeignKey("compta.Account", related_name='supplier_account_ve', null=True, blank=True)
    categ_code_name = models.CharField(_('Categ CodeName'), max_length=255, help_text="", null=True, blank=True)

    def __unicode__(self):
        return str(self.id)
        # return self.company

    class Meta:
        app_label = "webstore"


class SavesAccount(models.Model):
    """Manage account for the saves categ"""
    number = models.CharField(_("Unique id"), max_length=255, null=False, blank=True)
    customer = models.ForeignKey("Entities", related_name="sub_custo")
    order = models.ForeignKey("Order", null=True, blank=True)
    subscription = models.ForeignKey("Subscription", related_name='souscription', null=True, blank=True)
    date_add = models.DateTimeField(auto_now_add=True, auto_now=False)
    product_variant = models.ForeignKey("ProductVariant")
    lastname = models.CharField(_("Firstname"), max_length=50, null=True, blank=True)
    firstname = models.CharField(_("Lastname"), max_length=50, null=True, blank=True)
    email = models.EmailField(_("Email"), max_length=254, null=True, blank=True)
    login = models.CharField(_("Login"), max_length=50, null=True, blank=True)
    is_allocated = models.BooleanField(_("Is Allocated"), default=False)

    def __unicode__(self):
        return str(self.customer) + '-' + str(self.number)

    def save(self, *args, **kwargs):
        if not self.number:
            number = str(self.customer.id) + "-" + str(self.order.id) + "-" + str(len(SavesAccount.objects.filter(order=self.order)))
            self.number = number
        super(SavesAccount, self).save(*args, **kwargs)

    class Meta:
        app_label = "webstore"
