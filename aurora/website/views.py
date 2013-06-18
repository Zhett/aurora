# Create your views here.
# -*- coding: utf-8 -*-
from django.shortcuts import redirect, render, HttpResponse, render_to_response
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template import RequestContext
from django.conf import settings
from api.jarvis import *
from webstore.models import *
from django.core.cache import cache
from django.db.models import Q
from webstore.decorators import *
from itertools import chain
from shopbackoffice.forms import *
from backoffice.forms import *
from django.utils.translation import ugettext as _
from django.forms.widgets import HiddenInput
from django.http import Http404
from api.libs.product_lib import calculate_price
from django.template.defaultfilters import slugify
from django.http import Http404
from api.libs.payline import *

import logging
import pprint
import json


logger = logging.getLogger('logview.userlogins')


# def test(request):
#     # params = {'code_name': "login_params", 'sender': "test@mail.com", "receiver": 'anthony.bayle@cprodirect.fr', "shop": request.session['shop'], 'tags': {"_TEST_": "ok c cook"}}
#     # r = t.mod.send_generic_mail(params)
#     # testdumps = {"order_confirmation": {"email": True, "message": True}}

#     # request.session['shop'].notifs_ban = json.dumps(testdumps)
#     # request.session['shop'] = request.session['shop']
#     # params = {"code_name": 'order_confirmation',
#     #                     "sender": request.user,
#     #                     "receiver": request.user,
#     #                     "shop": request.session['shop'],
#     #                     "tags": {"test": "okyyyyy"}
#     #                 }
#     # r = t.mod.send_notif(params)
#     t = Jarvis("Shield")
#     t.mod.include_options([21266, 27771], request.session['shop'])
#     # return HttpResponse("test")
#     # a = Customer.objects.filter(company__contains="k")
#     # b = User.objects.filter(last_name__contains="t")
#     # c = list(chain(a, b))
#     # print c
#     # return HttpResponse(c)
#     # params = dict(filter=dict(type_of="PRD"), exclude=dict(id__contains=1))

#     # print get_products_list(params)
#     return HttpResponse("Test Blackwidow")


@is_shop_public
def home(request):
    """First page display at login"""
    homepage_content = request.session['shop'].get_homepage(request.LANGUAGE_CODE)[0]
    return render(request, "home.html", {"homepage_content": homepage_content})


def index_page(request):

    if "user_infos" in request.session:
        return redirect("/home")
    else:
        return redirect(login_user)


def login_user(request, next=None):
    """Login form view
    @return if success return to home page
    """
    if request.POST:
        if "next" in request.POST:
            next = request.POST['next']

        usern = request.POST['login'][:29]
        password = request.POST['password']
        user = authenticate(username=usern, password=password)

        if user is not None:
            if user.is_active:
                try:
                    try:
                        Entities.objects.get(user=user, shop=request.session['shop'])
                    except Exception, e:
                        # TODO : WHY ? BECAUSE POUR SE LOGGUER SUR UNE AUTRE BOUTIQUE QUE LA PRINCIPALE ? => provoque des erreurs
                        # if not Shop.objects.filter(reseller__entity__user=user):
                        return redirect('/')
                except Exception, e:
                    logger.info("cannot login %s", e)
                    return redirect('/logout?login=failed')
                else:
                    login(request, user)
                    list_group = [i.name for i in request.user.groups.all()]
                    request.session['groups'] = list_group

                    if 'admin' in list_group and not next:
                        return redirect('/backoffice/admin')

                    request.session['shield'].mod.load_user(user)
                    request.session['user_infos'] = request.session['shield']
                    request.session['main_categories'] = request.session['shield'].mod.load_main_order()
                    request.session['categories'] = request.session['shield'].mod.load_shopshelf()
                    request.session['thor'] = Jarvis("Thor")

                    if next:
                        return redirect(next)

                    if 'reseller' in list_group:
                        # TODO Make a var for stock subscribe options (with shopshelf)
                        # request.session['categories'] = request.session['shield'].mod.get_all_categories
                        request.session['list_shops'] = Shop.objects.filter(reseller=request.session['user_infos'].mod.entity.get_linked_account(), is_active=True).exclude(name="")
                        request.session['list_shops_to_configure'] = Shop.objects.filter(reseller=request.session['user_infos'].mod.entity.get_linked_account(), name=None, is_active=False)
                        return redirect('/backoffice/shop')

            if next:
                return redirect(next)
            else:
                return redirect('/')
        else:
            if request.session['shop'].is_public:
                # logout(request)
                return render(request, "login_public.html", {"msg": _("Login and/or password incorrect")})
            else:
                # logout(request)
                return render(request, "login_private.html", {"msg": _("Login and/or password incorrect")})

    if request.session['shop'].is_public and not "/backoffice" in request.path:
        return render(request, "login_public.html")
    else:
        return render(request, "login_private.html")


