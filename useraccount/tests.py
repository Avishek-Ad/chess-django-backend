from django.urls import reverse
from .models import User
from rest_framework.test import APITestCase

class UserCreateViewTest(APITestCase):
    def test_user_create(self):
        data = {
            "email": "weorisf@gmail.com",
            "password": "asdsdyukjfsd%$23",
            "confirm_password": "asdsdyukjfsd%$23"
        }
        response = self.client.post(reverse('user-register'), data=data, content_type="application/json")
        self.assertEqual(response.data['username'], "weorisf")
        self.assertContains(response, 'id', status_code=201)

class DashboardStatsViewTest(APITestCase):
    def test_access_by_unauthenticated_user(self):
        returned_data = {
            "username": "Guest",
            "total_game_played": 0,
            "total_game_win": 0,
            "total_game_loss": 0,
            "total_game_draw": 0,
        }
        response = self.client.get(reverse('user-dashboard-stats'))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, returned_data)

    def test_access_by_authenticated_user(self):
        User.objects.create_user(email="abcdefg@gmail.com", password="awdrgyjbt!@#")

        self.client.login(email="abcdefg@gmail.com", password="awdrgyjbt!@#")
        response = self.client.get(reverse('user-dashboard-stats'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], "abcdefg")