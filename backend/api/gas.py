# backend/api/gas.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/gas")
def get_gas():
    return {"gas_fee": "placeholder"}
