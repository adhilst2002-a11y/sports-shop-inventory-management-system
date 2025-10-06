from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.db.models import Sum, Q
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from functools import wraps

from .models import Product, Supplier, Purchase, Sale


def inline_base_style() -> str:
    return (
        "body{font-family:Arial,Helvetica,sans-serif;margin:0;padding:0;background:#f7f7f7;}"
        "header{background:#0b6ef3;color:#fff;padding:14px 20px;}"
        "a{color:#0b6ef3;text-decoration:none;}"
        ".container{padding:20px;}"
        ".card{background:#fff;border:1px solid #e6e6e6;border-radius:8px;padding:16px;margin-bottom:16px;}"
        ".btn{display:inline-block;padding:8px 12px;border-radius:6px;border:1px solid #0b6ef3;color:#0b6ef3;background:#e9f1ff;margin-right:8px;}"
        ".btn.primary{background:#0b6ef3;color:#fff;border-color:#0b6ef3;}"
        "table{width:100%;border-collapse:collapse;}th,td{padding:8px;border-bottom:1px solid #eee;text-align:left;}"
        ".low{color:#b30000;font-weight:bold;}"
        ".grid{display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));}"
        "input,select{padding:8px;border:1px solid #ccc;border-radius:6px;width:100%;}label{font-weight:bold;margin-top:8px;display:block;}"
        ".row{display:flex;gap:10px;align-items:center;flex-wrap:wrap;}"
    )


def staff_required(view_func):
    @wraps(view_func)
    def _wrapped(request: HttpRequest, *args, **kwargs):
        if not request.user.is_staff:
            return HttpResponseForbidden("Forbidden")
        return view_func(request, *args, **kwargs)
    return _wrapped


def login_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("dashboard")
        return render(request, "auth/login.html", {"style": inline_base_style(), "error": "Invalid credentials"})
    return render(request, "auth/login.html", {"style": inline_base_style()})


def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return redirect("login")


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    query = request.GET.get("q", "").strip()
    products = Product.objects.all()
    if query:
        products = products.filter(Q(name__icontains=query) | Q(sku__icontains=query))
    low_stock = products.filter(stock_quantity__lte=models.F("low_stock_threshold"))[:10]
    totals = {
        "products": Product.objects.count(),
        "suppliers": Supplier.objects.count(),
        "stock_units": Product.objects.aggregate(total=Sum("stock_quantity"))["total"] or 0,
        "sales": Sale.objects.count(),
    }
    return render(request, "dashboard.html", {"style": inline_base_style(), "low_stock": low_stock, "totals": totals, "query": query})


@login_required
def product_list(request: HttpRequest) -> HttpResponse:
    query = request.GET.get("q", "").strip()
    products = Product.objects.all()
    if query:
        products = products.filter(Q(name__icontains=query) | Q(sku__icontains=query))
    return render(request, "products/list.html", {"style": inline_base_style(), "products": products, "query": query})


