from app.models import ShippingRate


def get_shipping_cost(wilaya_name):
    rate = ShippingRate.query.filter_by(wilaya_name=wilaya_name, is_active=True).first()
    if rate:
        return rate.price
    return 600


def get_shipping_rates(wilaya_name):
    rate = ShippingRate.query.filter_by(wilaya_name=wilaya_name, is_active=True).first()
    if rate:
        return {
            "bureau": rate.price,
            "domicile": rate.home_delivery_price or (rate.price + 150),
        }
    return {"bureau": 600, "domicile": 750}


def get_all_wilayas():
    rates = ShippingRate.query.filter_by(is_active=True).order_by(ShippingRate.wilaya_code).all()
    return [(r.wilaya_name, r.wilaya_name, r.price) for r in rates]


ALGERIAN_WILAYAS = [
    ("01", "Adrar"), ("02", "Chlef"), ("03", "Laghouat"), ("04", "Oum El Bouaghi"),
    ("05", "Batna"), ("06", "Béjaïa"), ("07", "Biskra"), ("08", "Béchar"),
    ("09", "Blida"), ("10", "Bouira"), ("11", "Tamanrasset"), ("12", "Tébessa"),
    ("13", "Tlemcen"), ("14", "Tiaret"), ("15", "Tizi Ouzou"), ("16", "Alger"),
    ("17", "Djelfa"), ("18", "Jijel"), ("19", "Sétif"), ("20", "Saïda"),
    ("21", "Skikda"), ("22", "Sidi Bel Abbès"), ("23", "Annaba"), ("24", "Guelma"),
    ("25", "Constantine"), ("26", "Médéa"), ("27", "Mostaganem"), ("28", "M'Sila"),
    ("29", "Mascara"), ("30", "Ouargla"), ("31", "Oran"), ("32", "El Bayadh"),
    ("33", "Illizi"), ("34", "Bordj Bou Arréridj"), ("35", "Boumerdès"), ("36", "El Tarf"),
    ("37", "Tindouf"), ("38", "Tissemsilt"), ("39", "El Oued"), ("40", "Khenchela"),
    ("41", "Souk Ahras"), ("42", "Tipaza"), ("43", "Mila"), ("44", "Aïn Defla"),
    ("45", "Naâma"), ("46", "Aïn Témouchent"), ("47", "Ghardaïa"), ("48", "Relizane"),
    ("49", "El M'Ghair"), ("50", "El Meniaa"), ("51", "Ouled Djellal"),
    ("52", "Bordj Badji Mokhtar"), ("53", "Béni Abbès"), ("54", "Timimoun"),
    ("55", "Touggourt"), ("56", "Djanet"), ("57", "In Salah"), ("58", "In Guezzam"),
]