def logout_user(request):
    """Logout view
    @return redirect to Login page
    """
    logout(request)
    return redirect("/login")


@is_shop_public
def router(request, url_rewrite):
    """This view routing request send with url-rewrite type, category or product"""
    from django.shortcuts import get_list_or_404

    try:
        category_lg = CategoryLang.objects.get(url_rewrite=url_rewrite, category__is_active=True)
    except Exception, e:
        # if not category found, try with product
        try:
            product_lg = ProductLang.objects.get(product__is_active=True, url_rewrite=url_rewrite)
        except:
            raise Http404
        else:
            catalog = build_catalog([product_lg.product, ], request)

            try:
                if product_lg.product.main_category.code_name == "save":
                    return HttpResponse(save_details(request, ProductVariant.objects.get(product=product_lg.product).reference_in))
            except:
                return Http404
            try:
                if product_lg.product.main_category.code_name == "location":
                    return HttpResponse(rent_view_details(request, product_lg.product.id))
            except:
                return Http404
            try:
                if product_lg.product.main_category.code_name == "emailing":
                    return HttpResponse(emailing(request))
            except:
                return Http404
            try:
                if product_lg.product.main_category.code_name == "websites":
                    return HttpResponse(websites(request))
            except:
                return Http404

            if product_lg.product.category.get_genea()[0].code_name == "software":
                category_lg = Categories.objects.get(code_name="software").get_trans(lg_code=request.LANGUAGE_CODE.upper())
            else:
                category_lg = product_lg.product.category.get_trans(request.LANGUAGE_CODE)
            try:
                qty = request.session['thor'].mod.basket[product_lg.product.supplier][product_lg.product.get_variants()[0]]['qty']
            except:
                qty = 0

            screenshots = list()

            for attr in product_lg.product.get_variants()[0].attributes.all():
                if attr.code_name == "screenshot":
                    screenshots.append(attr.value)

            return render(request, "generic_product.html", {"META_TITLE": product_lg.meta_title,
                                                            "META_DESCRIPTION": product_lg.meta_description,
                                                            "META_KEYWORDS": product_lg.meta_keywords,
                                                            "catalog": catalog[0],
                                                            "category": category_lg,
                                                            "screenshots": screenshots,
                                                            "qty": qty})
    else:
        # If category find, it is special category
        try:
            return globals()[str(category_lg.category.code_name).lower()](request)
        except Exception, e:
            logger.info("router switch : %s" % e)
            # Not special category, try get all it products
            try:
                datas = get_list_or_404(Product.objects.exclude(id__in=request.session['shield'].mod.get_products_ban), category=category_lg.category, is_active=True, type_of='PRD')
            except Exception, e:
                # No products found, have sub categories to display
                list_subcategories = category_lg.category.get_childrens()
                if category_lg.category.get_genea()[0].code_name == "software":
                    category_lg = Categories.objects.get(code_name="software").get_trans(lg_code=request.LANGUAGE_CODE.upper())

                if not list_subcategories:
                    raise Http404
                else:
                    return render(request, "generic_list_subcategories.html", {"META_TITLE": category_lg.meta_title,
                                                                               "META_DESCRIPTION": category_lg.meta_description,
                                                                               "META_KEYWORDS": category_lg.meta_keywords,
                                                                               "list_subcategories": list_subcategories,
                                                                               "category": category_lg})
            else:
                paginator = Paginator(datas, settings.NB_PRD_LIST)  # Show 25 contacts per page
                page = request.GET.get('page')

                try:
                    list_prd = paginator.page(page)
                except PageNotAnInteger:
                    # If page is not an integer, deliver first page.
                    list_prd = paginator.page(1)
                except EmptyPage:
                    # If page is out of range (e.g. 9999), deliver last page of results.
                    list_prd = paginator.page(paginator.num_pages)

                catalog = build_catalog(list_prd, request)
                if category_lg.category.get_genea()[0].code_name == "software":
                    category_lg = Categories.objects.get(code_name="software").get_trans(lg_code=request.LANGUAGE_CODE.upper())

                return render(request, "generic_list_products.html", {"datas": catalog,
                                                                      "META_TITLE": category_lg.meta_title,
                                                                      "META_DESCRIPTION": category_lg.meta_description,
                                                                      "META_KEYWORDS": category_lg.meta_keywords,
                                                                      "category": category_lg,
                                                                      "has_previous": list_prd.has_previous,
                                                                      "has_next": list_prd.has_next,
                                                                      "previous_page_number": list_prd.previous_page_number,
                                                                      "page_number": list_prd.number,
                                                                      "num_pages": list_prd.paginator.num_pages,
                                                                      "num_pages_pag": range(0, list_prd.paginator.num_pages),
                                                                      "next_page_number": list_prd.next_page_number})


