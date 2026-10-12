import requests


def tiempo_barcelona():
    url = (
        "https://api.open-meteo.com/v1/forecast"
        "?latitude=41.38&longitude=2.17"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max"
        "&timezone=Europe/Madrid&forecast_days=1"
    )
    d = requests.get(url, timeout=10).json()["daily"]
    tmax = d["temperature_2m_max"][0]
    tmin = d["temperature_2m_min"][0]
    lluvia = d["precipitation_probability_max"][0]

    texto = f"Hoy: {tmin}°C / {tmax}°C, probabilidad de lluvia {lluvia}%."
    if lluvia >= 50:
        texto += "\nCoge paraguas."
    return texto