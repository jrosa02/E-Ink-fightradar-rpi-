import random
from typing import Iterable, Iterator


kapitan_bomba_cytaty = [
    "Tępy chuju, masz mnie za idiotę? Wylądujemy w nocy!",
    "Średnia hawajska dla każdego!",
    "Moja dupa jest ciasna jak po praniu, a twoja matka to chuj.",
    "Nie ważne co mam w sercu, ważne co mam w dupie.",
    "Umysł robota walczy z umysłem debila.",
    "Zrobię ci z dupy kropkę nad i!",
    "Pachną nigdy niemyty siusiakiem, tak jak chorąży Torpeda.",
    "Może i robimy chujowo, ale kto robi dobrze?",
    "Domino - leć po kieliszki, Grzegorz - smaruj stoły gównem!",
    "Ryby w Morskim Oku zdechły. A w Czarnym Stawie... zdechły.",
    "Jeżeli chodzi o dziewczynki, to można powiedzieć, że jestem jaroszem.",
    "Panie kapitanie, a co by pan zrobił, gdyby się pan dowiedział, \nże pana siostra opierdala kiełbachy kosmitom?",
    "Donna mamma es chujoczita",
    "Matka była mi jak brat, a jak zabijesz brata to jakbyś zabił matkę",
]


class TextsSelector(Iterable):
    def __init__(self, ifrandom: bool) -> None:
        self.ifrandom: bool = ifrandom
        self.texts: list[str] = kapitan_bomba_cytaty

    def __iter__(self) -> Iterator:
        if self.ifrandom:
            return self
        else:
            return iter(self.texts)

    def __next__(self):
        return random.choice(self.texts)
