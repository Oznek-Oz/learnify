"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')), # On inclut les URLs de l'application users pour gérer les endpoints liés à l'authentification et aux profils des utilisateurs (ex: inscription, login, profil, etc.)
    path('api/courses/', include('courses.urls')),
    path('api/quiz/',    include('quizz.urls')),
    path('api/flashcards/', include('flashcards.urls'))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) # Permet de servir les fichiers médias (PDF, images) pendant le développement en utilisant les paramètres MEDIA_URL et MEDIA_ROOT définis dans settings.py
