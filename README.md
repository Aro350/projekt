## Opis programu
Program służy do automatycznego pobierania załączników z wiadomości e-mail na podstawie listy użytkowników zawartej w pliku programu Excel.
Pozwala w prosty sposób określić zakres dat, wybrać grupę użytkowników, a następnie zapisać wszystkie ich załączniki w przypisanych katalogach.

Projekt został zaprojektowany jako skrypt konsolowy w Pythonie.

## Funkcjonalności
- Logowanie do skrzynki IMAP z użyciem podanego adresu i portu
- Możliwość zapisu i wczytania konfiguracji
- Wybór pliku Excel zawierającego listę użytkowników  
- Wybór zakresu czasu (np. „dzisiaj”, „od-do”, „od-do dzisiaj”)  
- Wyszukiwanie wiadomości od wskazanych użytkowników  
- Pobieranie wszystkich załączników z tych wiadomości  
- Automatyczne zapisywanie załączników do osobnych folderów  
- Zarządzanie błędami

## Wymagania
### System:
- Winows / Linux
- Python 3.10 lub nowszy  

### Biblioteki:
- pandas
- openpyxl

### Instalacja wymaganych bibliotek:
- pip install pandas openpyxl
