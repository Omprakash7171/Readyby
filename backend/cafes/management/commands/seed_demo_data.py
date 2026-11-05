"""Seed the fictional demo catalogue so the pilot UI can be exercised locally.

Everything created here is flagged ``is_demo=True`` and is hidden from customers
unless ``SHOW_DEMO_CAFES`` is on. None of it describes a real business, so it must
never be loaded into a live pilot database.

    python manage.py seed_demo_data

Pass ``--reset`` to delete existing demo rows first.
"""

from __future__ import annotations

import os
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from cafes.models import Cafe, CafeDistance, Destination, MenuItem

DEMO_CUSTOMER_EMAIL = "customer@readyby.demo"
DEMO_MERCHANT_EMAIL = "merchant@readyby.demo"
DEFAULT_DEMO_PASSWORD = "readyby-demo-2026"

#: Demo cafés stay open late so the pilot can be tried at any sensible hour.
#: A real café sets its own hours; this is only ever used by this command.
DEMO_OPENING_HOURS: dict[str, list[list[str]]] = {
    "mon": [["07:00", "22:30"]],
    "tue": [["07:00", "22:30"]],
    "wed": [["07:00", "22:30"]],
    "thu": [["07:00", "22:30"]],
    "fri": [["07:00", "22:30"]],
    "sat": [["08:00", "22:30"]],
    "sun": [["08:00", "21:00"]],
}


def demo_opening_hours() -> dict[str, list[list[str]]]:
    """A fresh copy of the demo hours."""
    return {
        day: [[window[0], window[1]] for window in windows]
        for day, windows in DEMO_OPENING_HOURS.items()
    }

# (key, name, kind, area, icon, note)
DESTINATIONS = [
    ("city-centre-salon", "City Centre Salon", "Hair salon", "Old Market Quarter", "scissors", "Average appointment 45-60 min"),
    ("london-business-hub", "London Business Hub", "Office building", "Bishopsgate", "building", "Around 600 staff on site"),
    ("central-university", "Central University", "Campus", "Holloway Road", "graduation", "Between lectures and labs"),
    ("riverside-gym", "Riverside Gym", "Gym", "Riverside Walk", "dumbbell", "Most popular after a workout"),
    ("kings-cross-station", "King's Cross Station", "Transport hub", "King's Cross", "train", "Platforms 1 min walk apart"),
]

# slug, name, tagline, category, description, prep minutes, rating, reviews,
# distance by destination key
CAFES = [
    (
        "bean-and-brew",
        "Bean & Brew",
        "Coffee & Bakery",
        "Coffee & Bakery",
        "A corner roastery two minutes from the salon. Most orders are a flat white and a pastry, handed over the counter.",
        6,
        "4.8",
        412,
        {
            "city-centre-salon": 160,
            "london-business-hub": 240,
            "central-university": 420,
            "riverside-gym": 380,
            "kings-cross-station": 300,
        },
    ),
    (
        "northside-coffee",
        "Northside Coffee",
        "Coffee & Breakfast",
        "Coffee & Breakfast",
        "Bright, high-ceilinged room that fills up by 9am. Strong on breakfast rolls and cold brew for people on the move.",
        7,
        "4.6",
        268,
        {
            "city-centre-salon": 320,
            "london-business-hub": 260,
            "central-university": 350,
            "riverside-gym": 460,
            "kings-cross-station": 280,
        },
    ),
    (
        "daily-grind",
        "Daily Grind",
        "Coffee & Pastries",
        "Coffee & Pastries",
        "Small pastry counter with a serious bake schedule. Everything is out of the oven by 8:30 and out of stock by 11.",
        5,
        "4.7",
        189,
        {
            "city-centre-salon": 480,
            "london-business-hub": 520,
            "central-university": 260,
            "riverside-gym": 340,
            "kings-cross-station": 560,
        },
    ),
    (
        "riverside-cafe",
        "Riverside Cafe",
        "Smoothies & Breakfast",
        "Smoothies & Breakfast",
        "Built for post-workout. Protein lattes, yogurt bowls and smoothies you can carry to the riverside path.",
        8,
        "4.5",
        143,
        {
            "city-centre-salon": 900,
            "london-business-hub": 1100,
            "central-university": 820,
            "riverside-gym": 200,
            "kings-cross-station": 1200,
        },
    ),
    (
        "corner-cup",
        "Corner Cup",
        "Teas & Toasties",
        "Teas & Toasties",
        "A tiny kiosk on the station approach. Opens early for commuters and shuts when the last train leaves.",
        6,
        "4.3",
        96,
        {
            "city-centre-salon": 1400,
            "london-business-hub": 700,
            "central-university": 1500,
            "riverside-gym": 1600,
            "kings-cross-station": 220,
        },
    ),
]