def offline(request):
    return HttpResponse("<b>Site introuvable</b><br/>Le domaine que vous demandez n'existe pas.")


@is_shop_public
def location(request):
    list_prds = dict()
    categ = Categories.objects.get(code_name="location")
    categ_lg = categ.get_trans()  # CategoryLang.objects.get(category=categ, language__code_iso=request.LANGUAGE_CODE.upper())
    prds = Product.objects.filter(category=categ, type_of='PRD')

    for prd in prds:
        prd_lg = ProductLang.objects.get(product=prd)
        list_prds[prd] = prd_lg

    return render(request, "categories/location/rent.html", {"category": categ_lg,
                                                             "list_products": list_prds,
                                                             "META_TITLE": categ_lg.meta_title,
                                                             "META_DESCRIPTION": categ_lg.meta_description,
                                                             "META_KEYWORDS": categ_lg.meta_keywords})


@is_shop_public
def emailing(request):
    categ = Categories.objects.get(code_name="emailing")
    categ_lg = categ.get_trans()
    prds = Product.objects.filter(category=categ, type_of='PRD')
    catalog = build_catalog(prds, request)
    try:
        #print request.session['thor'].mod.basket[prds[0].supplier][prds[0].get_variants()[0]]
        qty = request.session['thor'].mod.basket[prds[0].supplier][prds[0].get_variants()[0]]['qty']
    except Exception, e:
        print e
        qty = 0
    #print qty
    return render(request, "categories/emailing/emailing.html", {"category": categ_lg,
                                                                 "catalog": catalog,
                                                                 "META_TITLE": categ_lg.meta_title,
                                                                 "META_DESCRIPTION": categ_lg.meta_description,
                                                                 "META_KEYWORDS": categ_lg.meta_keywords,
                                                                 "qty": qty})


@is_shop_public
def websites(request):
    categ = Categories.objects.get(code_name="websites")
    categ_lg = categ.get_trans()  # CategoryLang.objects.get(category=categ, language__code_iso=request.LANGUAGE_CODE.upper())
    prds = Product.objects.filter(category=categ, type_of='PRD')
    catalog = build_catalog(prds, request)
    return render(request, "categories/websites/websites.html", {"category": categ_lg,
                                                                 "catalog": catalog,
                                                                 "META_TITLE": categ_lg.meta_title,
                                                                 "META_DESCRIPTION": categ_lg.meta_description,
                                                                 "META_KEYWORDS": categ_lg.meta_keywords})


