from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand

from accounts.models import Circle, TrainerProfile, User
from tasks.models import Batch, Holiday, Task


class Command(BaseCommand):
    help = "Seed TRMS with sample users, circles, tasks, batches, and holidays."

    def handle(self, *args, **options):
        admin, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "name": "System Admin",
                "email": "admin@trms.local",
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin.set_password("admin12345")
        admin.save()

        manager, _ = User.objects.get_or_create(
            username="manager1",
            defaults={"name": "Mina Manager", "email": "manager1@trms.local", "role": User.Role.MANAGER},
        )
        manager.set_password("manager12345")
        manager.save()

        circle_lead, _ = User.objects.get_or_create(
            username="circlelead1",
            defaults={"name": "Chris Circle", "email": "circlelead1@trms.local", "role": User.Role.CIRCLE_LEAD},
        )
        circle_lead.set_password("circle12345")
        circle_lead.save()

        circle, _ = Circle.objects.get_or_create(name="Digital Learning", defaults={"manager": manager})
        trainer_names = [("trainer1", "Tara Trainer"), ("trainer2", "Dev Trainer")]
        trainers = []
        for username, name in trainer_names:
            trainer, _ = User.objects.get_or_create(
                username=username,
                defaults={"name": name, "email": f"{username}@trms.local", "role": User.Role.TRAINER},
            )
            trainer.set_password("trainer12345")
            trainer.save()
            TrainerProfile.objects.get_or_create(user=trainer, defaults={"skills": "Python, LMS", "circle": circle})
            trainers.append(trainer)

        holiday, _ = Holiday.objects.get_or_create(date=date.today() + timedelta(days=3), defaults={"description": "Festival Holiday"})
        batch, _ = Batch.objects.get_or_create(
            name="Java Bootcamp April",
            defaults={
                "course": "Advanced Java",
                "start_date": date.today() - timedelta(days=5),
                "end_date": date.today() + timedelta(days=20),
                "trainer": trainers[0],
                "circle": circle,
                "assessment_dates": [(date.today() + timedelta(days=7)).isoformat()],
            },
        )
        batch.holidays.add(holiday)

        for index, trainer in enumerate(trainers):
            for day_offset in range(1, 6):
                Task.objects.get_or_create(
                    trainer=trainer,
                    date=date.today() - timedelta(days=day_offset),
                    task_type=Task.TaskType.TRAINING if day_offset % 2 == 0 else Task.TaskType.CONTENT,
                    defaults={
                        "hours": Decimal("6.5") + index,
                        "description": f"Sample work log {day_offset} for {trainer.name}",
                        "status": Task.Status.APPROVED if day_offset % 2 == 0 else Task.Status.PENDING,
                    },
                )

        self.stdout.write(self.style.SUCCESS("Sample TRMS data created."))