# slug -> (address, postcode)
CAFE_ADDRESSES = {
    "bean-and-brew": ("14 Old Market Street", "E2 7JP"),
    "northside-coffee": ("3 Bishopsgate Walk", "E2 7AA"),
    "daily-grind": ("88 Holloway Road", "N7 8JA"),
    "riverside-cafe": ("21 Riverside Walk", "N1 9SF"),
    "corner-cup": ("Station Approach, King's Cross", "N1C 4AP"),
}

# slug -> [(name, description, price, category, art, popular, tag)]
MENUS = {
    "bean-and-brew": [
        ("Latte", "Double shot, steamed milk, thin foam", "3.20", "Coffee", "latte", True, "Most popular"),
        ("Cappuccino", "Equal parts espresso, milk and foam", "3.00", "Coffee", "cappuccino", False, ""),
        ("Americano", "Long black with a splash of hot water", "2.70", "Coffee", "hot-cup", False, ""),
        ("Flat White", "Ristretto base, micro-foam, no dust", "3.30", "Coffee", "latte", False, ""),
        ("Croissant", "All-butter, baked fresh each morning", "2.50", "Breakfast", "croissant", True, ""),
        ("Pain au chocolat", "Two batons of 70% dark chocolate", "2.80", "Breakfast", "pain-au-chocolat", False, ""),
        ("Breakfast sandwich", "Back bacon, cheddar, egg, tomato relish", "4.50", "Breakfast", "sandwich", False, ""),
        ("English breakfast tea", "Loose leaf, brewed to order", "1.60", "Tea & chocolate", "tea", False, ""),
        ("Hot chocolate", "70% dark chocolate, whipped cream", "3.40", "Tea & chocolate", "hot-chocolate", False, ""),
    ],
    "northside-coffee": [
        ("Cappuccino", "Double shot with a deep, dry foam", "3.10", "Coffee", "cappuccino", True, "Most popular"),
        ("Latte", "Oat milk available on request", "3.30", "Coffee", "latte", False, ""),
        ("Filter coffee", "Rotating single origin, brewed by the litre", "2.60", "Coffee", "hot-cup", False, ""),
        ("Iced latte", "Cold brew, milk, poured over ice", "3.60", "Cold drinks", "cold-cup", True, ""),
        ("Breakfast roll", "Sausage, egg, grilled tomato in a crusty roll", "4.90", "Breakfast", "sandwich", False, ""),
        ("Scrambled eggs on sourdough", "Herb butter, two rashers of bacon", "6.20", "Breakfast", "toastie", False, ""),
        ("Cinnamon bun", "Soft, sticky, baked at 7am", "3.00", "Bakery", "muffin", False, ""),
        ("Fresh orange juice", "Squeezed to order, no added sugar", "3.40", "Cold drinks", "cold-cup", False, ""),
    ],
    "daily-grind": [
        ("Flat White", "Chocolatey Brazilian beans, silky micro-foam", "3.40", "Coffee", "latte", True, "Most popular"),
        ("Cortado", "Equal espresso and warm milk in a small glass", "3.00", "Coffee", "cappuccino", False, ""),
        ("Cold brew", "Steeped 18 hours, poured over one large cube", "3.50", "Cold drinks", "cold-cup", False, ""),
        ("Croissant", "Golden, flaky, out of the oven at 8:30", "2.60", "Bakery", "croissant", False, ""),
        ("Pain au chocolat", "Two dark batons, flaky layers", "2.90", "Bakery", "pain-au-chocolat", False, ""),
        ("Almond pastry", "Frangipane, icing sugar, toasted flaked almonds", "3.10", "Bakery", "muffin", False, ""),
        ("Bagel with cream cheese", "Sesame or plain, toasted on request", "2.80", "Breakfast", "muffin", False, ""),
        ("Chocolate chip cookie", "Warm, chewy, best within the hour", "2.10", "Bakery", "cookie", False, ""),
    ],
    "riverside-cafe": [
        ("Protein latte", "Double shot plus a scoop of vanilla protein", "4.10", "Coffee", "latte", True, "Post-workout"),
        ("Cortado", "Short, strong, served in glass", "2.90", "Coffee", "cappuccino", False, ""),
        ("Green smoothie", "Spinach, apple, ginger, coconut water", "4.80", "Cold drinks", "cold-cup", False, ""),
        ("Yogurt & granola bowl", "Greek yogurt, honey, seasonal fruit", "5.20", "Breakfast", "bowl", True, ""),
        ("Banana bread", "Toasted, salted butter on the side", "2.90", "Bakery", "muffin", False, ""),
        ("Spiced chai", "House masala blend, steamed milk", "3.30", "Tea & chocolate", "tea", False, ""),
    ],
    "corner-cup": [
        ("Flat white", "House blend, poured with care", "3.20", "Coffee", "latte", False, ""),
        ("Tea", "English breakfast, Yorkshire style", "1.60", "Tea & chocolate", "tea", False, ""),
        ("Cheese & onion toastie", "Mature cheddar, sliced tomato, butter", "4.20", "Lunch", "toastie", False, ""),
        ("Chocolate chip cookie", "Baked in-house every morning", "2.00", "Bakery", "cookie", False, ""),
        ("Blueberry muffin", "Baked daily, best before noon", "2.50", "Bakery", "muffin", False, ""),
        ("Hot chocolate", "Thick, dark, topped with cream", "3.00", "Tea & chocolate", "hot-chocolate", False, ""),
    ],
}

