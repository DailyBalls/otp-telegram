class BotConfig:
    def __init__(self, server_name: str, whitelist_mode: bool, whitelist_ids: list[int]) -> None:
        self.server_name = server_name
        self.whitelist_ids = whitelist_ids
        self.whitelist_mode = whitelist_mode