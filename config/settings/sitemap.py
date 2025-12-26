# from django.urls import reverse
# from django.contrib.sitemaps import Sitemap
# from django.utils import timezone

# # If you have a BlogPost model, import it. If not, skip blog sitemap.
# try:
#     from booking.models import BlogPost  # adjust import to your blog model path
# except Exception:
#     BlogPost = None


# class StaticViewSitemap(Sitemap):
#     """
#     Sitemap for static views defined in your urlpatterns.
#     Keep the list of names in `items()` for maintainability.
#     """
#     priority = 0.8
#     changefreq = "weekly"

#     def items(self):
#         # Use your URL names as defined in urls.py
#         return [
#             "home",
#             "contact",
#             "faqs",
#             "ourcompany",
#             "rates",
#             "blog",
#             "team",  # note: your url name for teams is 'team' in your provided urls
#         ]

#     def location(self, item):
#         return reverse(item)


# if BlogPost is not None:
#     class BlogSitemap(Sitemap):
#         """
#         Sitemap for blog posts.
#         Requires your BlogPost model to have fields:
#           - get_absolute_url() or provide location()
#           - updated_at or modified datetime field (optional)
#           - published boolean / status (optional)
#         """
#         changefreq = "daily"
#         priority = 0.9

#         def items(self):
#             # Filter only published posts (adjust field names to your model)
#             qs = BlogPost.objects.filter(published=True) if hasattr(BlogPost, "published") else BlogPost.objects.all()
#             return qs.order_by("-updated_at") if hasattr(BlogPost, "updated_at") else qs

#         def lastmod(self, obj):
#             # Use updated_at if present, else created_at, else None
#             if hasattr(obj, "updated_at") and obj.updated_at:
#                 return obj.updated_at
#             if hasattr(obj, "modified") and obj.modified:
#                 return obj.modified
#             if hasattr(obj, "created_at") and obj.created_at:
#                 return obj.created_at
#             return None

#         def location(self, obj):
#             # Prefer get_absolute_url on model
#             if hasattr(obj, "get_absolute_url"):
#                 return obj.get_absolute_url()
#             # Fallback: try to build from a slug attribute
#             if hasattr(obj, "slug"):
#                 return reverse("blog:detail", kwargs={"slug": obj.slug})  # adjust to your blog detail url name
#             return "/blog/"  # safe fallback
