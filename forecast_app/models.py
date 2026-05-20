import itertools
import logging
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX

logger = logging.getLogger(__name__)


def sarima_auto_tune(series, seasonal_period=52):
    """
    Búsqueda exhaustiva de hiperparámetros SARIMA y devuelve el modelo con menor AIC.

    Espacio de búsqueda:
        p, q ∈ {0, 1, 2}  |  d ∈ {0, 1}
        P, Q ∈ {0, 1}      |  D = 0  (fijo: D=1 con s=52 es muy lento)
        s = seasonal_period (52 semanas por defecto)
    Total: 72 combinaciones (18 pdq × 4 estacionales).

    Returns
    -------
    SARIMAXResults | None
        None únicamente cuando todas las configuraciones fallan.
        Los llamadores DEBEN verificar None antes de llamar a .forecast().
    """
    p_range = range(0, 3)
    d_range = range(0, 2)
    q_range = range(0, 3)
    P_range = Q_range = range(0, 2)
    # D fijado a 0: la diferenciación estacional con s=52 es muy costosa
    # computacionalmente y raramente converge con ~2 años de datos.
    D_values = [0]

    pdq = list(itertools.product(p_range, d_range, q_range))
    seasonal_pdq = list(itertools.product(P_range, D_values, Q_range))

    best_aic = np.inf
    best_model = None
    failed = 0

    for param in pdq:
        for seasonal in seasonal_pdq:
            # El modelo completamente nulo es degenerado — se salta
            if param == (0, 0, 0) and seasonal == (0, 0, 0):
                continue
            try:
                model = SARIMAX(
                    series,
                    order=param,
                    seasonal_order=(seasonal[0], seasonal[1], seasonal[2], seasonal_period),
                    enforce_stationarity=False,
                    enforce_invertibility=False,
                )
                results = model.fit(disp=False)

                if np.isfinite(results.aic) and results.aic < best_aic:
                    best_aic = results.aic
                    best_model = results

            except Exception as e:
                failed += 1
                logger.debug("SARIMA%s x %s falló: %s", param, seasonal, e)
                continue

    if best_model is None:
        logger.warning(
            "sarima_auto_tune: todas las %d configuraciones fallaron. "
            "Devolviendo None — el llamador debe gestionar este caso.",
            failed,
        )

    return best_model
