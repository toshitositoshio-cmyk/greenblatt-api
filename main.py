from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Japan Equity Screening API")

class StockSummary(BaseModel):
    ticker: str
    name: Optional[str] = None
    fiscal_quarter: Optional[str] = None
    sales: Optional[float] = None
    op_income: Optional[float] = None
    ordinary_income: Optional[float] = None
    net_income: Optional[float] = None
    gross_margin: Optional[float] = None
    op_margin: Optional[float] = None
    sales_yoy: Optional[float] = None
    op_income_yoy: Optional[float] = None
    progress_sales: Optional[float] = None
    progress_op_income: Optional[float] = None
    roic: Optional[float] = None
    roic_prev: Optional[float] = None
    earnings_yield: Optional[float] = None
    price: float
    vwap: Optional[float] = None
    ma25: Optional[float] = None
    ma75: Optional[float] = None
    volume_today: Optional[float] = None
    volume_1w_avg: Optional[float] = None
    credit_long: Optional[float] = None
    credit_short: Optional[float] = None
    credit_ratio: Optional[float] = None
    volume_status: Optional[str] = None
    note: Optional[str] = None

@app.get("/stock-summary", response_model=StockSummary)
def get_stock_summary(ticker: str):
    return StockSummary(
        ticker=ticker,
        name="Dummy Corp.",
        fiscal_quarter="2025Q2",
        sales=10000.0,
        op_income=1500.0,
        ordinary_income=1400.0,
        net_income=900.0,
        gross_margin=35.0,
        op_margin=15.0,
        sales_yoy=120.0,
        op_income_yoy=300.0,
        progress_sales=55.0,
        progress_op_income=60.0,
        roic=18.0,
        roic_prev=10.0,
        earnings_yield=12.0,
        price=1234.0,
        vwap=1220.0,
        ma25=1150.0,
        ma75=980.0,
        volume_today=500000.0,
        volume_1w_avg=300000.0,
        credit_long=200000.0,
        credit_short=50000.0,
        credit_ratio=4.0,
        volume_status="normal",
        note="This is dummy data for testing."
    )
