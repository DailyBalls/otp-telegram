from typing import Optional

from pydantic.main import BaseModel
from pydantic import field_validator

from services.otp_services.models import APIResponse


GAME_TYPES = ["slot", "casino", "sports", "sabung", "arcade", "interactive"]

class Game(BaseModel):
    id: Optional[int] = None
    provider_id: Optional[str] = None
    game_type: Optional[str] = None
    game_id: Optional[str] = None
    game_name: Optional[str] = None
    game_code: Optional[str] = None
    image_url: Optional[str] = None
    game_image: Optional[str] = None
    game_url: Optional[str] = None
    game_status: Optional[str] = None
    pass

    @field_validator("game_name", mode="before")
    def validate_game_name(cls, v):
        return v.encode('ascii', errors='ignore').decode('ascii')



class AvailableGames(BaseModel):
    games: Optional[list[Game]] = None

    def add_game(self, game: Game) -> None:
        if self.games is None:
            self.games = []
        for g in self.games:
            if g.game_type == game.game_type and g.game_id == game.game_id and g.game_code == game.game_code:
                return
        self.games.append(game)

    def get_games_by_type(self, game_type: str) -> list[Game]:
        if self.games is None:
            return []
        return [game for game in self.games if game.game_type == game_type]

    def load_from_list(self, data: list[dict]) -> None:
        if data is None:
            return
        for game in data:
            self.games.append(Game(**game))


class Provider(BaseModel):
    provider_id: Optional[str] = None
    provider_name: Optional[str] = None
    provider_name_mobile: Optional[str] = None
    provider_type: Optional[str] = None

    @field_validator("provider_name", "provider_name_mobile", mode="before")
    def validate_provider_name(cls, v):
        return v.encode('ascii', errors='ignore').decode('ascii')