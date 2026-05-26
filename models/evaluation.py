import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error


def evaluate(y_true, y_pred):
    """
    Calcula MAE, RMSE y MAPE.

    Returns
    -------
    tuple[float, float, float]
        (MAE, RMSE, MAPE)
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    if len(y_true) == 0:
        raise ValueError("evaluate(): y_true está vacío — el conjunto de test puede ser demasiado pequeño.")
    if len(y_pred) == 0:
        raise ValueError("evaluate(): y_pred está vacío.")

    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))

    mask = y_true != 0
    if mask.sum() == 0:
        mape = float("nan")
    else:
        mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100

    return float(mae), float(rmse), float(mape)
