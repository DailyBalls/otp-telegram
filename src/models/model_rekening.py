from typing import Optional
from pydantic import BaseModel


class Rekening(BaseModel):
    bank_name: Optional[str] = None
    bank_account_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    default: Optional[bool] = False