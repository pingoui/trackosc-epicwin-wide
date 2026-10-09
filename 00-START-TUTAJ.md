# TrackOSC EpicWin: 0,5× / 1× na iPhonie, przygotowanie z Windowsa

## Co dostajesz i co trzeba jeszcze zrobić

Pakiet zawiera zmodyfikowany moduł kamery, wybór fizycznego obiektywu 0,5× / 1×,
zapamiętywanie wyboru, ochronę przed autoblokadą i gotowy proces budowania w GitHub Actions.
Nie potrzebujesz własnego Maca ani płatnego konta Apple na pierwszy test.

**ZIP z tym pakietem nie jest jeszcze aplikacją IPA.** Najpierw uruchamiasz przygotowaną
kompilację na GitHubie, potem podpisujesz i instalujesz IPA lokalnie przez AltStore Classic.
Nie potwierdzono jeszcze kompilacji w Xcode ani działania tej modyfikacji na fizycznym
iPhonie. Zielony wynik Actions potwierdzi kompilację, a poniższe testy — sprzęt.

Aplikacja nazywa się **TrackOSC EpicWin**, ma inny identyfikator niż oryginał z App Store.
Oryginalny TrackOSC, nasza gra Windows i Camo pozostają bez zmian. Pierwsze uruchomienie:
tylna kamera 1×, tylko **2D Body**, ochrona przed usypianiem włączona.

## 1. Umieść WYŁĄCZNIE ten pakiet na GitHubie

Potrzebujesz konta GitHub. Nie publikuj całego repo EpicWin: zawiera Twoje materiały i logi.
Nasz skrypt kopiuje tylko wskazane pliki modułu TrackOSC do osobnego małego repozytorium.

Na tym komputerze Git i GitHub CLI są już dostępne. Otwórz PowerShell:

```powershell
cd C:\Users\mateu\Desktop\epicwin\tools\trackosc-wide
gh auth login
powershell -ExecutionPolicy Bypass -File .\Prepare-GitHub.ps1 -Publish
```

W logowaniu wybierz GitHub.com, HTTPS i logowanie przez przeglądarkę. Polecenie z `-Publish`
**utworzy PUBLICZNE repozytorium `trackosc-epicwin-wide` na Twoim koncie i wyśle pakiet**.
Nie wysyła gry ani danych konta Apple. Przy zajętej nazwie wybierz inną, np.
`-RepositoryName trackosc-epicwin-wide-test`.

Standardowy runner macOS użyty w pakiecie jest bezpłatny dla publicznego repozytorium według
[dokumentacji GitHub](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).
Nie wybieraj płatnych większych runnerów i nie dodawaj żadnych kluczy Apple do GitHub Secrets.

Alternatywa bez CLI: uruchom skrypt bez `-Publish`, potem w GitHub Desktop wybierz
**File → Add local repository**, wskaż utworzony folder `github-upload` i opublikuj go.
Ukryty katalog `.github` musi trafić do repozytorium — samo przeciągnięcie widocznych plików
w przeglądarce może go pominąć. Instrukcja naprawy przerwanej publikacji jest w README.md.

## 2. Zbuduj i pobierz IPA

1. Otwórz nowe repozytorium w przeglądarce.
2. Wejdź w **Actions → Build TrackOSC EpicWin IPA → Run workflow → Run workflow**.
3. Poczekaj na zakończenie. Pierwszy build pobiera zależności; nie obiecujemy konkretnego czasu.
4. Otwórz zakończone uruchomienie. Przy zielonym wyniku pobierz z sekcji **Artifacts** paczkę
   **TrackOSC-EpicWin-iPhone**.
5. Rozpakuj pobrany ZIP. W środku będzie **TrackOSC-EpicWin-unsigned.ipa**.

To build dla fizycznego iPhone'a, nie symulatora. Jest niepodpisany celowo: podpisywanie
wykonasz lokalnie swoim kontem Apple. Nie zainstalujesz IPA zwykłym dwuklikiem.
Plik `SHA256.txt` pozwala sprawdzić pobraną paczkę poleceniem
`Get-FileHash .\TrackOSC-EpicWin-unsigned.ipa -Algorithm SHA256`.

Gdy build jest czerwony: pobierz **TrackOSC-EpicWin-build-diagnostics** i przekaż
`xcodebuild.log`. Jeśli błąd wystąpił wcześniej, skopiuj komunikat z czerwonego kroku Actions.
Nie trzeba wtedy instalować Xcode na Windowsie ani kupować konta Apple.

## 3. Podpisz i zainstaluj aplikację z Windowsa

Używamy **AltStore Classic + AltServer**, NIE AltStore PAL. To zewnętrzne oprogramowanie;
instaluj je wyłącznie z oficjalnej strony i świadomie zdecyduj o użyciu konta Apple.
Nie przesyłaj nam hasła, kodów 2FA ani certyfikatów.

