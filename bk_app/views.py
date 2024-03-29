from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.forms import modelformset_factory, inlineformset_factory
from django.utils import timezone
import datetime
import win32print, win32ui, win32con
from PIL import Image, ImageWin
import os
from django.conf import settings

from .forms import *
from .models import *


@login_required(login_url='login')
def home(request):
    # total_orders = Order.objects.filter(date_created__day=datetime.datetime.now().day).count()
    total_orders = Order.objects.filter(date_created__day=timezone.now().day).count()
    # oall = Order.objects.all()
    # for i in oall:
    #     print(i.date_created)
    # print(timezone.now().day)
    stock_items = StockItem.objects.all()
    context = {'total_orders': total_orders,
               'stock_items': stock_items}
    if request.method == 'POST':
        stock_item = StockItem.objects.get(id=request.POST['stock_item'])
        stock_list = Stock.objects.filter(item_id=request.POST['stock_item'])
        total_added_items = Stock.objects.filter(item_id=request.POST['stock_item'], status='Add')
        total_removed_items = Stock.objects.filter(item_id=request.POST['stock_item'], status='Remove')
        total_added = 0.0
        for add_item in total_added_items:
            total_added += add_item.quantity
        total_removed = 0.0
        for removed_item in total_removed_items:
            total_removed += removed_item.quantity
        price_spent = 0.0
        unit = 'KG'
        for st_item in stock_list:
            price_spent += st_item.price
            unit = st_item.unit
        context = {'stock_item': stock_item,
                   'stock_list': stock_list,
                   'total_added': total_added,
                   'total_taken': total_removed,
                   'price_spent': price_spent,
                   'unit': unit}
        return render(request, 'bk_app/view_stock.html', context)
    return render(request, 'bk_app/home.html', context)


@login_required(login_url='login')
def stock(request):
    stocks = Stock.objects.all()
    stock_items = StockItem.objects.all()
    context = {'stocks': stocks,
               'stock_items': stock_items}
    return render(request, 'bk_app/stock.html', context)


@login_required(login_url='login')
def print_stock(request, pk):
    stock_item = StockItem.objects.get(id=pk)
    stock_list = Stock.objects.filter(item_id=pk)
    total_added_items = Stock.objects.filter(item_id=pk, status='Add')
    total_removed_items = Stock.objects.filter(item_id=pk, status='Remove')
    total_added = 0.0
    for add_item in total_added_items:
        total_added += add_item.quantity
    total_removed = 0.0
    for removed_item in total_removed_items:
        total_removed += removed_item.quantity
    price_spent = 0.0
    unit = 'KG'
    for st_item in stock_list:
        price_spent += st_item.price
        unit = st_item.unit
    ##################################################################
    # PRINT SUMMARY
    hDC = win32ui.CreateDC()
    hDC.CreatePrinterDC(win32print.GetDefaultPrinter())
    hDC.StartDoc("bamboo_receipt")
    hDC.StartPage()
    # LOGO
    ################################################################################################
    # Constants for GetDeviceCaps
    # HORZRES / VERTRES = printable area
    HORZRES = 6  # 8
    VERTRES = 8  # 10
    # LOGPIXELS = dots per inch
    LOGPIXELSX = 88
    LOGPIXELSY = 90
    # PHYSICALWIDTH/HEIGHT = total area
    PHYSICALWIDTH = 30
    PHYSICALHEIGHT = 30
    # PHYSICALOFFSETX/Y = left / top margin
    PHYSICALOFFSETX = 200
    PHYSICALOFFSETY = 10
    file_name = os.path.join(settings.BASE_DIR, 'bk_logo_white.png')
    printable_area = hDC.GetDeviceCaps(HORZRES), hDC.GetDeviceCaps(VERTRES)
    printer_size = hDC.GetDeviceCaps(PHYSICALWIDTH), hDC.GetDeviceCaps(PHYSICALHEIGHT)
    printer_margins = hDC.GetDeviceCaps(PHYSICALOFFSETX), hDC.GetDeviceCaps(PHYSICALOFFSETY)
    bmp = Image.open(file_name)
    if bmp.size[0] > bmp.size[1]:
        bmp = bmp.rotate(90)

    ratios = [1.0 * printable_area[0] / bmp.size[0], 1.0 * printable_area[1] / bmp.size[1]]
    scale = min(ratios)
    dib = ImageWin.Dib(bmp)
    scaled_width, scaled_height = [int(scale * i) for i in bmp.size]
    x1 = int((printer_size[0] - scaled_width) / 2)
    y1 = int((printer_size[1] - scaled_height) / 2)
    x2 = x1 + scaled_width
    y2 = y1 + scaled_height
    dib.draw(hDC.GetHandleOutput(), (180, 0, 380, 160))
    hDC.TextOut(215, 100, f'BAMBOO')
    hDC.TextOut(215, 130, f'KITCHEN')
    ##################################################################################################
    # ADD SUMMARY
    hDC.TextOut(150, 200, f'{stock_item} SUMMARY')
    hDC.TextOut(10, 260, f'Total Added')
    hDC.TextOut(350, 260, f'{total_added} {unit}')
    hDC.TextOut(10, 300, f'Total Taken')
    hDC.TextOut(350, 300, f'{total_removed} {unit}')
    hDC.TextOut(10, 360, f'Remaining')
    hDC.TextOut(350, 360, f'{total_added - total_removed} {unit}')
    hDC.TextOut(10, 400, f'Price Spent')
    hDC.TextOut(350, 400, f'RS. {price_spent}')
    hDC.EndPage()
    hDC.EndDoc()
    hDC.DeleteDC()
    ###################################################################
    return redirect('home')