CAFE_IMAGES = {
    "bean-and-brew": "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=1200&q=80",
    "northside-coffee": "https://images.unsplash.com/photo-1445116572660-236099ec97a0?auto=format&fit=crop&w=1200&q=80",
    "daily-grind": "https://images.unsplash.com/photo-1554118811-1e0d58224f24?auto=format&fit=crop&w=1200&q=80",
    "riverside-cafe": "https://images.unsplash.com/photo-1559925393-8be0ec4767c8?auto=format&fit=crop&w=1200&q=80",
    "corner-cup": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=1200&q=80",
}

ITEM_IMAGES = {
    "latte": "https://images.unsplash.com/photo-1541167760496-1628856ab772?auto=format&fit=crop&w=800&q=80",
    "cappuccino": "https://images.unsplash.com/photo-1572442388796-11668a67e53d?auto=format&fit=crop&w=800&q=80",
    "hot-cup": "https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=800&q=80",
    "cold-cup": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?auto=format&fit=crop&w=800&q=80",
    "croissant": "https://images.unsplash.com/photo-1555507036-ab1f4038808a?auto=format&fit=crop&w=800&q=80",
    "pain-au-chocolat": "https://images.unsplash.com/photo-1608198093002-ad4e005484ec?auto=format&fit=crop&w=800&q=80",
    "sandwich": "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?auto=format&fit=crop&w=800&q=80",
    "toastie": "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?auto=format&fit=crop&w=800&q=80",
    "muffin": "https://images.unsplash.com/photo-1607958996333-41aef7caefaa?auto=format&fit=crop&w=800&q=80",
    "cookie": "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?auto=format&fit=crop&w=800&q=80",
    "tea": "https://images.unsplash.com/photo-1544787219-7f47ccb76574?auto=format&fit=crop&w=800&q=80",
    "hot-chocolate": "https://images.unsplash.com/photo-1517578239113-b03992dcdd25?auto=format&fit=crop&w=800&q=80",
    "bowl": "https://images.unsplash.com/photo-1511690743698-d9d85f2fbf38?auto=format&fit=crop&w=800&q=80",
}

MENU_PREP_MINUTES = {
    "Coffee": 3,
    "Cold drinks": 3,
    "Tea & chocolate": 3,
    "Bakery": 2,
    "Breakfast": 6,
    "Lunch": 7,
}

DEMO_MERCHANT_CAFE = "bean-and-brew"


