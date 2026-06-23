from django.core.management.base import BaseCommand
from django.db import transaction

from courses.models import CourseChunk
from courses.vector_store import get_embedding_model


class Command(BaseCommand):
    help = "Backfill missing pgvector embeddings for CourseChunk rows"

    def add_arguments(self, parser):
        parser.add_argument("--batch-size", type=int, default=256, help="Number of chunks to update per DB transaction")

    def handle(self, *args, **options):
        batch_size = options.get("batch_size") or 256
        model = get_embedding_model()

        qs = CourseChunk.objects.filter(embedding__isnull=True).order_by("id")
        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS("No CourseChunk rows without embeddings found."))
            return

        self.stdout.write(f"Found {total} chunks without embeddings. Processing in batches of {batch_size}...")

        processed = 0
        while True:
            batch = list(qs[:batch_size])
            if not batch:
                break

            texts = [c.content for c in batch]
            try:
                embeddings = model.encode(texts, show_progress_bar=False)
            except Exception as e:
                self.stderr.write(f"Embedding model failed: {e}")
                return

            # embeddings is numpy array or list; ensure list of lists
            emb_list = [e.tolist() if hasattr(e, "tolist") else list(e) for e in embeddings]

            for c, emb in zip(batch, emb_list):
                c.embedding = emb

            with transaction.atomic():
                CourseChunk.objects.bulk_update(batch, ["embedding"])

            processed += len(batch)
            self.stdout.write(f"Updated {processed}/{total}")

        self.stdout.write(self.style.SUCCESS(f"Backfill complete: {processed} rows updated."))
