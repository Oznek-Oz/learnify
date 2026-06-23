from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0004_coursechunk_embedding'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE INDEX coursechunk_embedding_ivfflat_idx
                ON courses_coursechunk
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100);
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS coursechunk_embedding_ivfflat_idx;
            """,
        ),
    ]