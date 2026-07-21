import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from app.models import Admin, Category, Product, ProductImage, ProductVariant, ShippingRate, SiteSettings
from app.utils.helpers import slugify
from app.utils.shipping import ALGERIAN_WILAYAS

app = create_app()


def seed():
    with app.app_context():
        db.create_all()

        if not Admin.query.first():
            admin = Admin(username=app.config["ADMIN_USERNAME"])
            admin.set_password(app.config["ADMIN_PASSWORD"])
            db.session.add(admin)
            print("[+] Admin user created")

        categories_data = [
            ("Coques", "coques", "Coques et coquilles de protection pour tous les modèles", 1),
            ("Chargeurs", "chargeurs", "Chargeurs murs, rapides et sans fil", 2),
            ("Écouteurs", "ecouteurs", "Écouteurs filaires et sans fil", 3),
            ("Câbles", "cables", "Câbles USB, Lightning, Type-C", 4),
            ("Supports", "supports", "Supports auto, vélo, bureaux", 5),
            ("Protections d'écran", "protections-ecran", "Verres trempés et films de protection", 6),
        ]
        for name, slug, desc, order in categories_data:
            if not Category.query.filter_by(slug=slug).first():
                db.session.add(Category(name=name, slug=slug, description=desc, order=order))
        db.session.commit()
        print("[+] Categories seeded")

        cat_map = {c.slug: c.id for c in Category.query.all()}

        products_data = [
            # ---- COQUES ----
            {
                "name": "Coque Silicone iPhone 15 Pro",
                "slug": "coque-silicone-iphone-15-pro",
                "description": "Coque en silicone souple, protection 360°, ultra-fine et légère. Anti-choc, anti-rayures. Compatible iPhone 15 Pro.",
                "price": 800, "compare_price": 1200, "stock": 50,
                "cat": "coques", "featured": True, "new": True,
                "phones": "iPhone 15 Pro, iPhone 15",
                "variants": [("iPhone 15 Pro", "Noir", 20, None), ("iPhone 15 Pro", "Bleu", 15, None), ("iPhone 15", "Noir", 15, None), ("iPhone 15", "Transparent", 10, None)],
            },
            {
                "name": "Coque Transparente Samsung S24",
                "slug": "coque-transparente-samsung-s24",
                "description": "Coque transparente en TPU, ultra-mince, ne jaunit pas. Protection renforcée aux coins.",
                "price": 600, "compare_price": 900, "stock": 40,
                "cat": "coques", "featured": True,
                "phones": "Samsung Galaxy S24, Samsung S24+",
                "variants": [("Samsung Galaxy S24", "Transparent", 20, None), ("Samsung S24+", "Transparent", 20, None)],
            },
            {
                "name": "Coque Armored iPhone 15",
                "slug": "coque-armored-iphone-15",
                "description": "Coque blindée militaire, protection renforcée aux coins, support intégré. Résistante aux chocs.",
                "price": 1500, "compare_price": 2000, "stock": 25,
                "cat": "coques", "new": True,
                "phones": "iPhone 15, iPhone 15 Pro",
                "variants": [("iPhone 15", "Noir", 15, None), ("iPhone 15 Pro", "Vert", 10, None)],
            },
            {
                "name": "Coque Cuir Xiaomi Redmi Note 13",
                "slug": "coque-cuir-xiaomi-redmi-note-13",
                "description": "Coque en cuir synthétique, effet premium, fermeture magnétique. Compatible Redmi Note 13/Pro.",
                "price": 900, "compare_price": 1400, "stock": 30,
                "cat": "coques",
                "phones": "Xiaomi Redmi Note 13, Xiaomi Redmi Note 13 Pro",
                "variants": [("Redmi Note 13", "Noir", 15, None), ("Redmi Note 13 Pro", "Marron", 15, None)],
            },
            {
                "name": "Coque Souple Samsung A54",
                "slug": "coque-souple-samsung-a54",
                "description": "Coque souple en TPU, design minimaliste, protège sans ajouter de volume.",
                "price": 500, "compare_price": 700, "stock": 45,
                "cat": "coques",
                "phones": "Samsung Galaxy A54",
            },
            {
                "name": "Coque MagSafe iPhone 15",
                "slug": "coque-magsafe-iphone-15",
                "description": "Coque compatible MagSafe avec aimant intégré. Charge sans fil possible avec la coque.",
                "price": 1800, "compare_price": 2500, "stock": 20,
                "cat": "coques", "new": True,
                "phones": "iPhone 15, iPhone 15 Pro, iPhone 15 Pro Max",
                "variants": [("iPhone 15", "Noir", 8, None), ("iPhone 15 Pro", "Bleu", 7, None), ("iPhone 15 Pro Max", "Transparent", 5, None)],
            },

            # ---- CHARGEURS ----
            {
                "name": "Chargeur Rapide 25W USB-C",
                "slug": "chargeur-rapide-25w-usbc",
                "description": "Chargeur mural rapide 25W, compatible Samsung, Xiaomi, tous USB-C. Charge 0 à 50% en 30 min. protection surchauffe.",
                "price": 1500, "compare_price": 2200, "stock": 30,
                "cat": "chargeurs", "featured": True, "new": True,
            },
            {
                "name": "Chargeur Sans Fil MagSafe 15W",
                "slug": "chargeur-sans-fil-magsafe-15w",
                "description": "Chargeur magnétique sans fil 15W, compatible iPhone 12 et plus récent. Design compact, LED indicatrice.",
                "price": 2500, "compare_price": 3500, "stock": 20,
                "cat": "chargeurs", "new": True,
                "phones": "iPhone 12, iPhone 13, iPhone 14, iPhone 15",
            },
            {
                "name": "Chargeur double port USB 3.1A",
                "slug": "chargeur-double-port-usb-31a",
                "description": "Chargeur double USB, 3.1A au total. Charge 2 appareils simultanément. Compact pour voyages.",
                "price": 900, "compare_price": 1300, "stock": 40,
                "cat": "chargeurs",
            },
            {
                "name": "Station de charge 3-en-1",
                "slug": "station-charge-3-en-1",
                "description": "Chargeur sans fil 3-en-1 : téléphone, montre et écouteurs. Compatible MagSafe. Design élégant.",
                "price": 4500, "compare_price": 6000, "stock": 10,
                "cat": "chargeurs", "featured": True,
                "phones": "iPhone 12 et plus récent, AirPods, Apple Watch",
            },
            {
                "name": "Batterie externe 10000mAh",
                "slug": "batterie-externe-10000mah",
                "description": "Power bank 10000mAh, charge rapide 20W USB-C, affichage LED. Ultra-légère.",
                "price": 2200, "compare_price": 3000, "stock": 25,
                "cat": "chargeurs", "new": True,
            },

            # ---- ÉCOUTEURS ----
            {
                "name": "Écouteurs Bluetooth TWS Pro",
                "slug": "ecouteurs-bluetooth-tws-pro",
                "description": "Écouteurs sans fil, réduction de bruit active (ANC), autonomie 30h avec boîtier. Bluetooth 5.3, résistant à l'eau IPX5.",
                "price": 2800, "compare_price": 4000, "stock": 25,
                "cat": "ecouteurs", "featured": True,
            },
            {
                "name": "Écouteurs Filaires Type-C Hi-Fi",
                "slug": "ecouteurs-filiaires-typec-hifi",
                "description": "Écouteurs filaires avec connecteur Type-C, son Hi-Fi, micro intégré. Câble tressé résistant.",
                "price": 600, "compare_price": 0, "stock": 60,
                "cat": "ecouteurs",
            },
            {
                "name": "AirPods Style Sans Fil",
                "slug": "airpods-style-sans-fil",
                "description": "Écouteurs sans fil style TWS, autonomie 20h, touch controls, Bluetooth 5.2. Compatible Android/iOS.",
                "price": 1800, "compare_price": 2800, "stock": 35,
                "cat": "ecouteurs", "featured": True,
            },
            {
                "name": "Casque Bluetooth Over-Ear",
                "slug": "casque-bluetooth-over-ear",
                "description": "Casque sans fil, réduction de bruit, autonomie 40h, pliable. Son immersif, coussins moelleux.",
                "price": 3500, "compare_price": 5000, "stock": 15,
                "cat": "ecouteurs", "new": True,
            },
            {
                "name": "Écouteurs Filaires Lightning",
                "slug": "ecouteurs-filiaires-lightning",
                "description": "Écouteurs filaires certifiés MFi, connecteur Lightning, micro et boutons intégrés.",
                "price": 700, "compare_price": 1000, "stock": 50,
                "cat": "ecouteurs",
                "phones": "iPhone 6 à iPhone 14",
            },

            # ---- CÂBLES ----
            {
                "name": "Câble USB-C Rapide 1.5m",
                "slug": "cable-usbc-rapide-15m",
                "description": "Câble USB-C to USB-C, charge rapide 60W, transfert données. Longueur 1.5m, tressé en nylon renforcé.",
                "price": 500, "compare_price": 700, "stock": 80,
                "cat": "cables", "featured": True,
            },
            {
                "name": "Câble Lightning iPhone 1m",
                "slug": "cable-lightning-iphone-1m",
                "description": "Câble certifié MFi, charge rapide, résistant. Compatible tous iPhone avec Lightning. Tressé kevlar.",
                "price": 700, "compare_price": 1000, "stock": 45,
                "cat": "cables",
                "phones": "iPhone 6 à iPhone 14",
            },
            {
                "name": "Câble USB-C vers Lightning 2m",
                "slug": "cable-usbc-lightning-2m",
                "description": "Câble USB-C to Lightning, charge rapide 20W, certifié MFi. Longueur 2m, idéal pour le lit.",
                "price": 900, "compare_price": 1300, "stock": 30,
                "cat": "cables",
                "phones": "iPhone 8 et plus récent",
            },
            {
                "name": "Câble Micro-USB 1m",
                "slug": "cable-micro-usb-1m",
                "description": "Câble Micro USB, charge et transfert données. Compatible ancien Android, écouteurs, etc.",
                "price": 300, "compare_price": 0, "stock": 70,
                "cat": "cables",
            },
            {
                "name": "Câble USB-C 3-en-1 1.2m",
                "slug": "cable-3-en-1-12m",
                "description": "Câble multifonction : USB-C + Lightning + Micro-USB. Un seul câble pour tous vos appareils. 1.2m.",
                "price": 800, "compare_price": 1200, "stock": 40,
                "cat": "cables", "new": True,
            },

            # ---- SUPPORTS ----
            {
                "name": "Support Auto Magnétique",
                "slug": "support-auto-magnetique",
                "description": "Support téléphone ventouse pour voiture, rotation 360°, compatible toutes tailles. Installation facile.",
                "price": 1200, "compare_price": 1800, "stock": 35,
                "cat": "supports", "new": True,
            },
            {
                "name": "Support Bureau Adjustable",
                "slug": "support-bureau-adjustable",
                "description": "Support de bureau pliable, angle ajustable, compatible téléphone et tablette. Aluminium.",
                "price": 1500, "compare_price": 2000, "stock": 20,
                "cat": "supports",
            },
            {
                "name": "Support Ventouse Pare-Brise",
                "slug": "support-ventouse-pare-brise",
                "description": "Support ventouse robuste, bras extensible, fixation pare-brise. Rotation complète.",
                "price": 1000, "compare_price": 1500, "stock": 25,
                "cat": "supports",
            },
            {
                "name": "Support Vélo / Moto",
                "slug": "support-velo-moto",
                "description": "Support étanche pour vélo/moto, fixation sur guidon, imperméable IP65.",
                "price": 1800, "compare_price": 2500, "stock": 15,
                "cat": "supports", "new": True,
            },

            # ---- PROTECTIONS D'ÉCRAN ----
            {
                "name": "Verre Trempé iPhone 15 Pro",
                "slug": "verre-trempe-iphone-15-pro",
                "description": "Verre trempé 9H, protection écran complète, oleophobic. Dureté supérieure au plastique 5x.",
                "price": 500, "compare_price": 800, "stock": 100,
                "cat": "protections-ecran", "featured": True,
                "phones": "iPhone 15 Pro, iPhone 15 Pro Max",
                "variants": [("iPhone 15 Pro", "Transparent", 50, None), ("iPhone 15 Pro Max", "Transparent", 50, None)],
            },
            {
                "name": "Verre Trempé Samsung S24 Ultra",
                "slug": "verre-trempe-samsung-s24-ultra",
                "description": "Verre trempé 9H, bords noirs, ultra-mince 0.33mm. Adhésion parfaite, bulles zéro.",
                "price": 600, "compare_price": 900, "stock": 70,
                "cat": "protections-ecran",
                "phones": "Samsung Galaxy S24 Ultra",
            },
            {
                "name": "Film Hydrogel universel 3 pièces",
                "slug": "film-hydrogel-universel",
                "description": "Film hydrogel auto-réparateur, 3 pièces. S'adapte à tous les écrans. Protège contre les rayures.",
                "price": 400, "compare_price": 600, "stock": 120,
                "cat": "protections-ecran",
            },
            {
                "name": "Verre Trempé Courbé Samsung S24",
                "slug": "verre-trempe-courbe-samsung-s24",
                "description": "Verre trempé courbe 3D, couvre les bords de l'écran. Compatible Samsung S24/S24+.",
                "price": 800, "compare_price": 1200, "stock": 40,
                "cat": "protections-ecran",
                "phones": "Samsung Galaxy S24, Samsung S24+",
                "variants": [("Samsung S24", "Noir", 20, None), ("Samsung S24+", "Noir", 20, None)],
            },
            {
                "name": "Verre Trempé Xiaomi Redmi Note 13",
                "slug": "verre-trempe-xiaomi-redmi-note-13",
                "description": "Verre trempé 9H pour Redmi Note 13/Pro. Installation facile avec kit inclus.",
                "price": 400, "compare_price": 600, "stock": 50,
                "cat": "protections-ecran",
                "phones": "Xiaomi Redmi Note 13, Xiaomi Redmi Note 13 Pro",
            },
        ]

        for pdata in products_data:
            if Product.query.filter_by(slug=pdata["slug"]).first():
                continue
            cat_id = cat_map.get(pdata["cat"])
            if not cat_id:
                continue
            product = Product(
                name=pdata["name"],
                slug=pdata["slug"],
                description=pdata.get("description", ""),
                price=pdata["price"],
                compare_price=pdata.get("compare_price", 0),
                stock=pdata.get("stock", 0),
                sku=f"FZ-{pdata['slug'].upper()}",
                category_id=cat_id,
                is_active=True,
                is_featured=pdata.get("featured", False),
                is_new=pdata.get("new", True),
                compatible_phones=pdata.get("phones", ""),
            )
            db.session.add(product)
            db.session.flush()

            placeholder_text = pdata["name"][:25].replace(" ", "+")
            import urllib.parse
            svg_label = urllib.parse.quote(pdata["name"][:30])
            img = ProductImage(
                product_id=product.id,
                url=f"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='800' height='800'%3E%3Crect width='100%25' height='100%25' fill='%23e2e8f0'/%3E%3Ctext x='50%25' y='45%25' dominant-baseline='middle' text-anchor='middle' fill='%2364748b' font-size='22' font-family='sans-serif'%3E{svg_label}%3C/text%3E%3Ctext x='50%25' y='58%25' dominant-baseline='middle' text-anchor='middle' fill='%2394a3b8' font-size='14' font-family='sans-serif'%3EFayzishopping%3C/text%3E%3C/svg%3E",
                alt_text=product.name,
                is_primary=True, order=0,
            )
            db.session.add(img)

            for v in pdata.get("variants", []):
                variant = ProductVariant(
                    product_id=product.id,
                    phone_model=v[0], color=v[1], stock=v[2],
                    price=v[3] if len(v) > 3 and v[3] else None,
                )
                db.session.add(variant)

        db.session.commit()
        print(f"[+] {len(products_data)} products seeded")

        for code, name in ALGERIAN_WILAYAS:
            if not ShippingRate.query.filter_by(wilaya_code=code).first():
                if name == "Alger":
                    price = 400
                elif code in ["09", "15", "16", "31", "25", "19", "35"]:
                    price = 500
                elif int(code) <= 20:
                    price = 600
                elif int(code) <= 40:
                    price = 700
                else:
                    price = 800
                db.session.add(ShippingRate(wilaya_code=code, wilaya_name=name, price=price))
        db.session.commit()
        print("[+] 58 wilayas shipping rates seeded")

        defaults = {
            "banner_title": "Accessoires Tech au Meilleur Prix",
            "banner_subtitle": "Coques, chargeurs, écouteurs et plus encore. Livraison dans toute l'Algérie.",
            "site_name": "Fayzishopping",
            "whatsapp_number": "213XXXXXXXXX",
        }
        for key, value in defaults.items():
            if not SiteSettings.query.filter_by(key=key).first():
                db.session.add(SiteSettings(key=key, value=value))
        db.session.commit()
        print("[+] Site settings seeded")

        print("\n========================================")
        print("  SEED TERMINÉ AVEC SUCCÈS")
        print("========================================")
        print(f"  Admin    : {app.config['ADMIN_USERNAME']}")
        print(f"  Produits : {Product.query.count()}")
        print(f"  Wilayas  : {ShippingRate.query.count()}")
        print("  URL      : http://localhost:5000")
        print("  Admin    : http://localhost:5000/admin")
        print("========================================\n")


if __name__ == "__main__":
    seed()
