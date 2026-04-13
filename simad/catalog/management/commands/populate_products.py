import os
import random
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.core.files import File
from pathlib import Path
from simad.catalog.models import Category, Product, ProductImage, ProductReview
from simad.users.models import User
from simad.global_data.enum import ReviewRatingChoices, ProductTypeChoices, UnitOfMeasureChoices

class Command(BaseCommand):
    help = 'Populate the database with 50 realistic products and real information.'

    def handle(self, *args, **options):
        self.stdout.write("Starting product population...")

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
        
        self.stdout.write(f"Categories ready: {len(categories)}")

        # 2. Prepare Detailed Descriptions (300 words approximately)
        desc_blocks = [
            "Ce produit est le fruit d'une recherche approfondie menée par les experts de SIMAD Cameroon. Il a été conçu pour répondre aux besoins spécifiques du marché local, en alliant performance, sécurité et respect de l'environnement. Sa formule concentrée permet une utilisation économique tout en garantissant des résultats professionnels dès la première application.",
            "Que vous soyez un professionnel de l'industrie ou un particulier soucieux de l'hygiène de sa maison, ce produit saura vous satisfaire. Il élimine efficacement les taches les plus tenaces, les graisses accumulées et les agents pathogènes invisibles à l'œil nu. Sa polyvalence en fait un allié indispensable pour tous vos travaux de nettoyage, des plus simples aux plus complexes.",
            "En choisissant les produits SIMAD, vous soutenez l'expertise locale et bénéficiez d'une qualité certifiée conforme aux normes internationales les plus strictes. Ce produit a subi des tests rigoureux en laboratoire pour assurer une efficacité maximale sans compromettre la santé des utilisateurs ni l'intégrité des surfaces traitées.",
            "L'innovation est au cœur de notre démarche. C'est pourquoi ce produit intègre des agents actifs de nouvelle génération qui agissent en profondeur pour désincruster la saleté tout en laissant un parfum frais et durable. Facile à utiliser et à rincer, il vous fait gagner un temps précieux lors de vos routines d'entretien quotidien.",
            "La sécurité de votre famille et de vos collaborateurs est notre priorité absolue. Ce produit est formulé sans substances nocives agressives, minimisant ainsi les risques d'allergies ou d'irritations. Pour chaque bidon acheté, nous nous engageons à maintenir un standard de pureté irréprochable qui caractérise la marque SIMAD depuis ses débuts au Cameroun.",
            "Pour des résultats optimaux, nous recommandons une utilisation régulière conformément aux instructions figurant sur l'étiquette. Ce produit est disponible en plusieurs formats pour s'adapter à toutes les échelles de consommation, du format familial au vrac industriel. SIMAD : La solution chimique d'excellence pour un environnement sain.",
            "Nous comprenons les défis posés par les environnements tropicaux et les conditions de travail exigeantes. C'est pourquoi notre gamme de produits est spécialement stabilisée pour conserver toutes ses propriétés même en cas de températures élevées ou d'humidité importante. Vous avez la garantie d'un produit stable et efficace sur le long terme.",
            "Recommandé par les professionnels du secteur, ce produit est devenu une référence incontournable au Cameroun. Son efficacité prouvée sur une large variété de supports en fait le choix numéro un des entreprises de nettoyage, des hôpitaux et des ménages exigeants. Faites confiance à SIMAD pour une propreté qui se voit et qui se sent."
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

        # 4. Images
        media_dir = Path("simad/media/")
        available_images = list(media_dir.glob("*.webp"))
        if not available_images:
            available_images = list(media_dir.glob("*.png")) # Fallback
            if not available_images:
                self.stdout.write("Warning: No images found in media directory.")

        # 5. Create 50 Products
        for i, name in enumerate(product_names):
            long_desc = " ".join(random.sample(desc_blocks, k=len(desc_blocks)))
            price = random.randint(500, 9900)
            
            product, created = Product.objects.update_or_create(
                slug=slugify(f"{name}-{i}"),
                defaults={
                    "name": name,
                    "category": random.choice(categories),
                    "description": long_desc,
                    "price": price,
                    "compare_price": price + random.randint(100, 2000),
                    "sku": f"SIMA-{i:03d}-{random.randint(1000, 9999)}",
                    "stock_quantity": random.randint(50, 500),
                    "is_available": True,
                }
            )

            if available_images:
                # Set thumbnail
                thumb = random.choice(available_images)
                # Note: This is an update, so we assume files are already relative to media_root in the path
                product.thumbnail = str(thumb).split('media/')[-1]
                product.save()

                # Create 6 gallery images
                gallery = random.sample(available_images, min(6, len(available_images)))
                product.images.all().delete() # Clear old ones if re-running
                for idx, img_path in enumerate(gallery):
                    ProductImage.objects.create(
                        product=product,
                        image=str(img_path).split('media/')[-1],
                        alt_text=f"{name} image {idx+1}",
                        is_primary=(idx == 0),
                        order=idx
                    )

        self.stdout.write(self.style.SUCCESS(f"Successfully populated 50 products."))

if __name__ == "__main__":
    pass
