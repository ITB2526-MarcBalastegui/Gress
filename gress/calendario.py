import os
import datetime
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Permiso solo para ver y crear eventos, no para tocar la configuración del calendario
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
TZ = "Europe/Madrid"
MADRID = ZoneInfo(TZ)


def get_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as f:
            f.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def proximos_eventos(n=5):
    ahora = datetime.datetime.now(datetime.timezone.utc).isoformat()
    resultado = get_service().events().list(
        calendarId="primary", timeMin=ahora, maxResults=n,
        singleEvents=True, orderBy="startTime",
    ).execute()
    return resultado.get("items", [])


def eventos_entre(desde, hasta):
    resultado = get_service().events().list(
        calendarId="primary", timeMin=desde.isoformat(), timeMax=hasta.isoformat(),
        singleEvents=True, orderBy="startTime",
    ).execute()
    return resultado.get("items", [])


def eventos_de_hoy():
    ahora = datetime.datetime.now(MADRID)
    inicio = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
    return eventos_entre(inicio, inicio + datetime.timedelta(days=1))


def crear_evento(titulo, inicio, con_hora):
    if con_hora:
        fin = inicio + datetime.timedelta(hours=1)
        cuerpo = {
            "summary": titulo,
            "start": {"dateTime": inicio.isoformat(), "timeZone": TZ},
            "end": {"dateTime": fin.isoformat(), "timeZone": TZ},
        }
    else:
        dia = inicio.date()
        cuerpo = {
            "summary": titulo,
            "start": {"date": dia.isoformat()},
            "end": {"date": (dia + datetime.timedelta(days=1)).isoformat()},
        }
    return get_service().events().insert(calendarId="primary", body=cuerpo).execute()


if __name__ == "__main__":
    for e in proximos_eventos():
        inicio = e["start"].get("dateTime", e["start"].get("date"))
        print(inicio, e.get("summary", "(sin título)"))