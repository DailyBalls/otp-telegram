from models.base_state_model import BaseStateModel

from typing import Optional

class DepositChannel(BaseStateModel):
    name: Optional[str] = None
    type: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    
class AvailableDepositChannel(BaseStateModel):
    channels: Optional[list[DepositChannel]] = None
    