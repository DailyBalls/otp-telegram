class BotConfig:
    def __init__(self, web_id: str, site_name: str, whitelist_mode: bool, whitelist_ids: list[int], otp_host: str = None) -> None:
        self.web_id = web_id
        self.site_name = site_name
        self.whitelist_ids = whitelist_ids
        self.whitelist_mode = whitelist_mode
        self.otp_host = otp_host