class Command(BaseCommand):
    help = "Create the fictional demo destinations, cafés and menus (local use only)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing demo cafés, destinations and demo orders first.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            self._reset()

        password = os.environ.get("DEMO_SEED_PASSWORD") or DEFAULT_DEMO_PASSWORD

        destinations = self._seed_destinations()
        merchant = self._seed_users(password)
        cafes = self._seed_cafes(merchant, destinations)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(destinations)} destinations and {len(cafes)} demo cafés."
            )
        )
        self.stdout.write(f"  demo customer: {DEMO_CUSTOMER_EMAIL} / {password}")
        self.stdout.write(f"  demo merchant: {DEMO_MERCHANT_EMAIL} / {password}")
        self.stdout.write(f"  demo café:     {DEMO_MERCHANT_CAFE}")
        if not getattr(settings, "SHOW_DEMO_CAFES", False):
            self.stdout.write(
                self.style.WARNING(
                    "  SHOW_DEMO_CAFES is off, so these cafés stay hidden from customers."
                )
            )

    def _reset(self) -> None:
        # Orders reference cafés with PROTECT, so clear them first.
        from orders.models import Order

        deleted, _ = Order.objects.filter(cafe__is_demo=True).delete()
        self.stdout.write(f"  removed {deleted} demo rows")
        Cafe.objects.filter(is_demo=True).delete()
        Destination.objects.filter(key__in=[row[0] for row in DESTINATIONS]).delete()

    def _seed_destinations(self) -> dict[str, Destination]:
        stored: dict[str, Destination] = {}
        for order, (key, name, kind, area, icon, note) in enumerate(DESTINATIONS):
            destination, _ = Destination.objects.update_or_create(
                key=key,
                defaults={
                    "name": name,
                    "kind": kind,
                    "area": area,
                    "icon": icon,
                    "note": note,
                    "is_active": True,
                    "sort_order": order,
                },
            )
            stored[key] = destination
        return stored

    def _seed_users(self, password: str) -> User:
        merchant, _ = User.objects.get_or_create(
            email=DEMO_MERCHANT_EMAIL,
            defaults={
                "first_name": "Bean & Brew",
                "last_name": "Manager",
                "role": User.Role.MERCHANT,
                "is_staff": True,
            },
        )
        merchant.set_password(password)
        merchant.role = User.Role.MERCHANT
        merchant.save()

        customer, _ = User.objects.get_or_create(
            email=DEMO_CUSTOMER_EMAIL,
            defaults={
                "first_name": "Demo",
                "last_name": "Customer",
                "role": User.Role.CUSTOMER,
            },
        )
        customer.set_password(password)
        customer.role = User.Role.CUSTOMER
        customer.save()
        return merchant

    def _seed_cafes(
        self, merchant: User, destinations: dict[str, Destination]
    ) -> list[Cafe]:
        cafes: list[Cafe] = []
        for slug, name, tagline, category, description, prep, rating, reviews, distances in CAFES:
            address, postcode = CAFE_ADDRESSES[slug]
            cafe, _ = Cafe.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "tagline": tagline,
                    "category": category,
                    "description": description,
                    "image_url": CAFE_IMAGES.get(slug, ""),
                    "address": address,
                    "postcode": postcode,
                    "prep_time_minutes": prep,
                    "kitchen_capacity": 2,
                    "slot_capacity": 6,
                    "rating": Decimal(rating),
                    "review_count": reviews,
                    "opening_hours": demo_opening_hours(),
                    "is_active": True,
                    "is_demo": True,
                    "merchant": merchant if slug == DEMO_MERCHANT_CAFE else None,
                },
            )
            self._seed_distances(cafe, destinations, distances)
            self._seed_menu(cafe, slug)
            cafes.append(cafe)
        return cafes

    def _seed_distances(
        self, cafe: Cafe, destinations: dict[str, Destination], distances: dict[str, int]
    ) -> None:
        for key, metres in distances.items():
            destination = destinations.get(key)
            if destination is None:
                continue
            CafeDistance.objects.update_or_create(
                cafe=cafe,
                destination=destination,
                defaults={"metres": metres},
            )

    def _seed_menu(self, cafe: Cafe, slug: str) -> None:
        MenuItem.objects.filter(cafe=cafe).delete()
        for order, (name, description, price, category, art, popular, tag) in enumerate(
            MENUS.get(slug, [])
        ):
            MenuItem.objects.create(
                cafe=cafe,
                name=name,
                description=description,
                price=Decimal(price),
                category=category,
                art=art,
                image_url=ITEM_IMAGES.get(art, ""),
                prep_time_minutes=MENU_PREP_MINUTES.get(category, 4),
                is_popular=popular,
                tag=tag,
                is_available=True,
                sort_order=order,
            )