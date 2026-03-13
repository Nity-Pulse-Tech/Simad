import os
import sys
import django
import random
import json
from pathlib import Path

# Setup Django environment manually
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from simad.catalog.models import (
    Category, Product, ProductImage, ProductReview
)
from simad.users.models import User
from simad.global_data.enum import ReviewRatingChoices


from django.utils.text import slugify
from django.core.files import File

def populate_database():
    print("Starting database population...")

    # 1. Ensure Categories exist
    root_category, _ = Category.objects.get_or_create(
        name="Désinfectants",
        slug="desinfectants",
        defaults={"description": "Produits de désinfection"}
    )
    
    subcategories_data = [
        {"name": "Gels Hydroalcooliques", "slug": "gels-hydroalcooliques"},
        {"name": "Lingettes", "slug": "lingettes"},
        {"name": "Solutions de Surface", "slug": "solutions-surface"},
    ]
    
    subcategories = []
    for sub in subcategories_data:
        cat, _ = Category.objects.get_or_create(
            name=sub["name"],
            slug=sub["slug"],
            parent=root_category
        )
        subcategories.append(cat)
        
    print(f"Created/Found {len(subcategories)} subcategories.")

    # 2. Collect Images
    media_dir = Path("simad/media/")
    available_images = list(media_dir.glob("Screenshot*.png"))
    
    # Ensure there are some users for reviews
    dummy_user, _ = User.objects.get_or_create(
        email="client@simad.com", 
        defaults={"first_name": "Client", "last_name": "Test", "is_active": True}
    )

    review_names = ["Jean-Paul M.", "Aissatou N.", "Marc D.", "Sophie L.", "Dr. E."]
    review_texts = [
        "Excellent produit. Nous l'utilisons dans notre clinique depuis plusieurs mois. L'odeur est neutre et l'efficacité est au rendez-vous. Livraison très rapide sur Douala.",
        "Produit de haute qualité, on sent tout de suite la différence avec les produits de supermarché. Je recommande pour une protection maximale à la maison.",
        "Très bon rapport qualité-prix. Fait bien le job.",
        "Facile à utiliser. Exactement ce dont nous avions besoin.",
        "Le format est parfait, je rachèterai certainement."
    ]

    ratings = [ReviewRatingChoices.FIVE, ReviewRatingChoices.FOUR, ReviewRatingChoices.FOUR, ReviewRatingChoices.FIVE, ReviewRatingChoices.FIVE]

    # Pre-defined templates for product data
    usage_instructions_template = [
        {"text": "Vaporiser à une distance de 20cm sur la surface préalablement nettoyée."},
        {"text": "Laisser agir pendant 5 minutes pour une efficacité bactéricide complète."},
        {"text": "Essuyer avec un chiffon propre non pelucheux si nécessaire."}
    ]

    technical_details_template = {
        "Composition": "Alcool Isopropylique 75%, Glycérine, Peroxyde d'hydrogène",
        "Certification": "ANOR Norme NC-ISO 22000:2018",
        "Dosage": "Prêt à l'emploi (Solution non diluée)",
        "Spectre": "Virucide, Bactéricide, Fongicide"
    }

    precautions_str = "Usage externe uniquement. Tenir hors de portée des enfants. Conserver dans un endroit frais et sec, à l'abri de la lumière directe du soleil. Ne pas mélanger avec d'autres produits chimiques."
    clinical_notes_str = "SimaDésinfect Pro est une solution de désinfection de grade médical haute performance, formulée pour éliminer 99.9% des agents pathogènes. Idéal pour les environnements cliniques, industriels et domestiques exigeants."

    realistic_products = [
        {"name": "SimaDésinfect Pro", "subtitle": "Solution de désinfection de grade médical haute performance"},
        {"name": "SimaGel Hydro", "subtitle": "Gel hydroalcoolique parfumé à l'aloé vera"},
        {"name": "SimaWipes Plus", "subtitle": "Lingettes désinfectantes multi-surfaces (x100)"},
        {"name": "SimaVrac 5L", "subtitle": "Recharge industrielle économique pour professionnels"},
        {"name": "CleanProtect Ultra", "subtitle": "Spray désinfectant pour environnements hospitaliers"},
        {"name": "SimaSanitizer M1", "subtitle": "Désinfectant rapide pour matériel chirurgical"},
        {"name": "PureCare Mains", "subtitle": "Lotion désinfectante douce pour usage fréquent"},
        {"name": "SimaClean Sols", "subtitle": "Détergent désinfectant concentré pour sols et grandes surfaces"},
        {"name": "AeroDésinfect Sima", "subtitle": "Aérosol désinfectant pour l'air et les surfaces"},
        {"name": "SimaLingettes Pocket", "subtitle": "Mini lingettes désinfectantes (x20) pour le voyage"},
        {"name": "SimaSeptique X", "subtitle": "Solution bactéricide et fongicide à action rapide"},
        {"name": "CliniClean Sima", "subtitle": "Nettoyant désinfectant sans rinçage"},
        {"name": "SimaMousse Active", "subtitle": "Mousse désinfectante pour surfaces poreuses"},
        {"name": "ProProtect Sima", "subtitle": "Désinfectant terminal pour blocs opératoires"},
        {"name": "SimaGel Aloe+", "subtitle": "Gel hydroalcoolique enrichi pour le soin des mains"},
        {"name": "SimaWipes Eco", "subtitle": "Lingettes désinfectantes biodégradables (x50)"},
        {"name": "SimaVrac Sols 10L", "subtitle": "Bidon industriel pour l'entretien des locaux"},
        {"name": "SimaDésinfect Pédiatrique", "subtitle": "Solution désinfectante douce pour environnements pédiatriques"},
        {"name": "SimaSpray Précision", "subtitle": "Spray désinfectant avec embout de précision pour petits matériels"},
        {"name": "SimaTotal Protect", "subtitle": "Gamme complète désinfection (Pack Découverte)"}
    ]

    detailed_descriptions = [
        "Formulé spécifiquement pour répondre aux normes d'hygiène les plus strictes. Ce produit assure une élimination rapide et totale de 99.9% des micro-organismes, garantissant ainsi un environnement sain et sécurisé. Sa composition unique évite le dessèchement tout en offrant une barrière protectrice durable. Conçu pour les professionnels exigeants, il s'adapte parfaitement à un usage en milieu clinique, en entreprise, ou pour une protection maximale à domicile.",
        "Notre solution innovante combine efficacité redoutable et respect total des surfaces. Validé par les laboratoires indépendants, ce désinfectant agit au cœur même des foyers bactériens. Grâce à son action rémanente, il empêche la recolonisation bactérienne pendant plusieurs heures. Idéal pour lutter contre la propagation des infections, il est l'allié indispensable des protocoles de nettoyage quotidiens.",
        "Développé par nos équipes de chercheurs, ce produit offre un spectre large d'action. Bactéricide, fongicide et virucide, il neutralise les menaces invisibles en quelques minutes seulement. Son parfum léger et agréable ne laisse aucune odeur chimique rémanente. Un choix de qualité pour maintenir un haut niveau d'asepsie dans tous vos espaces de travail et de vie.",
        "Une formulation haute technologie qui allie rapidité d'action et sécurité d'utilisation. Conforme aux dernières normes européennes et nationales (ANOR), il garantit une désinfection terminale irréprochable. Facile à appliquer, il ne nécessite aucun rinçage et ne laisse aucune trace. C'est l'outil de prévention par excellence pour tous les établissements recevant du public."
    ]

    print("Creating products...")

    created_products = []
    # Create 20 products
    for i, prod_data in enumerate(realistic_products):
        product_name = prod_data["name"]
        short_desc = prod_data["subtitle"]
        long_desc = random.choice(detailed_descriptions) + "\n\n" + clinical_notes_str
        
        # Determine main image
        img_path = str(available_images[i % len(available_images)])
        
        # Update or create to apply inventory changes to existing products
        product, created = Product.objects.update_or_create(
            name=product_name,
            defaults={
                "slug": f"produit-sima-{i}-{slugify(product_name)}",
                "category": random.choice(subcategories),
                "description": long_desc,
                "short_description": short_desc,
                "sku": f"SIMA-PROD-{i:03d}",
                "price": random.randint(15, 85) * 1000,
                "initial_stock_quantity": random.randint(100, 200),
                "stock_quantity": random.randint(10, 100),
                "clinical_notes": clinical_notes_str,
                "usage_instructions": usage_instructions_template,
                "precautions": precautions_str,
                "technical_details": technical_details_template,
                "thumbnail": img_path.split('media/')[-1] # relative to media root
            }
        )
        
        if created:
            created_products.append(product)
            
            # --- CREATE GALLERY IMAGES ---
            # pick up to 7 random images (but distinct from thumbnail if possible) for gallery
            gallery_imgs = random.sample(available_images, min(7, len(available_images)))
            
            for j, g_img in enumerate(gallery_imgs):
                ProductImage.objects.create(
                    product=product,
                    image=str(g_img).split('media/')[-1], # relative 
                    alt_text=f"Image {j+1} - {product_name}",
                    is_primary=(j==0),
                    order=j
                )

            # --- CREATE REVIEWS ---
            # Create 5 reviews
            for j in range(5):
                ProductReview.objects.create(
                    product=product,
                    user=dummy_user if j == 0 else None,
                    reviewer_name=review_names[j],
                    reviewer_email=f"reviewer{j}@example.com",
                    rating=ratings[j],
                    title=f"Avis sur {product_name}",
                    body=review_texts[j],
                    is_verified_purchase=True,
                    is_approved=True
                )
    
    print(f"Successfully created {len(created_products)} new products.")
    print("Database population completed successfully!")

if __name__ == "__main__":
    populate_database()