1. Przejdź przez [oficjalną instrukcję AltStore dla Windows](https://faq.altstore.io/altstore-classic/how-to-install-altstore-windows).
   Wymaga AltServer oraz odpowiednich wersji iTunes/iCloud. Jeżeli masz już Apple Devices
   lub inne sterowniki, najpierw sprawdź zgodność; nie odinstalowuj w ciemno działającego Camo.
2. Podłącz odblokowany iPhone przez USB, zaakceptuj zaufanie i zainstaluj AltStore przez AltServer.
   Konto Apple podajesz wyłącznie lokalnie w tym narzędziu, nie w GitHubie ani czacie.
3. W iPhonie zaakceptuj profil deweloperski i włącz **Tryb dewelopera**, zgodnie z instrukcją.
4. Przenieś własny plik IPA do aplikacji **Pliki** w iPhonie, np. przez iCloud Drive.
5. Przy działającym AltServer otwórz **AltStore → My Apps → +**, wskaż plik IPA i poczekaj
   na podpisanie oraz instalację. Telefon i komputer muszą mieć połączenie opisane przez AltStore.

Przy darmowym koncie aplikacje wygasają po **7 dniach**; odświeżaj je przez AltStore przy
dostępnym AltServer. Obowiązuje też limit aktywnych aplikacji instalowanych tą metodą.
To droga testowa, nie gotowy system utrzymania stanowiska eventowego.
[Zasady odświeżania AltStore](https://faq.altstore.io/altstore-classic/your-altstore)

## 4. Ustaw obiektyw i połącz z grą

1. Zamknij Camo Camera i oryginalny TrackOSC. Uruchom **TrackOSC EpicWin**.
2. Zezwól na kamerę i sieć lokalną. Na dole zobaczysz przełącznik **1x / 0.5x** dla tylnej kamery.
   Jest też w **Settings → Camera → Rear lens**. Przycisk zmiany przód/tył nadal działa;
   na przedniej kamerze wybór tylnego obiektywu jest niedostępny.
3. Wybierz **0.5x**. Sprawdź podpis aktywnej kamery: powinien zaczynać się od **Rear 0.5x**.
   Komunikat **0.5x unavailable - using rear 1x** oznacza rzeczywisty powrót do 1×,
   a nie działający ultraszeroki obiektyw. To fizyczny obiektyw, nie cyfrowe oddalenie obrazu.
4. **Settings → Camera → Keep screen awake** zostaw włączone. Działa, gdy aplikacja jest
   na pierwszym planie. Ręczna blokada, przełączenie aplikacji i połączenia telefoniczne
   mogą przerwać śledzenie — nie obiecujemy pracy w tle.
5. Ustaw telefon poziomo i zablokuj odpowiednią orientację. Zostaw włączone tylko **2D Body**.
6. W PowerShell uruchom istniejącą grę:

   ```powershell
   cd C:\Users\mateu\Desktop\epicwin
   powershell -ExecutionPolicy Bypass -File .\scripts\start-trackosc-demo.ps1
   ```

7. W telefonie **Settings → Destination** wpisz adres IPv4 wspólnej sieci wypisany przez
   launcher oraz port **9527**, potem **Apply**. Nie wpisuj 127.0.0.1 ani adresu VPN.
8. F2 w grze pokaże połączenie, wykryte osoby i aktualizacje/s. Nie otwieraj portu na routerze.

**Obiektyw zmieniaj PRZED kalibracją i rundą.** Nowy kadr wymaga ponownego ustawienia gracza;
przy porównaniu 1× / 0,5× wróć do przygotowania gracza albo ponownie uruchom grę.

## 5. Krótki test akceptacyjny

- Porównaj 1× i 0,5× bez przestawiania telefonu. Kadr na 0,5× musi być wyraźnie szerszy.
- Przełącz przód/tył, wróć na tył. Zapamiętany wybór 0,5× ma wrócić.
- Zamknij i otwórz aplikację: wybór obiektywu ma pozostać.
- Zostaw ją bez dotykania dłużej niż dotychczasowy czas autoblokady. Ekran ma nie zasnąć.
- Zagraj sam: menu, START, Runner, Squash, pauza, wyniki, powrót.
- Gdy będzie okazja: dwie osoby, ręce nad głową, skoki, role graczy i powrót po rundzie.
- Następnie próba 15–20 minut: obserwuj FPS, zgubienia sylwetek i nagrzewanie telefonu.
- Ręcznie zablokuj telefon: gra nie może być dalej sterowana zamrożoną pozą.

Zapisz ustawienie obiektywu, odległość, liczbę osób i odczyty/s z F2. 0,5× daje szerszy kadr,
ale sylwetki mają mniej pikseli; szybkość i dokładność, zwłaszcza dla 2–4 osób, wymagają pomiaru.
Logi gry są w `docs/playtests-trackosc/`. Nie ma jeszcze gwarancji obsługi czterech graczy.

## Powrót do poprzedniego rozwiązania

Zamknij modyfikację i uruchom oryginalny TrackOSC z App Store — ten sam launcher gry.
Możesz też wrócić do Camo przez `scripts/start-camera-demo.ps1 -Diagnostics`.
Nie uruchamiaj dwóch nadajników OSC jednocześnie.

Źródło: [TrackOSC](https://github.com/JGL/TrackOSC), MIT, Joel Gethin Lewis.
Zmiany EpicWin są nieoficjalne i nie zostały wydane przez autora TrackOSC.
