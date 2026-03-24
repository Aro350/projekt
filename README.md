## Opis programu
Program z interfejsem graficznym zaprojektowanym w Tkinterze służący do automatycznego pobierania załączników z wiadomości e-mail na podstawie listy użytkowników zawartej w pliku programu Excel.
Łączy się z pocztą przez protokoły IMAP lub POP3 i filtruje wiadomości na podstawie użytkowników, wybranych dat i tematów. Pobrane pliki są zapisywane w automatycznie tworzonych folderach na podstawie ustalonej przez użytkownika ścieżki, dodatkowo archiwa są automatycznie wypakowywane.

## Funkcjonalności
- Logowanie do skrzynki pocztowej wykorzystując POP3 i IMAP z użyciem podanego adresu i portu
- Możliwość zapisu i wczytania konfiguracji
- Wybór pliku Excel zawierającego listę użytkowników  
- Wybór zakresu czasu (np. „dzisiaj”, „od-do”, „od-do dzisiaj”)  
- Wyszukiwanie wiadomości od wskazanych użytkowników
- Filtrowanie wiadomości na podstawie tematu
- Pobieranie wszystkich załączników z tych wiadomości  
- Automatyczne zapisywanie załączników do odpowiednich folderów
- Automatyczne wypakowywanie archiwów
- Odnowienie połączenia z pocztą w przypadku jego utraty
- Zarządzanie błędami

## Wymagania
### System:
- Winows / Linux
- Python 3.10 lub nowszy  

### Biblioteki:
- pandas
- openpyxl
- tkcalendar
- patool
- cryptography

### Instalacja wymaganych bibliotek:
- pip install pandas openpyxl tkcalendar patool cryptography
- lub
- pip install -r ścieżka_do_pliku/requirements.txt