@is_shop_public
def adimpo_conso(request):
    import MySQLdb
    #list_models = None
    #if request.POST:
    #    if "modele" not in request.POST:
    categ = Categories.objects.get(code_name="adimpo_conso")
    categ_lg = categ.get_trans()  # CategoryLang.objects.get(category=categ, language__code_iso=request.LANGUAGE_CODE.upper())

    if cache.get("conso_configurator") and cache.get("adimpo_categories"):
        configurator = cache.get("conso_configurator")
        categs = cache.get("adimpo_categories")
    else:
        conn = MySQLdb.connect(host=settings.BDD_HOST, user=settings.BDD_USER, passwd=settings.BDD_PASSWORD, db="icom_ingram")
        c = conn.cursor()
        c.execute("SELECT manufacturer, model_type FROM modeles GROUP BY model_type")
        configurator = dict()
        categs = Categories.objects.filter(parent=categ)

        brands = [b.value.strip().upper() for b in Attributes.objects.filter(code_name="marque")]
        for manufacturer, model in c.fetchall():
            if manufacturer.strip().upper() in brands:
                manufacturer = 'XEROX' if manufacturer.strip().upper() == 'TEKTRONIX' else manufacturer
                try:
                    configurator[manufacturer.upper()].append(model.replace(manufacturer, '').upper())
                except:
                    configurator[manufacturer.upper()] = [model.replace(manufacturer, '').upper(), ]
        c.close()
        cache.set("conso_configurator", configurator, 3600)
        cache.set("adimpo_categories", categs, 3600)

    if "guest" not in request.session['groups']:
        supplier = Supplier.objects.get(company='adimpo')
        prds = list()
        try:
            last_purchase = LastPurchase.objects.get(supplier=supplier, customer=request.session['user_infos'].mod.entity)
            prds_v = ProductVariant.objects.filter(id__in=json.loads(last_purchase.purchases))

            try:
                list_ban_prd = request.session['shield'].mod.get_products_ban
                list_ban_prd.extend(request.session['shield'].mod.get_cpro_products_ban)
            except:
                list_ban_prd = []
            for tmp in prds_v:
                if tmp.product.id in list_ban_prd:
                    prds_v.pop(tmp.product)
        except:
            last_purchase = []
            prds_v = []

        for variant in prds_v:
            prds.append(variant.product)
        recent = build_catalog(prds, request)
    else:
        recent = None

    top = ["BROTHER", "CANON", "EPSON", "HEWLETT PACKARD", "IBM", "LEXMARK", "OKI", "SAMSUNG", "RICOH", "XEROX"]
    return render(request, "categories/consommables/consommables.html", {"category": categ_lg,
                                                                         "configurator": configurator,
                                                                         "categs": categs,
                                                                         "top": top,
                                                                         "recent": recent,
                                                                         "META_TITLE": categ_lg.meta_title,
                                                                         "META_DESCRIPTION": categ_lg.meta_description,
                                                                         "META_KEYWORDS": categ_lg.meta_keywords})


@is_shop_public
def save(request):
    try:
        categ = Categories.objects.get(code_name="save")
        categ_lg = categ.get_trans()  # CategoryLang.objects.get(category=categ, language__code_iso=request.LANGUAGE_CODE.upper())
        prds = Product.objects.filter(category=categ, type_of='PRD')
        catalog = build_catalog(prds, request)
    except Exception, e:
        print e
    return render(request, "categories/sauvegarde/sauvegarde.html", {"category": categ_lg,
                                                                     "catalog": catalog,
                                                                     "META_TITLE": categ_lg.meta_title,
                                                                     "META_DESCRIPTION": categ_lg.meta_description,
                                                                     "META_KEYWORDS": categ_lg.meta_keywords})


@is_shop_public
def save_details(request, prd_refin):
    try:
        categ = Categories.objects.get(code_name="save")
        categ_lg = categ.get_trans()  # CategoryLang.objects.get(category=categ, language__code_iso=request.LANGUAGE_CODE.upper())
        prd = ProductVariant.objects.get(reference_in=prd_refin)
        catalog = build_catalog([prd.product, ], request)
    except Exception, e:
        print e
    return render(request, "categories/sauvegarde/save_details.html", {"category": categ_lg,
                                                                     "catalog": catalog[0],
                                                                     "META_TITLE": categ_lg.meta_title,
                                                                     "META_DESCRIPTION": categ_lg.meta_description,
                                                                     "META_KEYWORDS": categ_lg.meta_keywords})



