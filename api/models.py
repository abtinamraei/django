from mongoengine import Document, StringField, EmailField, IntField, DecimalField, ReferenceField, ListField, DateTimeField
from datetime import datetime, timedelta

# مدل کد تایید ایمیل
class EmailVerificationCode(Document):
    email = EmailField(unique=True, required=True)
    code = StringField(max_length=6, required=True)
    created_at = DateTimeField(default=datetime.utcnow)

    def is_expired(self):
        return datetime.utcnow() > self.created_at + timedelta(minutes=10)

    def __str__(self):
        return f"{self.email} - {self.code}"

# دسته‌بندی محصولات
class Category(Document):
    name = StringField(max_length=100, unique=True, required=True)

    def __str__(self):
        return self.name

# محصول
class Product(Document):
    category = ReferenceField(Category, reverse_delete_rule=2)  # CASCADE
    name = StringField(max_length=200, required=True)
    description = StringField()
    price = DecimalField(precision=0, required=True)
    image = StringField()  # مسیر تصویر ذخیره می‌شود

    def __str__(self):
        return self.name

# رنگ محصول
class ProductColor(Document):
    product = ReferenceField(Product, reverse_delete_rule=2)  # CASCADE
    name = StringField(max_length=50, required=True)
    hex_code = StringField(max_length=7)

    def __str__(self):
        return f"{self.product.name} - {self.name}"

# سایز محصول
class ProductSize(Document):
    color = ReferenceField(ProductColor, reverse_delete_rule=2)  # CASCADE
    size = StringField(max_length=20, required=True)
    price = DecimalField(precision=0, required=True)
    stock = IntField(default=0)

    def __str__(self):
        return f"{self.color.product.name} - {self.color.name} - {self.size}"

# آیتم سبد خرید
class CartItem(Document):
    user_id = StringField(required=True)  # آیدی کاربر از سیستم Auth
    product_size = ReferenceField(ProductSize, reverse_delete_rule=2)
    quantity = IntField(default=1)

    meta = {
        'indexes': [
            {'fields': ('user_id', 'product_size'), 'unique': True}
        ]
    }

    def __str__(self):
        return f"{self.user_id} - {self.product_size} x {self.quantity}"
