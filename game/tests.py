from rest_framework.test import APITestCase
from django.urls import reverse
from useraccount.models import User
from .models import ChessGame
import uuid

class GameViewTests(APITestCase):
    def setUp(self):
        self.one_player = User.objects.create_user(email="zxcvbnm@gmail.com", password="awdrgyjbt!@#")
        self.user = User.objects.create_user(email="abcdefg@gmail.com", password="awdrgyjbt!@#")
        self.game = ChessGame.objects.create(player_white=self.one_player)
        self.full_game = ChessGame.objects.create(player_white=self.one_player, player_black=self.user)
        self.already_joined_game = ChessGame.objects.create(player_white=self.user)
        self.black_player = ChessGame.objects.create(player_black=self.user, player_white=self.one_player)
        self.white_player = ChessGame.objects.create(player_white=self.user, player_black=self.one_player)

    def test_create_game_by_authenticated_user(self):
        self.client.login(email="abcdefg@gmail.com", password="awdrgyjbt!@#")
        response = self.client.post(reverse("create-game"), data={"play_as":"white"})
        self.assertContains(response, "gameid", status_code=201)

    def test_join_game_by_authenticated_user(self):
        self.client.login(email="abcdefg@gmail.com", password="awdrgyjbt!@#")
        response = self.client.post(reverse("join-game", kwargs={"gameid":self.game.id}))
        self.assertEqual(response.data['message'], "You joined successfully")
        self.assertContains(response, "gameid", status_code=200)

        game_id = response.data['gameid']
        game = ChessGame.objects.get(id=game_id)
        self.assertEqual(game.status, "active")
    
    def test_join_game_without_valid_gameid(self):
        random_uuid = uuid.uuid4()
        self.client.login(email="abcdefg@gmail.com", password="awdrgyjbt!@#")
        response = self.client.post(reverse("join-game", kwargs={"gameid":random_uuid}))
        self.assertEqual(response.data['message'], "Game doesnot exists")
        self.assertEqual(response.status_code, 404)

    def test_join_game_with_user_already_in_game(self):
        self.client.login(email="abcdefg@gmail.com", password="awdrgyjbt!@#")
        response = self.client.post(reverse("join-game", kwargs={"gameid":self.already_joined_game.id}))
        self.assertEqual(response.data['message'], "Your are already in the game")
        self.assertEqual(response.status_code, 400)
    
    def test_join_game_with_two_player_already_in_game(self):
        self.client.login(email="abcdefg@gmail.com", password="awdrgyjbt!@#")
        response = self.client.post(reverse("join-game", kwargs={"gameid":self.full_game.id}))
        self.assertEqual(response.data['message'], "Game is already Full")
        self.assertEqual(response.status_code, 400)

    def test_game_status_with_valid_game(self):
        self.client.login(email="abcdefg@gmail.com", password="awdrgyjbt!@#")
        response = self.client.get(reverse("game-status", kwargs={"gameid":self.already_joined_game.id}))
        self.assertContains(response, "status", status_code=200)
    
    def test_game_status_with_invalid_gameid(self):
        random_uuid = uuid.uuid4()
        self.client.login(email="abcdefg@gmail.com", password="awdrgyjbt!@#")
        response = self.client.get(reverse("game-status", kwargs={"gameid":random_uuid}))
        self.assertEqual(response.data['message'], "Game Not Found")
        self.assertEqual(response.status_code, 404)
    
    def test_player_side_with_player_black(self):
        self.client.login(email="abcdefg@gmail.com", password="awdrgyjbt!@#")
        response = self.client.get(reverse("player-side", kwargs={"gameid":self.black_player.id}))
        self.assertEqual(response.data["orientation"], "black")
        self.assertEqual(response.data["black"], "abcdefg")
    
    def test_player_side_with_player_white(self):
        self.client.login(email="abcdefg@gmail.com", password="awdrgyjbt!@#")
        response = self.client.get(reverse("player-side", kwargs={"gameid":self.white_player.id}))
        self.assertEqual(response.data["orientation"], "white")
        self.assertEqual(response.data["white"], "abcdefg")
    
    def test_player_side_without_requesting_user(self):
        self.client.login(email="abcdefg@gmail.com", password="awdrgyjbt!@#")
        response = self.client.get(reverse("player-side", kwargs={"gameid":self.game.id}))
        self.assertEqual(response.data["message"], "invalid request")
        self.assertEqual(response.status_code, 400)
    
    def test_player_side_with_invalid_gameid(self):
        random_uuid = uuid.uuid4()
        self.client.login(email="abcdefg@gmail.com", password="awdrgyjbt!@#")
        response = self.client.get(reverse("player-side", kwargs={"gameid":random_uuid}))
        self.assertEqual(response.data["message"], "Game Not Found")
        self.assertEqual(response.status_code, 404)

    def test_join_a_random_game_first_request(self):
        self.client.login(email="zxcvbnm@gmail.com", password="awdrgyjbt!@#")
        response = self.client.post(reverse("join-a-random-game"))
        self.assertEqual(response.data['message'], "Waiting for Match")
        self.assertEqual(response.status_code, 200)
    
    def test_join_a_random_game_more_than_one_request(self):
        self.client.login(email="abcdefg@gmail.com", password="awdrgyjbt!@#")
        self.client.post(reverse("join-a-random-game"))
        response = self.client.post(reverse("join-a-random-game"))
        self.assertEqual(response.data['message'], "Already waiting for Match")
        self.assertEqual(response.status_code, 200)
    
    def test_quit_waiting_for_random_match(self):
        self.client.login(email="abcdefg@gmail.com", password="awdrgyjbt!@#")
        self.client.post(reverse("join-a-random-game"))
        response = self.client.post(reverse("quit-waiting-for-a-random-game"))
        self.assertEqual(response.data['message'], "Removed successfully")
        self.assertEqual(response.status_code, 200)