@is_shop_public
def rent_view_details(request, prd_id):
    prd = Product.objects.get(id=prd_id)
    catalog = build_catalog([prd, ], request)

    return render(request, "categories/location/rent_details.html", {'catalog': catalog[0],
                                                                     'category': prd.category.get_trans(request.LANGUAGE_CODE),
                                                                     'periods_list': settings.PERIODS_LIST_RENT})


@login_required
def renewal_subscription(request):
    list_sub_id = request.GET['list_sub_id'].split(",")
    if len(list_sub_id) == 0:
        logger.info(u"No subscription to renew")
        return True
    thor = request.session['thor']

    try:
        for sub_id in list_sub_id:
            try:
                sub = Subscription.objects.get(id=sub_id, customer=request.session['user_infos'].mod.entity)
            except Exception, e:
                logger.info("Unable to load subscription for renewal_subscription %s", e)
                continue
            params_basket = {'shop': request.session['shop'],
                             'customer': request.session['user_infos'].mod.entity.user,
                             'product_v': ProductVariant.objects.get(id=sub.product_variant_id)}
            next_month_start = calcul_days_to_start(sub.next_renewal)
            thor.mod.add_basket(params_basket, 1, True)

            # TODO Nettoyer ce mechant fix
            if sub.product_variant.product.type_of == 'RQD' and sub.product_variant.buy_price == 1500:
                params_sub_list = {'next_renewal': sub.next_renewal + relativedelta(years=1)}
                params_option = {'option': " ".join([convert_unicode_to_string(params_basket['product_v'].product.get_trans().name), ":", "<br/>",
                                                    convert_unicode_to_string(_('Period from')),
                                                    convert_unicode_to_string(sub.next_renewal.strftime('%d/%m/%Y')),
                                                    convert_unicode_to_string(_('to')),
                                                    convert_unicode_to_string(params_sub_list['next_renewal'].strftime('%d/%m/%Y')),
                                                    ":", (convert_unicode_to_string(sub.unit_price)).replace(".", ","), "&euro;"]),
                                 'product_v': params_basket['product_v'],
                                 'qty': 1
                                }
            elif sub.next_renewal.day > 10:
                params_sub_list = {'next_renewal': next_month_start + relativedelta(months=1)}
                params_option = {'option': " ".join([convert_unicode_to_string(params_basket['product_v'].product.get_trans().name), ":", "<br/>",
                                                    convert_unicode_to_string(_('Period from')),
                                                    convert_unicode_to_string(sub.next_renewal.strftime('%d/%m/%Y')),
                                                    convert_unicode_to_string(_('to')),
                                                    convert_unicode_to_string(next_month_start.strftime('%d/%m/%Y')),
                                                    ": 0,00 &euro;", "<br/>",
                                                    convert_unicode_to_string(_('Period from')),
                                                    convert_unicode_to_string(next_month_start.strftime('%d/%m/%Y')),
                                                    convert_unicode_to_string(_('to')),
                                                    convert_unicode_to_string((next_month_start + relativedelta(months=1)).strftime('%d/%m/%Y')),
                                                    ":", (convert_unicode_to_string(sub.unit_price)).replace(".", ","), "&euro;"]),
                                 'product_v': params_basket['product_v'],
                                 'qty': 1
                                 }
            else:
                params_sub_list = {'next_renewal': next_month_start}
                try:
                    params_option = {'option': " ".join([convert_unicode_to_string(params_basket['product_v'].product.get_trans().name), ":", "<br/>",
                                                        convert_unicode_to_string(_('Period from')),
                                                        convert_unicode_to_string(sub.next_renewal.strftime('%d/%m/%Y')),
                                                        convert_unicode_to_string(_('to')),
                                                        convert_unicode_to_string(next_month_start.strftime('%d/%m/%Y')),
                                                        ":", (convert_unicode_to_string(sub.unit_price)).replace(".", ","), "&euro;"]),
                                     'product_v': params_basket['product_v'],
                                     'qty': 1
                                     }
                except Exception, e:
                    print e
            thor.mod.add_subscription(sub, params_sub_list)
            thor.mod.add_option(params_option)
            request.session['thor'] = thor
    except Exception, e:
        logger.error("renewal_subscription error when renewing sub : %s", e)
        return HttpResponse(False)

    request.session['thor'] = thor
    return HttpResponse(True)


