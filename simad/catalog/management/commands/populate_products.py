import os
import random
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.core.files import File
from pathlib import Path
from simad.catalog.models import Category, Product, ProductImage
from simad.global_data.enum import ProductTypeChoices, UnitOfMeasureChoices

class Command(BaseCommand):
    help = 'Populate the database with 50 realistic products using images from prod_images.'

    def handle(self, *args, **options):
        self.stdout.write("Starting product population from prod_images...")

        # 1. Create Categories
        categories_data = [
            {"name": "Nettoyage Industériel", "description": "Produits chimiques et solutions de nettoyage pour les usines et les environnements industriels."},
            {"name": "Entretien Ménager", "description": "Tout ce dont vous avez besoin pour garder votre maison propre et saine au quotidien."},
            {"name": "Laboratoire et Recherche", "description": "Réactifs, solutions et matériel pour les laboratoires d'analyse et de recherche."},
            {"name": "Protection et Hygiène", "description": "Gels hydroalcooliques, masques, et produits de protection individuelle."},
            {"name": "Soin du Linge", "description": "Lessives liquides et en poudre, assouplissants pour un linge éclatant."},
        ]
        
        categories = []
        for cat_data in categories_data:
            cat, created = Category.objects.get_or_create(
                slug=slugify(cat_data["name"]),
                defaults={"name": cat_data["name"], "description": cat_data["description"]}
            )
            categories.append(cat)
        
        # 2. Prepare Detailed Descriptions (~300 words)
        desc_blocks = [
            "Ce produit de la gamme SIMAD est une solution d'entretien haute performance conçue spécifiquement pour répondre aux exigences de propreté les plus strictes. "
            "Grâce à sa formulation avancée, il pénètre au cœur des salissures pour une élimination complète sans laisser de résidus chimiques nocifs sur vos surfaces.",
            "Utilisé par les professionnels du nettoyage à travers tout le Cameroun, ce produit a prouvé son efficacité dans une multitude de scénarios, des cuisines collectives aux blocs opératoires. "
            "Sa concentration élevée permet une dilution importante, offrant ainsi un rapport qualité-prix exceptionnel pour les grands volumes de consommation.",
            "La sécurité des utilisateurs est notre priorité absolue. C'est pourquoi ce produit est biodégradable et respecte les normes environnementales locales. "
            "Il ne contient pas de phosphates ni d'agents de blanchiment agressifs, ce qui préserve l'éclat originel de vos matériaux tout en assurant une désinfection totale.",
            "L'innovation SIMAD réside dans la stabilité de nos formules. Même dans des conditions de stockage tropicales, le produit conserve toute son efficacité active. "
            "Chaque lot subit des contrôles qualité rigoureux pour garantir que vous recevez toujours le meilleur de notre expertise chimique directement dans votre établissement.",
            "Que vous cherchiez à assainir votre espace de vie ou à optimiser vos processus industriels, les solutions SIMAD sont là pour vous accompagner. "
            "Facile d'utilisation, notre produit est livré avec des instructions claires pour maximiser son rendement et garantir la sécurité de vos équipes au quotidien.",
            "Opter pour SIMAD, c'est choisir la fiabilité camerounaise alliée à la technologie de pointe. "
            "Notre engagement envers l'excellence nous pousse à améliorer constamment nos produits pour rester à la pointe du secteur de l'hygiène et de l'assainissement industriel.",
            "Pour un environnement plus sain et une tranquillité d'esprit totale, faites confiance à la puissance de nettoyage SIMAD. "
            "Une simple application suffit pour transformer vos espaces et instaurer une barrière protectrice durable contre les bactéries et les virus environnants.",
            "La polyvalence est le maître-mot de cette référence. Elle s'adapte aussi bien aux surfaces lisses qu'aux matériaux poreux, garantissant une finition impeccable à chaque fois. "
            "Recommandé par les experts, ce produit est le choix de référence pour tous ceux qui ne font aucun compromis sur la propreté et l'hygiène de leurs locaux."
        ]

        # 3. Product Names
        product_names = [
            "SimaDésinfect Pro", "SimaGel Hydro", "SimaWash Ultra", "SimaClean Surface", "SimaPure Water",
            "SimaForce Heavy", "SimaGlow Glass", "SimaSavon Liquid", "SimaPro Lab", "SimaLaundry Gold",
            "SimaChlor Plus", "SimaSanitizer Max", "SimaPoudre Active", "SimaLiquide Vaisselle", "SimaNet Sols",
            "SimaDirect Bio", "SimaExtra Clean", "SimaUltra Protect", "SimaGlow Inox", "SimaForce Degraal",
            "SimaPure Air", "SimaWash Color", "SimaClean Multi", "SimaSavon Aloe", "SimaPro Tech",
            "SimaLaundry Soft", "SimaChlor Liquid", "SimaSanitizer Gel", "SimaPoudre Express", "SimaLiquide Mains",
            "SimaNet Vitres", "SimaDirect Eco", "SimaExtra Wash", "SimaUltra Sanit", "SimaGlow Shine",
            "SimaForce Industrial", "SimaPure Nature", "SimaWash Bebé", "SimaClean Expert", "SimaSavon Citron",
            "SimaPro Chem", "SimaLaundry Power", "SimaChlor Granules", "SimaSanitizer Spray", "SimaPoudre Concentrée",
            "SimaLiquide Antiseptique", "SimaNet Multi-usages", "SimaDirect Premium", "SimaExtra Shine", "SimaUltra Hygiene"
        ]

        # 4. Source Images
        prod_images_dir = Path("/home/eddy/projects/Nity Pulse/simad/prod_images")
        available_images = list(prod_images_dir.glob("*.webp"))
        if not available_images:
            self.stdout.write(self.style.WARNING(f"No webp images found in {prod_images_dir}. Using fallback search."))
            available_images = list(prod_images_dir.glob("*"))

        if not available_images:
            self.stdout.write(self.style.ERROR(f"No images at all found in {prod_images_dir}."))
            return

        # 5. Create 50 Products
        for i, name in enumerate(product_names):
            long_desc = " ".join(random.sample(desc_blocks, k=len(desc_blocks)))
            # Duplicate the blocks to ensure ~300 words
            long_desc = (long_desc + "\n\n") * 2
            
            price = random.randint(500, 9900)
            
            product, created = Product.objects.get_or_create(
                slug=slugify(f"{name}-{i}"),
                defaults={
                    "name": name,
                    "category": random.choice(categories),
                    "description": long_desc,
                    "short_description": f"Solution haute performance SIMAD pour votre quotidien.",
                    "price": price,
                    "compare_price": price + random.randint(500, 2000),
                    "sku": f"SIMA-{i:03d}-{random.randint(1000, 9999)}",
                    "stock_quantity": random.randint(50, 500),
                    "is_available": True,
                }
            )

            # Assign images
            selected_images = random.sample(available_images, min(7, len(available_images)))
            
            # Thumbnail
            try:
                with open(selected_images[0], 'rb') as f:
                    product.thumbnail.save(selected_images[0].name, File(f), save=True)
            except Exception as e:
                self.stdout.write(f"Failed to save thumbnail for {name}: {e}")

            # Gallery (up to 6 additional)
            product.images.all().delete()
            for idx, img_path in enumerate(selected_images[1:]):
                try:
                    with open(img_path, 'rb') as f:
                        pi = ProductImage(product=product, alt_text=f"{name} {idx}")
                        pi.image.save(img_path.name, File(f), save=True)
                        pi.save()
                except Exception as e:
                    self.stdout.write(f"Failed to save gallery image for {name}: {e}")

        self.stdout.write(self.style.SUCCESS(f"Successfully populated 50 products using real images."))

if __name__ == "__main__":
    pass
