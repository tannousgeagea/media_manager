# populate_db.py

from django.core.management.base import BaseCommand
from database.models import PlantInfo, EdgeBoxInfo
import json

class Command(BaseCommand):
    help = 'Populate database with plant information and edge box information'

    def handle(self, *args, **kwargs):
        # Sample data to populate PlantInfo
        plants_data = [
            {
                "plant_id": "amk.iserlon",
                "plant_name": "AMK",
                "plant_location": "Iserlon",
                "domain": "amk.wasteant.com",
            },

        ]

        edge_boxes_data = {
            "amk.iserlon": [
                {"edge_box_id": "eb1.g3.iserlohn.amk.want", "edge_box_location": "gate03"},
                {"edge_box_id": "eb1.g4.iserlohn.amk.want", "edge_box_location": "gate04"},
            ],
        }

        # Step 1: Populate PlantInfo
        for plant_data in plants_data:
            plant, created = PlantInfo.objects.get_or_create(
                plant_id=plant_data["plant_id"],
                plant_name=plant_data["plant_name"],
                plant_location=plant_data["plant_location"],
                domain=plant_data["domain"],
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Plant '{plant.plant_name}' created."))

            # Step 2: Populate EdgeBoxInfo for each plant
            if plant.plant_id in edge_boxes_data:
                for edge_box_data in edge_boxes_data[plant.plant_id]:
                    edge_box, created = EdgeBoxInfo.objects.get_or_create(
                        plant=plant,
                        edge_box_id=edge_box_data["edge_box_id"],
                        location=edge_box_data["edge_box_location"],
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f"Edge Box '{edge_box.edge_box_id}' created for plant '{plant.plant_name}'."))

        self.stdout.write(self.style.SUCCESS('Database population complete.'))