@login_required(login_url='login')
def add_stock_item(request):
    crr_user = User.objects.get(username=request.user)
    if request.method == 'POST':
        stock_item_form = StockItemForm(request.POST)
        if stock_item_form.is_valid():
            obj = stock_item_form.save(commit=False)
            obj.add_by = crr_user
            obj.save()
    stock_item_form = StockItemForm()
    context = {'stock_item_form': stock_item_form, }
    return render(request, 'bk_app/add_stock_item.html', context)


@login_required(login_url='login')
def add_stock(request):
    crr_user = User.objects.get(username=request.user)
    if request.method == 'POST':
        stock_form = StockForm(request.POST)
        if stock_form.is_valid():
            obj = stock_form.save(commit=False)
            obj.add_by = crr_user
            obj.save()
    stock_form = StockForm()
    context = {'stock_form': stock_form, }
    return render(request, 'bk_app/add_stock.html', context)


@login_required(login_url='login')
def menu(request):
    categories = Category.objects.all()
    menu_items = MenuItem.objects.all()
    context = {'categories': categories,
               'menu_items': menu_items}
    return render(request, 'bk_app/menu.html', context)


@login_required(login_url='login')
def add_category(request):
    crr_user = User.objects.get(username=request.user)
    if request.method == 'POST':
        cat_form = CategoryForm(request.POST)
        if cat_form.is_valid():
            obj = cat_form.save(commit=False)
            obj.add_by = crr_user
            obj.save()
    cat_form = CategoryForm()
    context = {'cat_form': cat_form, }
    return render(request, 'bk_app/add_category.html', context)


@login_required(login_url='login')
def add_menu_item(request):
    crr_user = User.objects.get(username=request.user)
    if request.method == 'POST':
        menu_item_form = MenuItemForm(request.POST)
        if menu_item_form.is_valid():
            obj = menu_item_form.save(commit=False)
            obj.add_by = crr_user
            obj.save()
    menu_item_form = MenuItemForm()
    context = {'menu_item_form': menu_item_form, }
    return render(request, 'bk_app/add_menu_item.html', context)


@login_required(login_url='login')
def deals(request):
    all_deals = Deal.objects.all()
    context = {'deals': all_deals}
    return render(request, 'bk_app/deals.html', context)


@login_required(login_url='login')
def add_deal(request):
    crr_user = User.objects.get(username=request.user)
    if request.method == 'POST':
        deal_form = DealForm(request.POST)
        if deal_form.is_valid():
            obj = deal_form.save(commit=False)
            obj.add_by = crr_user
            obj.save()
    deal_form = DealForm()
    context = {'deal_form': deal_form, }
    return render(request, 'bk_app/add_deal.html', context)


