import random
from django.core.management.base import BaseCommand
from simad.catalog.models import Testimonial, Product
from simad.global_data.enum import ReviewRatingChoices

class Command(BaseCommand):
    help = 'Populate the database with realistic testimonials for the landing page.'

    def handle(self, *args, **options):
        self.stdout.write("Starting testimonial population...")

        testimonials_data = [
            {"name": "Moussa Bello", "content": "Les produits SIMAD ont transformé notre routine d'hygiène industrielle. Une efficacité redoutable sur les graisses lourdes !", "rating": ReviewRatingChoices.FIVE},
            {"name": "Chantal Mbarga", "content": "Le gel hydroalcoolique SimaGel est le meilleur que j'ai utilisé au Cameroun. Il ne dessèche pas les mains et sent très bon.", "rating": ReviewRatingChoices.FIVE},
            {"name": "Dr. Jean-Pierre Fotso", "content": "Livraison rapide à Yaoundé et service client impeccable. Les solutions de désinfection SIMAD sont aux normes internationales.", "rating": ReviewRatingChoices.FIVE},
            {"name": "Samuel Eto'o Junior", "content": "Une qualité internationale fabriquée directement ici au pays. C'est une fierté de voir une telle expertise camerounaise.", "rating": ReviewRatingChoices.FOUR},
            {"name": "Marie-Laure Temgoua", "content": "Indispensable pour notre laboratoire de recherche. Les réactifs SimaPro sont d'une pureté exemplaire et les résultats sont constants.", "rating": ReviewRatingChoices.FIVE},
            {"name": "Alhadji Ousmanou", "content": "Nous utilisons SimaWash Ultra pour notre service de blanchisserie industrielle. Le linge est éclatant et les coûts sont très abordables.", "rating": ReviewRatingChoices.FIVE},
            {"name": "Alice Ndemen", "content": "Pour ma maison, je ne jure que par SimaClean. C'est efficace, ça sent bon et c'est fabriqué chez nous. Bravo SIMAD !", "rating": ReviewRatingChoices.FIVE},
            {"name": "Professeur Essomba", "content": "En tant qu'hygiéniste hospitalier, je valide la gamme SimaDésinfect. Elle répond parfaitement aux protocoles d'asepsie les plus exigeants.", "rating": ReviewRatingChoices.FIVE},
            {"name": "Inès Kameni", "content": "Le rapport qualité-prix est imbattable. J'ai remplacé toutes mes marques importées par SIMAD et je ne regrette absolument pas.", "rating": ReviewRatingChoices.FOUR},
            {"name": "Directeur Logistique - Port Douala", "content": "La solution SimaForce a réduit notre temps de nettoyage des machines de 30%. Un gain de productivité énorme pour nos équipes.", "rating": ReviewRatingChoices.FIVE},
        ]

        products = list(Product.objects.all())

        for data in testimonials_data:
            product = random.choice(products) if products else None
            Testimonial.objects.create(
                full_name=data["name"],
                content=data["content"],
                rating=data["rating"],
                product=product,
                is_published=True
            )

        self.stdout.write(self.style.SUCCESS(f"Successfully populated {len(testimonials_data)} testimonials."))

if __name__ == "__main__":
    pass
