from channels.generic.websocket import AsyncWebsocketConsumer
from .models import ChessGame
from useraccount.models import User
from channels.db import database_sync_to_async
import json
import chess
import asyncio

# key: user_id, value: asyncio.Event to signal reconnection
CONNECTED_USERS = {}


class ChessConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        #### checking if user is connected or reconnected ####
        user_id = self.scope["user"].id
        # signal reconnection
        if user_id in CONNECTED_USERS:
            CONNECTED_USERS[user_id].set()  # old consumer knows user reconnected
        else:
            CONNECTED_USERS[user_id] = asyncio.Event()
        self.reconnect_event = CONNECTED_USERS[user_id]
        #### ####

        self.game_id = self.scope["url_route"]["kwargs"]['game_id']
        self.game_room_name = f"game_{self.game_id}"

        # join game room
        await self.channel_layer.group_add(
            self.game_room_name, self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.game_room_name, self.channel_name
        )

        # lets give the user 2 second to reconnect
        await asyncio.sleep(2)
        if self.reconnect_event.is_set():
            return
        
        # Load game safely
        game = await database_sync_to_async(ChessGame.objects.get)(id=self.game_id)

        winner = None  # IMPORTANT

        if game.status == "active":

            # Load players safely
            player_white, player_black = await database_sync_to_async(
                lambda: (game.player_white, game.player_black)
            )()
            disconnected_user = self.scope["user"]

            # Determine winner WITHOUT hitting DB inside async
            if disconnected_user.id == player_white.id:
                winner = player_black
            else:
                winner = player_white

            # Save changes safely
            def update_game():
                game.status = "finished"
                game.winner = winner
                game.save()

            await database_sync_to_async(update_game)()

        # Prepare event payload
        event = {
            'type': 'chess_move_handler',
            'move': None,
            'status': game.status,  # OK, primitive field
            'winner': str(winner.id) if winner else None
        }

        # Notify the opponent
        await self.channel_layer.group_send(self.game_room_name, event)

        # cleanup
        user_id = self.scope["user"].id
        if user_id in CONNECTED_USERS:
            del CONNECTED_USERS[user_id]

    
    async def receive(self, text_data):
        data = json.loads(text_data)
        move_from = data.get('from')
        move_to = data.get('to')
        player = data.get('player') # black or white

        game = await database_sync_to_async(ChessGame.objects.get)(id=self.game_id)

        if player == "white":
            current_player = await database_sync_to_async(lambda: game.player_white)()
        else:
            current_player = await database_sync_to_async(lambda: game.player_black)()

        # validating the moves
        board = chess.Board(game.board_fen)
        uci_move = chess.Move.from_uci(f"{move_from}{move_to}")

        # turn 1->white and 0->black
        if (board.turn and player != "white") or (not board.turn and player != 'black'):
            await self.send(text_data=json.dumps({'error':"Not your turn"}))
            return

        if uci_move not in board.legal_moves:
            await self.send(text_data=json.dumps({'error':"Illegal Move"}))
            return
        
        # Applying the move
        board.push(uci_move)
        move_record = {
            "from":move_from,
            "to":move_to,
            "player":player,
            "piece":board.piece_at(chess.parse_square(move_to)).symbol(),
            "turn":len(game.move_history)+1
        }
        game.move_history.append(move_record)
        game.board_fen = board.fen()


        # checking game outcome
        if board.is_checkmate():
            game.status = "finished"
            game.winner = current_player
        elif board.is_stalemate() or board.is_insufficient_material() or board.is_seventyfive_moves() or board.is_fivefold_repetition():
            # game is a draw
            game.status = "finished"
            game.winner = None

        await database_sync_to_async(game.save)()

        event = {
            'type':'chess_move_handler',
            'move':move_record,
            'status':game.status,
            'winner':str(game.winner.id) if game.winner else None
        }

        # broadcasting moves to all players in the game
        await self.channel_layer.group_send(
            self.game_room_name, event
        )

    async def chess_move_handler(self, event):
        move_record = event['move']
        status = event['status']
        winner = event['winner']
        # sending moves to websocket (browser)
        await self.send(text_data=json.dumps({"move":move_record, "status":status, "winner":winner}))
