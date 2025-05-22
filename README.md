DJCRM to aplikacja webowa stworzona w Django, której celem jest wspieranie zarządzania relacjami z klientami. Umożliwia ona przechowywanie danych o klientach, zarządzanie zamówieniami i produktami, a także wysyłanie powiadomień e-mailowych.
Projekt został stworzony na potrzeby pracy inżynierskiej jako praktyczne zastosowanie nowoczesnych technologii webowych do budowy systemów CRM dla małych i średnich firm.


Instrukcja konfiguracji przed uruchomieniem aplikacji:
1. Konfiguracja bazy danych

Aplikacja domyślnie korzysta z bazy danych PostgreSQL. Przed uruchomieniem upewnij się, że baza danych została poprawnie skonfigurowana.
W pliku settings.py znajdź sekcję DATABASES i zaktualizuj dane dostępowe:
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "your_db_name",
        "USER": "your_db_user",
        "PASSWORD": "your_db_password",
        "HOST": "your_db_host",
        "PORT": "your_db_port",
    }
}
Jeśli korzystasz z lokalnej instalacji PostgreSQL, typowe wartości to:
NAME: Nazwa bazy danych
USER: Użytkownik PostgreSQL
PASSWORD: Hasło użytkownika
HOST: localhost
PORT: 5432

2. Konfiguracja SMTP
Aplikacja wymaga skonfigurowania serwera SMTP do wysyłania powiadomień e-mailowych. W pliku settings.py znajdź sekcję dotyczącą konfiguracji e-maili i wprowadź swoje dane:
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "your_email@example.com"
EMAIL_HOST_PASSWORD = "your_email_password"

Powyższa konfiguracja dotyczy podłączenia e-mail w serwisie gmail. Aby skorzystać z innej domeny należy znaleźć domyślną nazwę EMAIL_HOST oraz EMAIL_PORT dla serwisu.
Przykładowa lista dostępna pod tym linkiem: https://domar.com/pages/smtp_pop3_server

UWAGA: niektóre serwisy mailowe (np. gmail) wymagają wygenerowania hasła aplikacji w ustawieniach bezpieczeństwa konta Google.
Przed dodaniem maila do ustawień aplikacji należy to zweryfikować.


Wymagania środowiskowe
Aby uruchomić aplikację, upewnij się, że Twój system spełnia następujące wymagania:
1. Python 3.8 lub nowszy, zalecany Python 3.12
Jeśli Python nie jest zainstalowany, pobierz go z python.org.
2. Pip (Python Package Installer)


Uruchomienie aplikacji:
1. Przejdź do katalogu projektu: 
cd ścieżka/do/projektu
2. (opcjonalne ale wysoce zalecane) Aktywuj środowisko:

Komenda dla Windows:
env\Scripts\activate

Na Linux/Mac:
source env/bin/activate

Po aktywowaniu środowiska, w terminalu zobaczysz nazwę środowiska (env), co oznacza, że wszystkie polecenia Python i pip będą teraz odnosiły się do tego środowiska.

3.Zainstaluj wymagane zależności.
pip install -r requirements.txt

4. Wykonaj migracje bazy danych:
python manage.py makemigrations
python manage.py migrate

5. Utworz konto administratorskie:
python manage.py createsuperuser

6. Uruchom serwer deweloperski:
python manage.py runserver
