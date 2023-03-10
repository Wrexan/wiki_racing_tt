import unittest

from wikiracing import WikiRacer


class WikiRacerTest(unittest.TestCase):
    racer = WikiRacer()

    def test_1(self):
        path = self.racer.find_path('Дружба', 'Рим')
        self.assertEqual(path, ['Дружба', 'Якопо Понтормо', 'Рим'])

    def test_2(self):
        path = self.racer.find_path('Мітохондріальна ДНК', 'Вітамін K')
        self.assertEqual(path, ['Мітохондріальна ДНК', 'Пластида', 'Дезоксирибонуклеїнова кислота',
                                'Аденозинтрифосфат', 'Вітамін K'])

    def test_3(self):
        path = self.racer.find_path('Марка (грошова одиниця)', 'Китайський календар')
        self.assertEqual(path, ['Марка (грошова одиниця)', '1924', 'Китайський календар'])

    def test_4(self):
        path = self.racer.find_path('Фестиваль', 'Пілястра')
        self.assertEqual(path, ['Фестиваль', 'Бароко', 'Пілястра'])

    def test_5(self):
        path = self.racer.find_path('Дружина (військо)', '6 жовтня')
        self.assertEqual(path, ['Дружина (військо)', 'Реєстрове козацтво', 'Крилаті гусари',
                                'Почет', 'Українська мала енциклопедія', 'Wayback Machine', '24 жовтня', '6 жовтня'])


if __name__ == '__main__':
    unittest.main()
