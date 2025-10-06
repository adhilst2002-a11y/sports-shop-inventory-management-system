from django.contrib import admin
from .models import Supplier, Product, Purchase, Sale


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_person", "phone", "email")
    search_fields = ("name", "contact_person", "email", "phone")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "category", "unit_price", "stock_quantity", "low_stock_threshold")
    list_filter = ("category",)
    search_fields = ("name", "sku")


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ("product", "supplier", "quantity", "unit_cost", "purchased_at")
    list_filter = ("supplier", "product")
    date_hierarchy = "purchased_at"


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("product", "quantity", "unit_price", "sold_at", "customer_name")
    list_filter = ("product",)
    date_hierarchy = "sold_at"

# Register your models here.