@login_required
@staff_required
def product_create(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        sku = request.POST.get("sku", "").strip()
        category = request.POST.get("category", "other")
        description = request.POST.get("description", "").strip()
        unit_price = request.POST.get("unit_price", "0")
        low_stock_threshold = request.POST.get("low_stock_threshold", "5")
        supplier_id = request.POST.get("supplier")
        supplier = Supplier.objects.filter(id=supplier_id).first() if supplier_id else None
        Product.objects.create(
            name=name,
            sku=sku,
            category=category,
            description=description,
            unit_price=unit_price or 0,
            low_stock_threshold=low_stock_threshold or 5,
            supplier=supplier,
        )
        return redirect("product_list")
    return render(request, "products/form.html", {"style": inline_base_style(), "suppliers": Supplier.objects.all(), "product": None})


@login_required
@staff_required
def product_update(request: HttpRequest, pk: int) -> HttpResponse:
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product.name = request.POST.get("name", product.name).strip()
        product.sku = request.POST.get("sku", product.sku).strip()
        product.category = request.POST.get("category", product.category)
        product.description = request.POST.get("description", product.description).strip()
        product.unit_price = request.POST.get("unit_price", product.unit_price)
        product.low_stock_threshold = request.POST.get("low_stock_threshold", product.low_stock_threshold)
        supplier_id = request.POST.get("supplier")
        product.supplier = Supplier.objects.filter(id=supplier_id).first() if supplier_id else None
        product.save()
        return redirect("product_list")
    return render(request, "products/form.html", {"style": inline_base_style(), "suppliers": Supplier.objects.all(), "product": product})


@login_required
@staff_required
def product_delete(request: HttpRequest, pk: int) -> HttpResponse:
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product.delete()
        return redirect("product_list")
    return render(request, "confirm_delete.html", {"style": inline_base_style(), "object": product, "back": reverse("product_list")})


@login_required
def supplier_list(request: HttpRequest) -> HttpResponse:
    suppliers = Supplier.objects.all()
    return render(request, "suppliers/list.html", {"style": inline_base_style(), "suppliers": suppliers})


@login_required
@staff_required
def supplier_create(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        Supplier.objects.create(
            name=request.POST.get("name", "").strip(),
            contact_person=request.POST.get("contact_person", "").strip(),
            phone=request.POST.get("phone", "").strip(),
            email=request.POST.get("email", "").strip(),
            address=request.POST.get("address", "").strip(),
        )
        return redirect("supplier_list")
    return render(request, "suppliers/form.html", {"style": inline_base_style(), "supplier": None})


@login_required
@staff_required
def supplier_update(request: HttpRequest, pk: int) -> HttpResponse:
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == "POST":
        supplier.name = request.POST.get("name", supplier.name).strip()
        supplier.contact_person = request.POST.get("contact_person", supplier.contact_person).strip()
        supplier.phone = request.POST.get("phone", supplier.phone).strip()
        supplier.email = request.POST.get("email", supplier.email).strip()
        supplier.address = request.POST.get("address", supplier.address).strip()
        supplier.save()
        return redirect("supplier_list")
    return render(request, "suppliers/form.html", {"style": inline_base_style(), "supplier": supplier})


@login_required
@staff_required
def supplier_delete(request: HttpRequest, pk: int) -> HttpResponse:
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == "POST":
        supplier.delete()
        return redirect("supplier_list")
    return render(request, "confirm_delete.html", {"style": inline_base_style(), "object": supplier, "back": reverse("supplier_list")})


@login_required
def purchase_create(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        product = get_object_or_404(Product, pk=request.POST.get("product"))
        supplier = get_object_or_404(Supplier, pk=request.POST.get("supplier"))
        quantity = int(request.POST.get("quantity", "0") or 0)
        unit_cost = request.POST.get("unit_cost", "0")
        Purchase.objects.create(product=product, supplier=supplier, quantity=quantity, unit_cost=unit_cost)
        product.stock_quantity = models.F("stock_quantity") + quantity
        product.save(update_fields=["stock_quantity"])
        return redirect("dashboard")
    return render(request, "purchases/form.html", {"style": inline_base_style(), "products": Product.objects.all(), "suppliers": Supplier.objects.all()})


@login_required
def sale_create(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        product = get_object_or_404(Product, pk=request.POST.get("product"))
        quantity = int(request.POST.get("quantity", "0") or 0)
        unit_price = request.POST.get("unit_price", product.unit_price)
        customer_name = request.POST.get("customer_name", "").strip()
        if quantity > 0 and product.stock_quantity >= quantity:
            Sale.objects.create(product=product, quantity=quantity, unit_price=unit_price, customer_name=customer_name)
            product.stock_quantity = models.F("stock_quantity") - quantity
            product.save(update_fields=["stock_quantity"])
        return redirect("dashboard")
    return render(request, "sales/form.html", {"style": inline_base_style(), "products": Product.objects.all()})


@login_required
def reports(request: HttpRequest) -> HttpResponse:
    # Optional date filters
    start = request.GET.get("start")
    end = request.GET.get("end")
    sales_qs = Sale.objects.all()
    purchases_qs = Purchase.objects.all()
    if start:
        sales_qs = sales_qs.filter(sold_at__date__gte=start)
        purchases_qs = purchases_qs.filter(purchased_at__date__gte=start)
    if end:
        sales_qs = sales_qs.filter(sold_at__date__lte=end)
        purchases_qs = purchases_qs.filter(purchased_at__date__lte=end)
    total_sales_amount = (
        sales_qs.aggregate(total=Sum(models.F("quantity") * models.F("unit_price")))
        ["total"]
        or 0
    )
    total_purchases_cost = (
        purchases_qs.aggregate(total=Sum(models.F("quantity") * models.F("unit_cost")))
        ["total"]
        or 0
    )
    recent_sales = Sale.objects.order_by("-sold_at")[:20]
    return render(
        request,
        "reports/index.html",
        {
            "style": inline_base_style(),
            "total_sales_amount": total_sales_amount,
            "total_purchases_cost": total_purchases_cost,
            "products": Product.objects.all(),
            "recent_sales": recent_sales,
        },
    )


@login_required
def sale_invoice_pdf(request: HttpRequest, pk: int) -> HttpResponse:
    sale = get_object_or_404(Sale, pk=pk)
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f"inline; filename=invoice_{sale.id}.pdf"
    c = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20 * mm, (height - 20 * mm), "Sports Shop - Invoice")
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, (height - 28 * mm), f"Invoice #: {sale.id}")
    c.drawString(20 * mm, (height - 34 * mm), f"Date: {sale.sold_at.strftime('%Y-%m-%d %H:%M')}")

    # Customer
    c.drawString(20 * mm, (height - 46 * mm), f"Customer: {sale.customer_name or 'Walk-in'}")

    # Table header
    y = height - 60 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(20 * mm, y, "Item")
    c.drawString(110 * mm, y, "Qty")
    c.drawString(130 * mm, y, "Unit Price")
    c.drawString(160 * mm, y, "Total")

    # Line item
    y -= 8 * mm
    c.setFont("Helvetica", 11)
    total = float(sale.quantity) * float(sale.unit_price)
    c.drawString(20 * mm, y, f"{sale.product.name} ({sale.product.sku})")
    c.drawRightString(125 * mm, y, str(sale.quantity))
    c.drawRightString(155 * mm, y, f"{sale.unit_price}")
    c.drawRightString(190 * mm, y, f"{total:.2f}")

    # Summary
    y -= 16 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(190 * mm, y, f"Grand Total: {total:.2f}")

    c.showPage()
    c.save()
    return response


# Create your views here.
