from channels.generic.websocket import AsyncWebsocketConsumer
from .models import ChessGame
from channels.db import database_sync_to_async
import json
import chess
import asyncio

# key: user_id, value: asyncio.Event to signal reconnection
CONNECTED_USERS = {}


class ChessConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.user = self.scope["user"]
            self.game_id = self.scope["url_route"]["kwargs"]['game_id']
            self.game_room_name = f"game_{self.game_id}"
            
            ##### reconnection logic
            # Handle Reconnection
            if self.user.id in CONNECTED_USERS:
                old_event = CONNECTED_USERS[self.user.id]
                old_event.set()

            self.disconnect_event = asyncio.Event()
            CONNECTED_USERS[self.user.id] = self.disconnect_event
            #####

            await self.channel_layer.group_add(
                self.game_room_name, self.channel_name
            )
            await self.accept()
            
        except Exception as e:
            await self.close()


    async def disconnect(self, close_code):
        ##### reconnection logic
        if not hasattr(self, 'game_room_name'):
            return
        #####

        # Leaving group immediately
        await self.channel_layer.group_discard(
            self.game_room_name, self.channel_name
        )

        ##### reconnection logic
        # Waiting for reconnection (The Grace Period) or the chance
        try:
            await asyncio.wait_for(self.disconnect_event.wait(), timeout=2.0)
            return 
        except asyncio.TimeoutError:
            pass
        except asyncio.CancelledError:
            pass

        # Cleaning up Dictionary
        if hasattr(self, 'user') and self.user.id in CONNECTED_USERS:
            if CONNECTED_USERS[self.user.id] == self.disconnect_event:
                del CONNECTED_USERS[self.user.id]
        #####

        try:            
            # Fetching game
            game = await database_sync_to_async(ChessGame.objects.get)(id=self.game_id)
            
            winner_id = None
            
            if game.status == "active":
                player_white, player_black = await database_sync_to_async(
                    lambda: (game.player_white, game.player_black)
                )()
                
                if self.user.id == player_white.id:
                    winner = player_black
                else:
                    winner = player_white
                
                # Updateing DB
                def update_game():
                    game.status = "finished"
                    game.winner = winner
                    game.save()
                await database_sync_to_async(update_game)()
                
                winner_id = str(winner.id)

            elif game.status == "finished":
                winner = await database_sync_to_async(lambda: game.winner)()
                winner_id = str(winner.id) if winner else None

            # Broadcasting "Game Over"
            event = {
                'type': 'chess_move_handler',
                'move': None, 
                'status': "finished",
                'winner': winner_id
            }
            
            await self.channel_layer.group_send(self.game_room_name, event)

        except BaseException as e:
            # print(f"critical ERROR in disconnect logic: {e}")
            pass
    
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
