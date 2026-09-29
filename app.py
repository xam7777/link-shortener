from flask import Flask, request, redirect, render_template_string  # Bibliothek für Webserver, Formulardaten, Weiterleitung und HTML-Seiten
import sqlite3  # In Python eingebaute Mini-Datenbank
import string  # Für die erlaubten Zeichen im Kurz-Code
import random  # Für die zufällige Auswahl der Zeichen

app = Flask(__name__)  # Erstellt die Webserver-Anwendung

# HTML für die Startseite mit Formular, als Text direkt im Code (einfacher Einstieg ohne separate Dateien)
STARTSEITE_HTML = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Link-Verkürzer</title>
    <style>
        body { font-family: Arial, sans-serif; background: #1e1e2f; color: white; display: flex; justify-content: center; padding-top: 80px; }
        .box { background: #2a2a3d; padding: 30px; border-radius: 12px; width: 420px; }
        h1 { font-size: 22px; }
        input[type=text] { width: 100%; padding: 10px; margin-top: 10px; border-radius: 6px; border: none; box-sizing: border-box; }
        button { margin-top: 12px; padding: 10px 20px; background: #6c5ce7; color: white; border: none; border-radius: 6px; cursor: pointer; }
        button:hover { background: #5a4bd6; }
        .ergebnis { margin-top: 20px; padding: 15px; background: #33334a; border-radius: 8px; word-break: break-all; }
        a { color: #a29bfe; }
    </style>
</head>
<body>
    <div class="box">
        <h1>🔗 Link-Verkürzer</h1>
        <form method="POST" action="/">
            <input type="text" name="url" placeholder="https://deine-lange-url.de/..." required>
            <button type="submit">Verkürzen</button>
        </form>

        {% if kurzer_link %}
        <div class="ergebnis">
            Dein kurzer Link: <a href="{{ kurzer_link }}">{{ kurzer_link }}</a><br>
            Statistik: <a href="/stats/{{ code }}">/stats/{{ code }}</a>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

# HTML für die Statistik-Seite eines einzelnen Links
STATS_HTML = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Statistik</title>
    <style>
        body { font-family: Arial, sans-serif; background: #1e1e2f; color: white; display: flex; justify-content: center; padding-top: 80px; }
        .box { background: #2a2a3d; padding: 30px; border-radius: 12px; width: 420px; }
        a { color: #a29bfe; }
    </style>
</head>
<body>
    <div class="box">
        <h1>📊 Statistik</h1>
        <p>Ziel-URL: {{ ziel_url }}</p>
        <p>Klicks bisher: <strong>{{ klicks }}</strong></p>
        <p><a href="/">Zurück zur Startseite</a></p>
    </div>
</body>
</html>
"""


def erstelle_datenbank():
    """Legt die Datenbank-Datei und die Tabelle an, falls sie noch nicht existieren."""
    verbindung = sqlite3.connect("links.db")  # Verbindet sich mit der Datei 'links.db'
    cursor = verbindung.cursor()  # Werkzeug, um Befehle an die Datenbank zu schicken
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS links (
            code TEXT PRIMARY KEY,
            ziel_url TEXT NOT NULL,
            klicks INTEGER DEFAULT 0
        )
    """)  # Erstellt die Tabelle, falls sie noch nicht existiert
    verbindung.commit()  # Speichert die Änderung dauerhaft
    verbindung.close()  # Schließt die Verbindung


def erzeuge_kurz_code(laenge=6):
    """Erzeugt einen zufälligen Code aus Buchstaben und Zahlen, z.B. 'xk9a2b'."""
    zeichen = string.ascii_lowercase + string.digits  # Erlaubte Zeichen: a-z und 0-9
    return "".join(random.choice(zeichen) for _ in range(laenge))  # Wählt 6 zufällige Zeichen aus


def speichere_neuen_link(ziel_url):
    """Erzeugt einen eindeutigen Kurz-Code und speichert ihn zusammen mit der Ziel-URL."""
    verbindung = sqlite3.connect("links.db")  # Verbindet sich mit der Datenbank
    cursor = verbindung.cursor()  # Werkzeug für Datenbank-Befehle

    while True:  # Wiederholt sich, falls der zufällige Code schon existiert
        code = erzeuge_kurz_code()  # Erzeugt einen neuen zufälligen Code
        cursor.execute("SELECT code FROM links WHERE code = ?", (code,))  # Prüft, ob der Code schon vergeben ist
        if cursor.fetchone() is None:  # Kein Eintrag gefunden = Code ist frei
            break  # Schleife verlassen

    cursor.execute(
        "INSERT INTO links (code, ziel_url) VALUES (?, ?)", (code, ziel_url)
    )  # Fügt den neuen Kurz-Code mit Ziel-URL ein
    verbindung.commit()  # Speichert dauerhaft
    verbindung.close()  # Schließt die Verbindung

    return code  # Gibt den neuen Code zurück


def hole_link(code):
    """Sucht die Ziel-URL und Klickzahl zu einem gegebenen Kurz-Code."""
    verbindung = sqlite3.connect("links.db")  # Verbindet sich mit der Datenbank
    cursor = verbindung.cursor()  # Werkzeug für Datenbank-Befehle
    cursor.execute("SELECT ziel_url, klicks FROM links WHERE code = ?", (code,))  # Sucht den Eintrag zum Code
    ergebnis = cursor.fetchone()  # Holt das Ergebnis (oder None, falls nicht gefunden)
    verbindung.close()  # Schließt die Verbindung
    return ergebnis  # Gibt (ziel_url, klicks) oder None zurück


def zaehle_klick_hoch(code):
    """Erhöht den Klick-Zähler für einen Code um 1."""
    verbindung = sqlite3.connect("links.db")  # Verbindet sich mit der Datenbank
    cursor = verbindung.cursor()  # Werkzeug für Datenbank-Befehle
    cursor.execute("UPDATE links SET klicks = klicks + 1 WHERE code = ?", (code,))  # Erhöht den Zähler um 1
    verbindung.commit()  # Speichert dauerhaft
    verbindung.close()  # Schließt die Verbindung


def bereinige_url(url):
    """Stellt sicher, dass die URL mit http:// oder https:// beginnt."""
    url = url.strip()  # Entfernt Leerzeichen am Anfang/Ende
    if not url.startswith("http://") and not url.startswith("https://"):  # Prüft, ob ein Protokoll fehlt
        url = "https://" + url  # Ergänzt https:// als Standard, falls es fehlt
    return url  # Gibt die bereinigte URL zurück


@app.route("/", methods=["GET", "POST"])
def startseite():
    """Zeigt das Formular an und verarbeitet neue eingegebene Links."""
    kurzer_link = None  # Anfangswert: noch kein Ergebnis anzuzeigen
    code = None  # Anfangswert: noch kein Code vorhanden

    if request.method == "POST":  # Nur wenn das Formular abgeschickt wurde
        ziel_url = request.form.get("url")  # Holt die eingegebene URL aus dem Formular
        if ziel_url:  # Nur weitermachen, wenn wirklich etwas eingegeben wurde
            ziel_url = bereinige_url(ziel_url)  # Stellt sicher, dass https:// davor steht
            code = speichere_neuen_link(ziel_url)  # Erzeugt und speichert den neuen Kurz-Code
            kurzer_link = request.host_url + code  # Baut den vollständigen kurzen Link zusammen (z.B. http://127.0.0.1:5000/xk9a2b)

    return render_template_string(STARTSEITE_HTML, kurzer_link=kurzer_link, code=code)  # Zeigt die Seite mit (oder ohne) Ergebnis an


@app.route("/stats/<code>")
def statistik(code):
    """Zeigt die Statistik zu einem einzelnen Kurz-Code an."""
    ergebnis = hole_link(code)  # Sucht die Daten zu diesem Code
    if ergebnis is None:  # Falls der Code nicht existiert
        return "Diesen Link gibt es nicht.", 404  # Zeigt eine einfache Fehlermeldung mit Status-Code 404

    ziel_url, klicks = ergebnis  # Trennt das Ergebnis in die zwei Werte auf
    return render_template_string(STATS_HTML, ziel_url=ziel_url, klicks=klicks)  # Zeigt die Statistik-Seite an


@app.route("/<code>")
def weiterleitung(code):
    """Leitet einen Kurz-Code zur echten, langen URL weiter und zählt den Klick."""
    ergebnis = hole_link(code)  # Sucht die Daten zu diesem Code
    if ergebnis is None:  # Falls der Code nicht existiert
        return "Dieser Link existiert nicht oder ist abgelaufen.", 404  # Fehlermeldung mit Status-Code 404

    ziel_url, klicks = ergebnis  # Trennt das Ergebnis auf
    zaehle_klick_hoch(code)  # Erhöht den Klick-Zähler für diesen Link um 1
    return redirect(ziel_url)  # Leitet den Browser zur echten, langen URL weiter
erstelle_datenbank()  # Stellt sicher, dass die Datenbank existiert, sobald das Programm startet

if __name__ == "__main__":
       app.run(debug=True)