@login_required
def remove_subscription(request):
    list_sub_id = request.GET['list_sub_id'].split(",")
    if len(list_sub_id) == 0:
        logger.info(u"No subscription to remove")
        return True
    try:
        blackwidow = request.session['blackwidow']
    except:
        blackwidow = Jarvis('blackwidow')
        request.session['blackwidow'] = blackwidow
    try:
        list_id_sub = [x.id for x in Subscription.objects.filter(id__in=list_sub_id, customer=request.session['user_infos'].mod.entity)]
        blackwidow.mod.resiliate_subscription(list_id_sub)
    except Exception, e:
        logger.error("Error remove subscription %s", e)
        return HttpResponse(False)
    return HttpResponse(True)


@is_shop_public
def shop_search(request):
    """Search engine in frontend"""
    error = None
    list_results = None
    catalog = None

    if request.POST:
        keywords = request.POST['query_search']

        if len(keywords) >= settings.MIN_KEYWORDS_CARACTERS:
            # LOOK IF QUERY DON'T ALREADY EXIST IN MEMCACHED

            cache_format_query = slugify(" ".join(["search", keywords]))

            if cache.get(cache_format_query):
                list_results = cache.get(cache_format_query)
            else:
                all_cat_ban = []
                all_prd_ban = []
                try:
                    all_cat_ban.extend(json.loads(request.session['shop'].categories_ban))
                except:
                    pass
                try:
                    all_cat_ban.extend(request.session['shop'].get_cpro_categories_ban())
                except:
                    pass

                try:
                    all_prd_ban.extend(json.loads(request.session['shop'].products_ban))
                except:
                    pass
                try:
                    all_prd_ban.extend(request.session['shop'].get_cpro_products_ban())
                except:
                    pass

                # Try if keyword is a manufacturer code
                list_results = ProductVariant.objects.filter(manufacturer_ref__iexact=keywords)
                try:
                    cpro_id = Categories.objects.get(code_name='cprodirect').id
                except Exception, e:
                    logger.error("Unable to get the cpro categ id : %s", e)
                    cpro_id = 0

                all_cat_ban.extend([Categories.objects.get(code_name='save').id, Categories.objects.get(code_name='location').id, Categories.objects.get(code_name='emailing').id, Categories.objects.get(code_name='websites').id])

                # if not, basic search is apply
                if not list_results:
                    test = keywords.split(" ")
                    list_results = ProductLang.objects.filter(reduce(lambda x, y: x | y, [Q(name__contains=word) for word in test])
                                                              | reduce(lambda x, y: x | y, [Q(description__icontains=word) for word in test])
                                                              | reduce(lambda x, y: x | y, [Q(product__reference_out__icontains=word) for word in test])
                                                              | reduce(lambda x, y: x | y, [Q(product__reference_in__icontains=word) for word in test]) &
                                                              Q(product__category__in=request.session['categories']),
                                                              ~Q(product__main_category__id=cpro_id), #code_name='cprodirect'),
                                                              ~Q(product__category__id__in=all_cat_ban),
                                                              ~Q(product__id__in=all_prd_ban),
                                                              ~Q(product__is_active=False))[:settings.MAX_RESULTS]
                    # SET QUERY RESULT IN MEMCACHED
                    try:
                        cache.set(cache_format_query, list_results, settings.DELAY_CACHE_SEARCH_RESULTS)
                    except:
                        pass

            prd_list = [lang.product for lang in list_results]

            catalog = build_catalog(prd_list, request)
        else:
            error = _("Your research must contain at least 3 caracters please.")

        return render(request, "result_search_list_products.html", {"datas": catalog, "error": error})
    return redirect("/")


@is_shop_public
def cms_display(request, url_rewrite):
    try:
        page_cms = PageCmsLang.objects.get(url_rewrite=url_rewrite, shop=request.session['shop'], is_active=True)
    except Exception, e:
        return redirect('/')
    else:
        return render(request, "page_cms.html", {"page_cms": page_cms})


