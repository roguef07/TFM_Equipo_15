from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
import xgboost as xgb


def create_lr_pipeline() -> Pipeline:
    """Regresión Lineal con escalado estándar."""
    return Pipeline([
        ("scaler", StandardScaler()),
        ("model", LinearRegression()),
    ])


def create_xgb_pipeline(
    n_estimators: int = 100,
    max_depth: int = 5,
    learning_rate: float = 0.1,
) -> Pipeline:
    """Regresor XGBoost (los árboles no requieren escalado)."""
    return Pipeline([
        ("model", xgb.XGBRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
        )),
    ])
