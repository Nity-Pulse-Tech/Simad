import os
import random
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from simad.catalog.models import Category, Product, ProductImage
from simad.global_data.enum import ProductTypeChoices, UnitOfMeasureChoices


class Command(BaseCommand):
    help = "Populate the database with 50 realistic SIMAD products using images from prod_images/."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing products before populating.",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            Product.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared all existing products."))

        # ── Images ──────────────────────────────────────────
        # Use BASE_DIR so this works on any server (local or /var/www/Simad)
        prod_images_dir = Path(settings.BASE_DIR) / "prod_images"
        available_images = sorted(prod_images_dir.glob("*.webp"))

        if not available_images:
            self.stdout.write(self.style.ERROR(
                f"No .webp images found in {prod_images_dir}. "
                "Please place product images there first."
            ))
            return

        self.stdout.write(f"Found {len(available_images)} images in {prod_images_dir}")

        # ── Categories ──────────────────────────────────────
        categories_data = [
            {"name": "Nettoyage Industriel", "desc": "Produits chimiques et solutions de nettoyage pour usines et environnements industriels."},
            {"name": "Entretien Ménager", "desc": "Tout pour garder votre maison propre et saine au quotidien."},
            {"name": "Laboratoire et Recherche", "desc": "Réactifs, solutions et matériel pour les laboratoires d'analyse."},
            {"name": "Protection et Hygiène", "desc": "Gels hydroalcooliques, masques et produits de protection individuelle."},
            {"name": "Soin du Linge", "desc": "Lessives liquides et en poudre, assouplissants pour un linge éclatant."},
        ]
        categories = []
        for c in categories_data:
            obj, _ = Category.objects.get_or_create(
                slug=slugify(c["name"]),
                defaults={"name": c["name"], "description": c["desc"]},
            )
            categories.append(obj)

        # ── Description blocks (~300 words when combined) ───
        desc_blocks = [
            "Ce produit de la gamme SIMAD est une solution d'entretien haute performance conçue spécifiquement pour répondre aux exigences de propreté les plus strictes. Grâce à sa formulation avancée, il pénètre au cœur des salissures pour une élimination complète sans laisser de résidus chimiques nocifs sur vos surfaces. La concentration élevée en agents actifs garantit une efficacité dès la première application, même sur les taches les plus tenaces.",
            "Utilisé par les professionnels du nettoyage à travers tout le Cameroun, ce produit a prouvé son efficacité dans une multitude de scénarios, des cuisines collectives aux blocs opératoires. Sa concentration élevée permet une dilution importante, offrant ainsi un rapport qualité-prix exceptionnel pour les grands volumes de consommation. Il est compatible avec la plupart des matériaux courants : inox, carrelage, verre, plastique et surfaces peintes.",
            "La sécurité des utilisateurs est notre priorité absolue. C'est pourquoi ce produit est biodégradable et respecte les normes environnementales locales. Il ne contient pas de phosphates ni d'agents de blanchiment agressifs, ce qui préserve l'éclat originel de vos matériaux tout en assurant une désinfection totale. Son parfum frais et discret laisse une sensation de propreté durable dans tous vos espaces.",
            "L'innovation SIMAD réside dans la stabilité de nos formules. Même dans des conditions de stockage tropicales avec une chaleur et une humidité élevées, le produit conserve toute son efficacité active. Chaque lot subit des contrôles qualité rigoureux en laboratoire pour garantir que vous recevez toujours le meilleur de notre expertise chimique directement dans votre établissement.",
            "Que vous cherchiez à assainir votre espace de vie ou à optimiser vos processus industriels, les solutions SIMAD sont là pour vous accompagner. Facile d'utilisation, notre produit est livré avec des instructions claires pour maximiser son rendement et garantir la sécurité de vos équipes au quotidien. Sa formule concentrée signifie moins de plastique et moins de déchets.",
            "Opter pour SIMAD, c'est choisir la fiabilité camerounaise alliée à la technologie de pointe. Notre engagement envers l'excellence nous pousse à améliorer constamment nos produits pour rester à la pointe du secteur de l'hygiène et de l'assainissement industriel. Chaque produit est le fruit de plus de 10 ans d'expérience dans la chimie industrielle africaine.",
            "Pour un environnement plus sain et une tranquillité d'esprit totale, faites confiance à la puissance de nettoyage SIMAD. Une simple application suffit pour transformer vos espaces et instaurer une barrière protectrice durable contre les bactéries, les virus et les champignons. Idéal pour les familles, les restaurants, les hôpitaux et les écoles.",
            "La polyvalence est le maître-mot de cette référence. Elle s'adapte aussi bien aux surfaces lisses qu'aux matériaux poreux, garantissant une finition impeccable à chaque utilisation. Recommandé par les experts en hygiène, ce produit est le choix de référence pour tous ceux qui ne font aucun compromis sur la propreté et l'hygiène de leurs locaux professionnels ou domestiques.",
        ]

        # ── Product list ────────────────────────────────────
        products_data = [
            ("SimaDésinfect Pro", "Désinfectant de grade médical haute performance pour surfaces et équipements."),
            ("SimaGel Hydro", "Gel hydroalcoolique parfumé à l'aloé vera pour une hygiène des mains optimale."),
            ("SimaWash Ultra", "Lessive liquide concentrée ultra-performante pour tous types de textiles."),
            ("SimaClean Surface", "Nettoyant multi-surfaces sans rinçage pour un entretien quotidien rapide."),
            ("SimaPure Water", "Solution purifiante pour le traitement de l'eau de consommation courante."),
            ("SimaForce Heavy", "Dégraissant industriel puissant pour ateliers et cuisines professionnelles."),
            ("SimaGlow Glass", "Nettoyant vitres et miroirs sans traces pour une brillance longue durée."),
            ("SimaSavon Liquid", "Savon liquide antibactérien enrichi en agents hydratants pour les mains."),
            ("SimaPro Lab", "Réactif de laboratoire haute pureté pour analyses chimiques précises."),
            ("SimaLaundry Gold", "Lessive premium avec microcapsules de parfum longue durée."),
            ("SimaChlor Plus", "Solution chlorée concentrée pour la désinfection des surfaces et de l'eau."),
            ("SimaSanitizer Max", "Désinfectant spray à action rapide pour bureaux et espaces communs."),
            ("SimaPoudre Active", "Détergent en poudre haute mousse pour lavage manuel du linge."),
            ("SimaLiquide Vaisselle", "Liquide vaisselle concentré au citron avec pouvoir dégraissant renforcé."),
            ("SimaNet Sols", "Nettoyant sols parfumé lavande pour carrelage, marbre et parquet."),
            ("SimaDirect Bio", "Nettoyant écologique 100% biodégradable pour surfaces sensibles."),
            ("SimaExtra Clean", "Spray nettoyant multi-usages avec agent antibactérien intégré."),
            ("SimaUltra Protect", "Gel désinfectant à spectre large virucide et bactéricide."),
            ("SimaGlow Inox", "Nettoyant et polish spécial acier inoxydable et chrome."),
            ("SimaForce Degraal", "Dégraissant alimentaire agréé pour cuisines industrielles HACCP."),
            ("SimaPure Air", "Assainisseur d'air professionnel neutralisant les mauvaises odeurs."),
            ("SimaWash Color", "Lessive spéciale couleurs avec protection anti-décoloration avancée."),
            ("SimaClean Multi", "Nettoyant concentré polyvalent dilutable pour toutes surfaces intérieures."),
            ("SimaSavon Aloe", "Savon crème hydratant à l'aloé vera pour lavage fréquent des mains."),
            ("SimaPro Tech", "Solution de nettoyage technique pour équipements électroniques et optiques."),
            ("SimaLaundry Soft", "Assouplissant textile longue durée au parfum de fleurs tropicales."),
            ("SimaChlor Liquid", "Eau de Javel concentrée pour la désinfection domestique et industrielle."),
            ("SimaSanitizer Gel", "Gel antiseptique format voyage 100ml pour une hygiène nomade."),
            ("SimaPoudre Express", "Détergent poudre express lavage rapide 30 minutes garanti."),
            ("SimaLiquide Mains", "Gel lavant mains professionnel pour distributeurs automatiques."),
            ("SimaNet Vitres", "Nettoyant vitres professionnel avec formule anti-buée intégrée."),
            ("SimaDirect Eco", "Gamme écologique certifiée pour le nettoyage responsable au quotidien."),
            ("SimaExtra Wash", "Détergent liquide renforcé haute performance pour linge très sale."),
            ("SimaUltra Sanit", "Désinfectant terminal pour blocs opératoires et salles blanches."),
            ("SimaGlow Shine", "Cire lustrante pour sols carrelés et surfaces lisses."),
            ("SimaForce Industrial", "Détergent industriel surpuissant pour sols d'usine et ateliers."),
            ("SimaPure Nature", "Nettoyant 100% naturel aux huiles essentielles de citronnelle."),
            ("SimaWash Bebé", "Lessive hypoallergénique spéciale vêtements bébé et peaux sensibles."),
            ("SimaClean Expert", "Solution de nettoyage professionnelle pour entreprises de propreté."),
            ("SimaSavon Citron", "Savon liquide au citron frais avec action dégraissante naturelle."),
            ("SimaPro Chem", "Réactif chimique de grade analytique pour laboratoires de recherche."),
            ("SimaLaundry Power", "Lessive en capsules pré-dosées ultra-concentrées pour machine."),
            ("SimaChlor Granules", "Chlore en granulés pour le traitement des piscines et bassins."),
            ("SimaSanitizer Spray", "Spray désinfectant de poche format 50ml prêt à l'emploi."),
            ("SimaPoudre Concentrée", "Poudre nettoyante concentrée pour le récurage de surfaces dures."),
            ("SimaLiquide Antiseptique", "Solution antiseptique pour le nettoyage médical des plaies légères."),
            ("SimaNet Multi-usages", "Nettoyant universel parfum océan pour cuisine, salle de bain et salon."),
            ("SimaDirect Premium", "Gamme premium de nettoyage avec formule enrichie en agents actifs."),
            ("SimaExtra Shine", "Polish et protecteur longue durée pour meubles et boiseries."),
            ("SimaUltra Hygiene", "Pack complet hygiène : gel mains, spray surface et lingettes."),
        ]

        created_count = 0
        for i, (name, short_desc) in enumerate(products_data):
            # Build long description (~300 words)
            shuffled = random.sample(desc_blocks, k=len(desc_blocks))
            long_desc = "\n\n".join(shuffled[:4])

            price = random.randint(5, 99) * 100  # 500 - 9900 FCFA
            compare = price + random.randint(5, 20) * 100

            product, created = Product.objects.get_or_create(
                slug=slugify(f"{name}-{i}"),
                defaults={
                    "name": name,
                    "category": random.choice(categories),
                    "description": long_desc,
                    "short_description": short_desc,
                    "price": price,
                    "compare_price": compare,
                    "sku": f"SIMA-{i:03d}-{random.randint(1000, 9999)}",
                    "stock_quantity": random.randint(50, 500),
                    "is_available": True,
                },
            )

            if not created:
                self.stdout.write(f"  ⏭  {name} already exists, skipping.")
                continue

            created_count += 1

            # ── Attach images from prod_images/ ──
            # Pick 7 images (1 thumb + 6 gallery)
            selected = random.sample(available_images, min(7, len(available_images)))

            # Thumbnail
            try:
                with open(selected[0], "rb") as f:
                    product.thumbnail.save(selected[0].name, File(f), save=True)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  ⚠ Thumb failed for {name}: {e}"))

            # Gallery (up to 6)
            for idx, img_path in enumerate(selected[1:]):
                try:
                    pi = ProductImage(
                        product=product,
                        alt_text=f"{name} – image {idx + 1}",
                        is_primary=(idx == 0),
                        order=idx,
                    )
                    with open(img_path, "rb") as f:
                        pi.image.save(img_path.name, File(f), save=False)
                    pi.save()
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"  ⚠ Gallery {idx} failed for {name}: {e}"))

            self.stdout.write(f"  ✅ {name} – {price} FCFA")

        self.stdout.write(self.style.SUCCESS(
            f"\nDone! Created {created_count} new products. "
            f"Total in DB: {Product.objects.count()}"
        ))