@login_required(login_url='login')
def view_deal(request, pk):
    deal = Deal.objects.get(id=pk)
    deal_items = deal.dealitem_set.all()
    context = {'deal': deal,
               'deal_items': deal_items}
    return render(request, 'bk_app/view_deal.html', context)


@login_required(login_url='login')
def add_deal_item(request, pk):
    deal = Deal.objects.get(id=pk)
    deal_item_formset = inlineformset_factory(Deal, DealItem, exclude=['deal'], extra=1)
    # deal_item_formset = modelformset_factory(DealItem, exclude=['deal'])
    if request.method == 'POST':
        # formset = deal_item_formset(request.POST, queryset=DealItem.objects.filter(deal_id=pk))
        formset = deal_item_formset(request.POST, instance=deal)
        if formset.is_valid():
            formset.save()
            # instances = formset.save(commit=False)
            # for instance in instances:
            #     instance.deal_id = deal.id
            #     instance.save()
    # formset = deal_item_formset(queryset=DealItem.objects.filter(deal_id=pk))
    formset = deal_item_formset(instance=deal)
    context = {'formset': formset,
               'd_id': pk}
    return render(request, 'bk_app/add_deal_item.html', context)


@login_required(login_url='login')
def orders(request):
    all_orders = Order.objects.all()
    current_orders = Order.objects.filter(date_created__day=timezone.now().day).count()
    # print(current_orders)
    context = {'orders': all_orders}
    return render(request, 'bk_app/orders.html', context)


@login_required(login_url='login')
def print_orders(request):
    if request.method == 'POST':
        date_str = request.POST.get('form_date', None)
        if date_str is None or date_str == "":
            return redirect('home')
        date_time_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        current_orders = Order.objects.filter(date_created__date=date_time_obj.date())

        ##################################################################
        # PRINT SUMMARY
        hDC = win32ui.CreateDC()
        hDC.CreatePrinterDC(win32print.GetDefaultPrinter())
        hDC.StartDoc("bamboo_receipt")
        hDC.StartPage()
        # LOGO
        ################################################################################################
        # Constants for GetDeviceCaps
        # HORZRES / VERTRES = printable area
        HORZRES = 6  # 8
        VERTRES = 8  # 10
        # LOGPIXELS = dots per inch
        LOGPIXELSX = 88
        LOGPIXELSY = 90
        # PHYSICALWIDTH/HEIGHT = total area
        PHYSICALWIDTH = 30
        PHYSICALHEIGHT = 30
        # PHYSICALOFFSETX/Y = left / top margin
        PHYSICALOFFSETX = 200
        PHYSICALOFFSETY = 10
        file_name = os.path.join(settings.BASE_DIR, 'bk_logo_white.png')
        printable_area = hDC.GetDeviceCaps(HORZRES), hDC.GetDeviceCaps(VERTRES)
        printer_size = hDC.GetDeviceCaps(PHYSICALWIDTH), hDC.GetDeviceCaps(PHYSICALHEIGHT)
        printer_margins = hDC.GetDeviceCaps(PHYSICALOFFSETX), hDC.GetDeviceCaps(PHYSICALOFFSETY)
        bmp = Image.open(file_name)
        if bmp.size[0] > bmp.size[1]:
            bmp = bmp.rotate(90)

        ratios = [1.0 * printable_area[0] / bmp.size[0], 1.0 * printable_area[1] / bmp.size[1]]
        scale = min(ratios)
        dib = ImageWin.Dib(bmp)
        scaled_width, scaled_height = [int(scale * i) for i in bmp.size]
        x1 = int((printer_size[0] - scaled_width) / 2)
        y1 = int((printer_size[1] - scaled_height) / 2)
        x2 = x1 + scaled_width
        y2 = y1 + scaled_height
        dib.draw(hDC.GetHandleOutput(), (180, 0, 380, 160))
        hDC.TextOut(215, 100, f'BAMBOO')
        hDC.TextOut(215, 130, f'KITCHEN')
        ##################################################################################################
        # ADD SUMMARY
        hDC.TextOut(50, 200, f'ORDERS SUMMARY --- {date_str}')
        hDC.TextOut(10, 340, 'Item')
        hDC.TextOut(200, 340, f'Time')
        hDC.TextOut(450, 340, 'Bill')
        hDC.MoveTo(10, 380)
        hDC.LineTo(550, 380)
        y = 400
        total_bill=0
        for order in current_orders:
            hDC.TextOut(10, y, f'{order}')
            hDC.TextOut(200, y, f'{str(order.date_created.time()).split(".")[0]}')
            hDC.TextOut(450, y, f'{order.bill}')
            total_bill += order.bill
            y = y+40
        hDC.MoveTo(10, y)
        hDC.LineTo(550, y)
        y = y + 20
        hDC.TextOut(10, y, f'Total Sale')
        hDC.TextOut(450, y, f'{total_bill}')
        # FOOTER
        hDC.TextOut(120, y + 80, 'Powered by Subtain Malik')
        hDC.EndPage()
        hDC.EndDoc()
        hDC.DeleteDC()
        ###################################################################
    return redirect('home')


