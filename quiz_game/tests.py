from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from users.models import CustomUser
from courses.models import Course
from .models import Level, QuizGameProgress, LevelProgress
from config.app_config import QUIZ_GAME_MAX_UNLOCKED_LEVELS


class QuizGameTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='tester', email='tester@example.com', password='pass'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # create a dummy course
        uploaded = SimpleUploadedFile('file.pdf', b'content')
        self.course = Course.objects.create(
            owner=self.user,
            title='Test Course',
            description='desc',
            file=uploaded,
            file_type='pdf',
            status=Course.Status.READY,
        )

    def test_progress_initialization_creates_10_levels(self):
        """
        Vérifie que lors de l'initialisation d'une progression,
        les 10 niveaux sont créés automatiquement.
        """
        url = reverse('quiz-game-progress')
        resp = self.client.post(url, {'course_id': self.course.id})
        self.assertIn(resp.status_code, (200, 201))
        data = resp.json()
        
        # Vérifier que 10 niveaux ont été créés
        self.assertEqual(len(data['level_progresses']), 10)
        
        # Vérifier que les niveaux sont dans le bon ordre
        for i, level_prog in enumerate(data['level_progresses'], start=1):
            self.assertEqual(level_prog['level']['number'], i)
        
        # Vérifier que le niveau 1 est débloqué
        unlocked = [l['number'] for l in data['unlocked_levels']]
        self.assertEqual(unlocked, [1])

    def test_level_progression_status_generating(self):
        """
        Vérifie que les niveaux commencent en statut 'generating'.
        """
        self.client.post(reverse('quiz-game-progress'), {'course_id': self.course.id})
        progress = QuizGameProgress.objects.get(user=self.user, course=self.course)
        level_progs = list(progress.level_progresses.all())
        
        # Au moins un niveau devrait être en statut 'generating' ou 'ready'
        statuses = [lp.status for lp in level_progs]
        self.assertTrue(any(s in ['generating', 'ready'] for s in statuses))

    def test_start_level_returns_level_progress(self):
        """
        Vérifie que démarrer un niveau retourne son état.
        """
        self.client.post(reverse('quiz-game-progress'), {'course_id': self.course.id})
        url = reverse('quiz-game-level-start', kwargs={'number': 1})
        resp = self.client.post(url, {'course_id': self.course.id})
        
        self.assertIn(resp.status_code, (200, 202))
        data = resp.json()
        self.assertIn(data['status'], ['in_progress', 'generating'])

    def test_submit_level_success_unlocks_next(self):
        """
        Vérifie que valider le niveau 1 déverrouille les niveaux 2 et 3.
        """
        self.client.post(reverse('quiz-game-progress'), {'course_id': self.course.id})
        self.client.post(reverse('quiz-game-level-start', kwargs={'number': 1}), {'course_id': self.course.id})
        
        url = reverse('quiz-game-level-submit', kwargs={'number': 1})
        resp = self.client.post(url, {
            'course_id': self.course.id,
            'completed_quiz_count': 5,
            'score': '100.00',
            'passed': True
        })
        
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        unlocked_nums = [l['number'] for l in data['unlocked_levels']]
        completed_nums = [l['number'] for l in data['completed_levels']]
        
        self.assertIn(2, unlocked_nums)
        self.assertIn(3, unlocked_nums)
        self.assertIn(1, completed_nums)

    def test_max_unlocked_levels_respected(self):
        """
        Vérifie que le nombre de niveaux débloqués n'excède pas QUIZ_GAME_MAX_UNLOCKED_LEVELS (5).
        """
        self.client.post(reverse('quiz-game-progress'), {'course_id': self.course.id})
        
        # Valider les 7 premiers niveaux pour voir si la limite est respectée
        for n in range(1, 8):
            self.client.post(reverse('quiz-game-level-start', kwargs={'number': n}), {'course_id': self.course.id})
            self.client.post(reverse('quiz-game-level-submit', kwargs={'number': n}), {
                'course_id': self.course.id,
                'completed_quiz_count': 999,
                'score': '100.00',
                'passed': True
            })
            
            progress = self.client.get(
                reverse('quiz-game-progress'),
                {'course_id': self.course.id}
            ).json()
            unlocked = [l['number'] for l in progress['unlocked_levels']]
            
            # Au max 5 niveaux devraient être débloqués à la fois
            self.assertLessEqual(len(unlocked), QUIZ_GAME_MAX_UNLOCKED_LEVELS)
