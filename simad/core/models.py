import uuid

from django.db import models
from django_extensions.db.models import ActivatorModel
from django_extensions.db.models import TimeStampedModel


class SIMADBASEMODEL(ActivatorModel, TimeStampedModel):
    """
    Abstract base model for all SIMAD models.

    Provides:
        - UUID primary key (id)
        - created / modified timestamps  (TimeStampedModel)
        - activate / deactivate helpers   (ActivatorModel)
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True
        ordering = ["-created"]