@login_required(login_url='login')
def add_order(request):
    crr_user = User.objects.get(username=request.user)
    menu_items = MenuItem.objects.all()
    all_deals = Deal.objects.all()
    total_available_deals = all_deals.count()
    total_available_items = menu_items.count()
    order = Order()
    order_no = Order.objects.filter(date_created__day=timezone.now().day).count() + 1
    order_form = OrderForm(instance=order, initial={'no': order_no})
    order_item_inline_form = inlineformset_factory(Order, OrderItem, exclude=('order',), extra=total_available_deals,
                                                   can_delete=False)
    order_menu_item_inline_form = inlineformset_factory(Order, OrderMenuItem, exclude=('order',),
                                                        extra=int(total_available_items * 0.5),
                                                        can_delete=False)
    order_item_forms = order_item_inline_form()
    menu_item_forms = order_menu_item_inline_form()
    if request.method == "POST":
        order_form = OrderForm(request.POST)
        order_item_forms = order_item_inline_form(request.POST, request.FILES)
        menu_item_forms = order_menu_item_inline_form(request.POST, request.FILES)
        if order_form.is_valid():
            created_order = order_form.save(commit=False)
            order_item_forms = order_item_inline_form(request.POST, request.FILES, instance=created_order)
            menu_item_forms = order_menu_item_inline_form(request.POST, request.FILES, instance=created_order)
            if order_item_forms.is_valid() and menu_item_forms.is_valid():
                created_order.save()
                order_item_forms.save()
                menu_item_forms.save()
                new_order = Order.objects.get(id=created_order.id)
                od_items = new_order.orderitem_set.all()
                mi_items = new_order.ordermenuitem_set.all()
                total_price = 0.0
                for d_item in od_items:
                    total_price += d_item.item.price * d_item.quantity
                for m_item in mi_items:
                    total_price += m_item.item.price * m_item.quantity
                charges = total_price
                # add discount
                if new_order.discount > 0:
                    m_discount = new_order.discount / 100
                    total_discount = total_price * m_discount
                    total_price -= total_discount
                new_order.charges = charges
                new_order.bill = total_price
                new_order.add_by = crr_user
                new_order.save()
                return redirect('view_order', pk=new_order.id)
    context = {'order_form': order_form,
               'order_item_form': order_item_forms,
               'menu_item_form': menu_item_forms,
               'menu_items': menu_items,
               'deals': all_deals}
    return render(request, 'bk_app/add_order.html', context)


