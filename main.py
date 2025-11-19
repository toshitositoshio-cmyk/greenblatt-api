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
# レスポンスモデル
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

    # ★ エラーを内包して返すためのフィールド
    status: str = "ok"                # "ok" or "error"
    error_code: Optional[str] = None
    error_message: Optional[str] = None


# =============================
# 分析ロジック本体（ここを書き換え）
# =============================
async def fetch_and_build_summary(code: str):
    """
    外部データを取得して各種指標をまとめる関数。
    ここをあなたの実際のロジックに置き換えてください。

    必要なら「大きすぎるPDFを検知して」
    raise ExternalDataTooLargeError を投げるようにします。
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
# メインAPI（エラーを必ず吸収）
# =============================
@app.get("/stock-summary", response_model=StockSummary)
async def get_stock_summary(
    code: str = Query(..., description="日本株の銘柄コード（例: 6227）")
):
    try:
        # 実データ取得
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

    # ★ 外部データの容量エラーに対処
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

    # ★ 予期せぬエラーも必ず 200 で返す
    except Exception as e:
        return StockSummary(
            status="error",
            code=code,
            error_code="UNEXPECTED_ERROR",
            error_message=f"銘柄コード {code} の処理中に予期せぬエラー: {type(e).__name__}: {e}",
        )