@is_shop_public
def consommables(request):
    if request.POST:
        model = request.POST['models'].strip()
        categ = request.POST['categ'].strip()
        if model == unicode("default") or categ == unicode("default"):
            return globals()["adimpo_conso"](request)
    else:
        return globals()["adimpo_conso"](request)

    prds = list()
    attribute = Attributes.objects.get(value=model)
    if categ != unicode("all"):
        prds_tmp = ProductVariant.objects.filter(attributes__id__exact=attribute.id, product__category__id=int(categ))
    else:
        prds_tmp = ProductVariant.objects.filter(attributes__id__exact=attribute.id)
    try:
        list_ban_prd = request.session['shield'].mod.get_products_ban
        list_ban_prd.extend(request.session['shield'].mod.get_cpro_products_ban)
    except:
        list_ban_prd = []
    for tmp in prds_tmp:
        if tmp.product.id not in list_ban_prd:
            prds.append(tmp.product)

    catalog = build_catalog(prds, request)
    category_lg = Categories.objects.get(code_name="adimpo_conso").get_trans(request.LANGUAGE_CODE)

    return render(request, "categories/consommables/consommables_details.html", {"datas": catalog,
                                                                                 "category_lg": category_lg,
                                                                                 "model": model})


@is_shop_public
def faq(request):
    questions = []
    questions = Faq.objects.filter(language__code_iso=request.LANGUAGE_CODE.upper(), is_active=True)

    if not questions:
        questions = Faq.objects.filter(language__code_iso="FR", is_active=True)

    return render(request, "faq.html", {"questions": questions})


def lost_password(request):
    if request.POST:
        if "email" in request.POST:
            try:
                entity = Entities.objects.get(user__email=request.POST['email'], shop=request.session['shop'])
                user = entity.user
            except Exception, e:
                return redirect("/login")
            else:
                new_pwd = User.objects.make_random_password(length=10, allowed_chars='abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789')
                try:
                    user.set_password(new_pwd)
                    user.save()
                except Exception, e:
                    logger.error("Cannot change password %s" % e)
                    msg = _("An error was occured while changing password. If persist contact your technical support.")
                else:
                    params = dict(code_name="password_lost",
                                  sender=request.session['shop'].reseller.get_user().email,
                                  receiver=user.email,
                                  shop=request.session['shop'],
                                  language_code=request.session['shop'].language,
                                  tags=dict(_LOGO_="".join([request.session['shop'].get_domain(), "/medias/", request.session['shop'].logo.url]),
                                            _SIGNATURE_=request.session['shop'].name,
                                            _DOMAIN_="",
                                            _PASSWORD_=new_pwd))
                    hawkeye = Jarvis("hawkeye")
                    try:
                        hawkeye.mod.send_generic_mail(params)
                        msg = _("Operation successful, an email was sent to your email address")
                    except Exception, e:
                        print e

                if request.session['shop'].is_public:
                    return render(request, "login_public.html", {"msg": msg})
                else:
                    return render(request, "login_private.html", {"msg": msg})
    else:
        return redirect("/login")


def payline_log(request):
    token = request.GET['token']
    try:
        result = payline.get_webpaymentdetails(token)
        result_transact = payline.get_transactiondetails(result.transaction.id)
    except Exception, e:
        logger.error(u'Error while running payline.getWebPaymentDetailsRequest(), Unable to get the data : %s', e)

    return HttpResponse(200)


def handler404(request):
    if "medias" in request.path:
        logger.info("Media manquant : %s", request.path)
        return HttpResponse(200)
    else:
        homepage_content = request.session['shop'].get_homepage(request.LANGUAGE_CODE)[0]
        return render_to_response("home.html", {"msg_redirect": True, "homepage_content": homepage_content}, context_instance=RequestContext(request))


def handler500(request):
    if "medias" in request.path:
        logger.info("Media manquant : %s", request.path)
        return HttpResponse(200)
    else:
        homepage_content = request.session['shop'].get_homepage(request.LANGUAGE_CODE)[0]
        return render_to_response("home.html", {"msg_redirect": True, "homepage_content": homepage_content}, context_instance=RequestContext(request))
