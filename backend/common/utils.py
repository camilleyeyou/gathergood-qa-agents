from django.utils.text import slugify


def generate_unique_slug(name: str, model_class, slug_field: str = 'slug') -> str:
    base_slug = slugify(name)
    if not base_slug:
        base_slug = 'untitled'
    slug = base_slug
    n = 1
    while model_class.objects.filter(**{slug_field: slug}).exists():
        n += 1
        slug = f"{base_slug}-{n}"
    return slug
