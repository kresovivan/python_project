import requests
import pandas as pd
from deep_translator import GoogleTranslator
import time


class ProgrammingDictionaryTranslator:
    def __init__(self):
        self.english_terms = []
        self.translated_dict = {}

    def download_dictionary_from_github(self):
        """1. Скачивание словаря программиста с GitHub"""
        print("Скачивание словаря с GitHub...")

        raw_url = "https://raw.githubusercontent.com/ephraimduncan/awesome-developer-dictionary/master/README.md"

        try:
            response = requests.get(raw_url, timeout=10)
            if response.status_code == 200:
                content = response.text
                self._parse_github_content(content)
                print(f"Успешно загружено {len(self.english_terms)} терминов")
            else:
                print(f"Ошибка загрузки: {response.status_code}")
                return False

        except Exception as e:
            print(f"Ошибка: {e}")
            return False

        return True

    def _parse_github_content(self, content):
        """Парсинг содержимого GitHub README"""
        lines = content.split('\n')

        for line in lines:
            line = line.strip()

            if line.startswith('## ') and not line.startswith('## Table of Contents'):
                term = line.replace('## ', '').strip()
                if len(term) > 2 and '#' not in term:
                    self.english_terms.append(term)

            elif line.startswith('- **') and '**' in line:
                parts = line.split('**')
                if len(parts) >= 3:
                    term = parts[1].strip()
                    if len(term) > 2:
                        self.english_terms.append(term)

            elif line.startswith('**') and '**' in line[2:]:
                term_match = line.split('**')[1]
                if term_match and len(term_match) > 2 and ':' not in term_match:
                    self.english_terms.append(term_match)

        self.english_terms = list(set(self.english_terms))

    def translate_terms(self):
        """2. Перевод терминов с английского на русский"""
        print("Перевод терминов...")

        translator = GoogleTranslator(source='en', target='ru')
        successful_translations = 0

        for i, term in enumerate(self.english_terms):
            try:
                translation = translator.translate(term)
                self.translated_dict[term] = translation
                successful_translations += 1
                print(f"{i + 1}/{len(self.english_terms)}: {term} -> {translation}")

                time.sleep(0.5)

            except Exception as e:
                print(f"Ошибка перевода '{term}': {e}")
                self.translated_dict[term] = "перевод не доступен"

        print(f"Успешно переведено терминов: {successful_translations}/{len(self.english_terms)}")

    def save_to_excel(self, filename="programming_dictionary.xlsx"):
        """3. Сохранение словаря в Excel файл"""
        if not self.translated_dict:
            print("Нет данных для сохранения")
            return False

        data = []
        for english, russian in self.translated_dict.items():
            data.append({
                "English Term": english,
                "Russian Translation": russian
            })

        df = pd.DataFrame(data)

        try:
            df.to_excel(filename, index=False)
            print(f"Файл сохранен: {filename}")
            print(f"Сохранено терминов: {len(df)}")
            return True

        except Exception as e:
            print(f"Ошибка сохранения файла: {e}")
            try:
                csv_filename = filename.replace('.xlsx', '.csv')
                df.to_csv(csv_filename, index=False, encoding='utf-8')
                print(f"Файл сохранен как CSV: {csv_filename}")
                return True
            except Exception as e2:
                print(f"Ошибка сохранения CSV: {e2}")
                return False


def main():
    print("Запуск программы перевода словаря программиста")
    print("=" * 40)

    translator = ProgrammingDictionaryTranslator()

    if not translator.download_dictionary_from_github():
        return

    translator.translate_terms()
    translator.save_to_excel("awesome_developer_dictionary_ru.xlsx")

    print("Программа завершена!")


if __name__ == "__main__":
    main()