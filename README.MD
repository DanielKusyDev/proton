# Proton Protocol

## Opis protokołu


Proton jest protokołem tekstowym, umożliwiającym komunikację pomiędzy serwerem a klientami za pomocą formatu **JSON**.
Każdy JSON jest konwertowany do postaci tekstowej (typ string), a na jego końcu jest dodawany znak końca linii **\r\n**.

Protokół ten działa w oparciu o szyfrowane gniazda TCP. Każdy klient musi sprawdzać klucz serwera.

***

#### Odbiór / wysyłanie wiadomości
Wszystkie wiadomość wysyłane przez klienta mają następujący format tekstowy:

`"{ "action": "{action}", "params": {params}}\r\n"`

gdzie:

`{Action}` - jedna z akcji (wyjaśnionych szczegółowo niżej): login, register, logout, get, create, alter, delete.

`{Params}` - obiekt z danymi wymaganymi do zapytania. Opcjonalne.


Wszystkie wiadomości wysyłane przez serwer mają następujący format tekstowy:

`"{"status": "{status}","message": "{message}", "data": {data}}\r\n"`

gdzie:

`{status}` - informacja o powodzeniu akcji lub jego braku. Jedno z wartości
- OK - polecenie wykonane prawidłowo,
- WRONG - polecenie wykonane, ale nie znaleziono danych potrzebnych w zapytaniu
- ERROR - błąd wykonania polecenia.

`{message}` - Opcjonalne. Wiadomość z opisem wykonania akcji.
`{data}` - Opcjonalne. Tablica z danymi będącymi wynikiem akcji.

Proces odbioru wiadomości polega na nasłuchiwaniu gniazda, dopóki wiadomość nie będzie zakończona znakiem końca linii **\r\n**.

***

### Akcje

##### Register
Umożliwia zarejestrowanie użytkownika

Przykładowy request:
`{action: "register", params: {username: "Test1234", password: "Test1234"}}\r\n`

Przykładowy response:
`{"data": [{"id": 6, "username": "Test1234"}], "message": "", "status": "OK"}\r\n`

##### Login
Uwierzytelnienie użytkownika, umożliwia dostęp do pozostałych akcji w komunikacji.

Przykładowy request:
`{action: "login", params: {username: "Qwerty", password: "Qwerty"}}\r\n`

Przykładowy response:
`{"data": [{"user_id": 5}], "message": "", "status": "OK"}\r\n`

##### Logout

Opis umożliwia bezpieczne wylogowanie użytkownika, zakończenie sesji oraz zamknięcie połączenia klienta.

Przykładowy request:
`{"action":"logout"}`

Przykładowy response:
`{"message": "Logged out.", "status": "OK"}`

##### Get
Pobranie listy postów bloga. Z opcjonalnym parametrem id, umożliwia pobranie pojedynczego posta.

Przykładowy request:
`{"action":"get"}\r\n`

Przykładowy response:
`{"data": [ { "id": 1, "image": "base64…","content": "Lorem ipsum dolor sit amet...","title": "Lorem ipsum dolor sit amet...","user_id": 1} ], "message": "","status": "OK" }\r\n`

gdzie *image* to zdjęcie zapisane w formacie base64.

##### Create
Tworzy nowy post.

Przykładowy request:
`{"action": "create", "params": {"image": "base64…", "content": "Lorem ipsum dolor sit amet...", "title": "Lorem ipsum dolor sit amet..."}}\r\n`


Przykładowy response:
`{"data": [{"content": ""Lorem ipsum dolor sit amet..", "id": 14, "image": "base64", "title": ""Lorem ipsum dolor sit amet..", "user_id": 5}], "message": "Post created successfully.", "status": "OK"}\r\n`

##### Alter
Zmienia parametry posta.

Przykładowy request:
`{"action": "alter", "params": {id: 14, "image": "base64…", "content": "Lorem ipsum dolor sit amet...", "title": "Lorem ipsum dolor sit amet..."}}\r\n`

Przykładowy response:
`{"data": [{"content": "Gghggff", "id": 14, "image": base64", "title": "Hbvggv", "user_id": 5}], "message": "", "status": "OK"}\r\n`

##### Delete
Usuwa post.

Przykładowy request:
`{"action": "delete", "params": {"id": 14}}\r\n`

Przykładowy response:
`{"data": {"id": 14}, "status": "OK"}\r\n`

Repozytorium zawiera implementację serwera obsługującego protokół. Klient w postaci aplikacji mobilnej dostępny pod adresem
https://github.com/lukaszkurantdev/proton-blog-app 

Ogólny sposób funkcjonowania serwera:
![alt text](https://www.planttext.com/api/plantuml/img/VL913i8m3Bll5Ja24X_O0I7W1S1z2fq54wKTRSRxAQnZxK2SkiPE7BjRUs4dtKqNHHi-6jMqR8Iske6Hh7I0Uy3zO1ql3bndm1xt3ZxltreZpcezcR67RwtnA6eMFh47xJO5AsaUB1X4Uo5QhcAX91SL-dkAd26LX-eSAc_L5JARZwnLjZCj5bJIEu50-eXcjZ9-a8dMGkiND3hi1wi02FxHIhgmgJMgQ6SMptIPCRQaCOpPRUXjbgmZrXAAhmGdf27TVA64ifmayafsU13yMYAjfZcbG7orDKmT_gmd "Request flow")
