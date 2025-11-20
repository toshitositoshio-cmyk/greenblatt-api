from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Optional, Any, Dict

app = FastAPI()


# =============================
# カスタム例外（大容量データ用）
# =============================
class ExternalDataTooLargeError(Exception):
    """外部データのサイズが大きすぎる場合に投げる例外"""
    pass


# =============================
# /stock-summary 用レスポンスモデル
# =============================
class StockSummary(BaseModel):
    code: str
    name: Optional[str] = None
    market: Optional[str] = None
    as_of: Optional[str] = None

    metrics: Optional[Dict[str, Any]] = None
    greenblatt_score: Optional[float] = None
    turnaround_quality: Optional[str] = None
    verdict: Optional[str] = None
    time_horizon: Optional[str] = None
    summary_text: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None

    # エラー情報（常に含める）
    status: str = "ok"  # "ok" or "error"
    error_code: Optional[str] = None
    error_message: Optional[str] = None


# =============================
# 分析ロジック本体（ここを書き換え）
# =============================
async def fetch_and_build_summary(code: str):
    """
    外部データを取得して各種指標をまとめる関数。
    本番ではここに実際の決算データ取得ロジックを実装する。

    必要なら「大きすぎるPDFを検知して」
    raise ExternalDataTooLargeError を投げるようにする。
    """

    # ▼（例）外部データが重すぎると判断した場合に例外を投げる
    # if size_too_large:
    #     raise ExternalDataTooLargeError()

    # ▼今は仮のダミーデータ（動作確認用）
    return type("X", (), dict(
        name="ダミー銘柄",
        market="東証プライム",
        as_of="2025-11-19T09:00:00+09:00",
        metrics=dict(
            sales_yoy=45.3,
            op_income_yoy=310.0,
            op_margin=12.4,
            roic=18.7
        ),
        greenblatt_score=89.0,
        turnaround_quality="high",
        verdict="BUY",
        time_horizon="mid_term_2x_candidate",
        summary_text="これはダミーデータです。実際には外部データ取得結果を入れてください。",
        raw_data={"dummy": True}
    ))


# =============================
# メインAPI（GET /stock-summary）
# =============================
@app.get("/stock-summary", response_model=StockSummary)
async def get_stock_summary(
    code: str = Query(..., description="日本株の銘柄コード（例: 6227）")
):
    """
    Custom GPT の getStockSummary アクションから呼ばれるエンドポイント。
    銘柄コードを受け取り、構造転換 × 黒字転換 × 高ROIC の観点でまとめたサマリーを返す。
    """
    try:
        # 実データ取得（今はダミー）
        summary = await fetch_and_build_summary(code)

        return StockSummary(
            status="ok",
            code=code,
            name=summary.name,
            market=summary.market,
            as_of=summary.as_of,
            metrics=summary.metrics,
            greenblatt_score=summary.greenblatt_score,
            turnaround_quality=summary.turnaround_quality,
            verdict=summary.verdict,
            time_horizon=summary.time_horizon,
            summary_text=summary.summary_text,
            raw_data=summary.raw_data,
        )

    # 外部データの容量エラーに対処
    except ExternalDataTooLargeError:
        return StockSummary(
            status="error",
            code=code,
            error_code="DATA_TOO_LARGE",
            error_message=(
                f"外部データ取得で一時的なエラーが発生しました（{code}）。"
                "決算資料のデータサイズが大きすぎたため取得に失敗しました。"
            ),
        )

    # 想定外エラーも必ず 200 で返して GPT が読めるようにする
    except Exception as e:
        return StockSummary(
            status="error",
            code=code,
            error_code="UNEXPECTED_ERROR",
            error_message=f"銘柄コード {code} の処理中に予期せぬエラー: {type(e).__name__}: {e}",
        )


# =============================
# GPT から受け取る決算データ用モデル
# =============================
class FinancialInput(BaseModel):
    code: str
    name: Optional[str] = None
    market: Optional[str] = None

    # GPTが抽出して送る決算・財務データ
    sales: Optional[float] = None
    sales_yoy: Optional[float] = None
    op_income: Optional[float] = None
    op_income_yoy: Optional[float] = None
    gross_margin: Optional[float] = None
    op_margin: Optional[float] = None
    nopat: Optional[float] = None
    invested_capital: Optional[float] = None
    roic: Optional[float] = None
    earnings_yield: Optional[float] = None

    # 株価指標
    price: Optional[float] = None
    vwap: Optional[float] = None
    ma25: Optional[float] = None
    ma75: Optional[float] = None

    # 需給データ
    credit_ratio: Optional[float] = None

    # 追加で任意のデータも受け取れる
    extra: Optional[Dict[str, Any]] = None


# =============================
# POST /process-financials
# GPT からの JSON を受け取って解析
# =============================
@app.post("/process-financials")
async def process_financials(data: FinancialInput):
    """
    ChatGPT が Web/ブラウズで取得した決算データ(JSON)を受け取り、
    Greenblatt型の簡易判定を行って返すエンドポイント。
    """

    # ROIC 計算
    if data.roic is not None:
        roic = data.roic
    elif data.nopat is not None and data.invested_capital:
        roic = (data.nopat / data.invested_capital) * 100
    else:
        roic = None

    # Earnings Yield
    ey = data.earnings_yield

    # Greenblatt スコア（超シンプルな例）
    score = 0.0
    if roic is not None:
        score += min(roic, 30) * 1.5  # ROIC 30%上限でウェイト1.5
    if ey is not None:
        score += min(ey, 20) * 1.0    # EY 20%上限でウェイト1.0

    verdict = "HOLD"
    if roic is not None and ey is not None:
        if roic > 15 and ey > 10:
            verdict = "BUY"
        elif roic < 5:
            verdict = "EXIT"

    return {
        "code": data.code,
        "name": data.name,
        "roic": roic,
        "ey": ey,
        "greenblatt_score": score,
        "verdict": verdict,
        "raw": data.dict()
    }