@login_required(login_url='login')
def view_order(request, pk):
    order = Order.objects.get(id=pk)
    order_items = order.orderitem_set.all()
    menu_items = order.ordermenuitem_set.all()
    if request.method == 'POST':
        hDC = win32ui.CreateDC()
        hDC.CreatePrinterDC(win32print.GetDefaultPrinter())
        hDC.StartDoc("bamboo_receipt")
        hDC.StartPage()
        order_no = order.no
        time_date = str(order.date_created).split(".")[0]
        order_status = order.status
        order_charges = order.charges
        order_bill = order.bill
        order_discount = order.discount

        # LOGO
        ################################################################################################
        # Constants for GetDeviceCaps
        # HORZRES / VERTRES = printable area
        HORZRES = 6  # 8
        VERTRES = 8  # 10
        # LOGPIXELS = dots per inch
        LOGPIXELSX = 88
        LOGPIXELSY = 90
        # PHYSICALWIDTH/HEIGHT = total area
        PHYSICALWIDTH = 30
        PHYSICALHEIGHT = 30
        # PHYSICALOFFSETX/Y = left / top margin
        PHYSICALOFFSETX = 200
        PHYSICALOFFSETY = 10
        file_name = os.path.join(settings.BASE_DIR, 'bk_logo_white.png')
        printable_area = hDC.GetDeviceCaps(HORZRES), hDC.GetDeviceCaps(VERTRES)
        printer_size = hDC.GetDeviceCaps(PHYSICALWIDTH), hDC.GetDeviceCaps(PHYSICALHEIGHT)
        printer_margins = hDC.GetDeviceCaps(PHYSICALOFFSETX), hDC.GetDeviceCaps(PHYSICALOFFSETY)
        bmp = Image.open(file_name)
        if bmp.size[0] > bmp.size[1]:
            bmp = bmp.rotate(90)

        ratios = [1.0 * printable_area[0] / bmp.size[0], 1.0 * printable_area[1] / bmp.size[1]]
        scale = min(ratios)
        dib = ImageWin.Dib(bmp)
        scaled_width, scaled_height = [int(scale * i) for i in bmp.size]
        x1 = int((printer_size[0] - scaled_width) / 2)
        y1 = int((printer_size[1] - scaled_height) / 2)
        x2 = x1 + scaled_width
        y2 = y1 + scaled_height
        dib.draw(hDC.GetHandleOutput(), (180, 0, 380, 160))
        hDC.TextOut(215, 100, f'BAMBOO')
        hDC.TextOut(215, 130, f'KITCHEN')
        ##################################################################################################

        # HEADINGS
        hDC.TextOut(150, 200, f'Order# {order_no} --- {order_status}')
        hDC.TextOut(120, 240, f'\nTime: {time_date}')
        # BODY
        hDC.TextOut(10, 340, 'Item')
        hDC.TextOut(320, 340, 'Quantity')
        hDC.TextOut(470, 340, 'Price')
        hDC.MoveTo(10, 380)
        hDC.LineTo(550, 380)
        y = 400
        for o_item in order_items:
            hDC.TextOut(10, y, f'{o_item.item}')
            hDC.TextOut(320, y, f'{o_item.quantity}')
            hDC.TextOut(470, y, f'{o_item.item.price*o_item.quantity}')
            y = y + 40
        for m_item in menu_items:
            hDC.TextOut(10, y, f'{m_item.item.name}')
            hDC.TextOut(320, y, f'{m_item.quantity} {m_item.item.unit}')
            hDC.TextOut(470, y, f'{m_item.item.price*m_item.quantity}')
            y = y + 40
        hDC.MoveTo(10, y)
        hDC.LineTo(550, y)
        y = y + 20
        hDC.TextOut(10, y, f'Total Bill')
        hDC.TextOut(460, y, f'{order_charges}')
        y = y + 40
        if order_discount > 0:
            hDC.TextOut(10, y, f'Discount Offered')
            hDC.TextOut(460, y, f'{order_discount}%')
            y = y + 40
            hDC.TextOut(10, y, f'Final Bill')
            hDC.TextOut(460, y, f'{order_bill}')
        # FOOTER
        hDC.TextOut(120, y + 80, 'Powered by Subtain Malik')
        hDC.EndPage()
        hDC.EndDoc()
        hDC.DeleteDC()
    context = {'order': order,
               'order_items': order_items,
               'menu_items': menu_items, }
    return render(request, 'bk_app/view_order.html', context)


def do_login(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
    return render(request, 'bk_app/login.html')


@login_required(login_url='login')
def do_logout(request):
    logout(request)
    return redirect('home')
