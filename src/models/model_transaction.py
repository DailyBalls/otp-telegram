from typing import Optional
from pydantic import BaseModel

REPORT_TYPE_PROGRESS = "PROGRESS"
REPORT_TYPE_REJECTED = "REJECTED"
REPORT_TYPE_SUCCESS  = "SUCCESS"
class ModelTransaction(BaseModel):
    id: Optional[int] = None
    description: Optional[str] = None
    channel: Optional[str] = None
    type: Optional[str] = None
    report: Optional[str] = None
    lastUpdate: Optional[str] = None
    amount: Optional[int] = None
    debit: Optional[int] = None
    credit: Optional[int] = None
    balance: Optional[int] = None

    def get_transaction_type_icon(self) -> str:
        if self.type == "deposit"             : return "📥"
        elif self.type == "deposit_crypto"    : return "C📥"
        elif self.type == "withdraw"       : return "📤"
        elif self.type == "withdraw_crypto": return "C📤"
        else: return "❓"

    def get_report_type_icon(self) -> str:
        if self.report == REPORT_TYPE_PROGRESS: return "🕒"
        elif self.report == REPORT_TYPE_REJECTED: return "❌"
        elif self.report == REPORT_TYPE_SUCCESS: return "✅"
        else: return "❓"