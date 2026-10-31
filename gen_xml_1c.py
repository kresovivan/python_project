# -*- coding: utf-8 -*-
"""
Генератор тестового ConfigDumpInfo.xml (~5000 записей <Metadata>)
с поддержкой префикса ПЛ_ (как в реальных конфигурациях 1С).
Сохранить как gen_test_xml.py и запустить: python gen_test_xml.py
"""
import random
import uuid

random.seed(42)  # воспроизводимость

OUTPUT = 'ConfigDumpInfo.xml'
TARGET_COUNT = 5000

# ============================================================================
# СПРАВОЧНИКИ ИМЁН
# ============================================================================
OBJECT_TYPES = [
    'Catalog', 'Document', 'Enum', 'InformationRegister',
    'AccumulationRegister', 'AccountingRegister', 'CalculationRegister',
    'BusinessProcess', 'Task', 'DataProcessor', 'Report',
    'ChartOfAccounts', 'ChartOfCharacteristicTypes',
    'ChartOfCalculationTypes', 'ExchangePlan', 'Constant',
    'CommonModule', 'CommonForm', 'CommonCommand', 'CommonTemplate',
    'CommonPicture', 'CommonAttribute', 'SessionParameter',
    'DefinedType', 'Role', 'Subsystem', 'ScheduledJob',
    'FunctionalOption', 'FunctionalOptionsParameter',
    'EventSubscription', 'HTTPService', 'WebService',
    'IntegrationService', 'XDTOPackage', 'ExternalDataSource', 'Bot',
]

# Префиксы: пустой и ПЛ_ (можно добавить свои)
PREFIXES = ['', 'ПЛ_']

# Русские имена объектов БЕЗ префикса — префикс добавим отдельно
OBJECT_NAMES_BASE = [
    # Справочники
    'ФизическиеЛица', 'Организации', 'Контрагенты', 'Номенклатура',
    'Склады', 'Банки', 'Валюты', 'ЕдиницыИзмерения', 'Договоры',
    'Сотрудники', 'Должности', 'Подразделения', 'Пользователи',
    'Локации', 'Помещения', 'Оборудование', 'Материалы',
    'ТипыЛокаций', 'СтатусыОбъектов', 'КатегорииОбъектов',
    # Документы
    'РеализацияТоваровУслуг', 'ПоступлениеТоваровУслуг',
    'СчетФактураВыданный', 'СчетФактураПолученный',
    'ПлатежноеПоручение', 'ПриходныйКассовыйОрдер',
    'РасходныйКассовыйОрдер', 'АвансовыйОтчет',
    'ИнвентаризацияТоваров', 'ПеремещениеТоваров',
    'СписаниеТоваров', 'ОприходованиеТоваров',
    'ЗаказПоставщику', 'ЗаказПокупателя',
    'КорректировкаПоступления', 'КорректировкаРеализации',
    'НачислениеЗарплаты', 'ВыплатаЗарплаты', 'Отпуск',
    'БольничныйЛист', 'Командировка', 'Премия',
    'ДокументыПредприятия', 'КонтурГИСФизЛица',
    # Регистры
    'КурсыВалют', 'ЦеныНоменклатуры', 'КоличествоЗадачПоАвторам',
    'КоличествоЗадачПоИсполнителям', 'КоличествоКонтролей',
    'РабочееВремяСотрудников', 'КоличествоМоихДокументов',
    # Прочее
    'ОсновныеСредства', 'НематериальныеАктивы',
    'СтатьиЗатрат', 'НоменклатурныеГруппы',
    'СерииНоменклатуры', 'ХарактеристикиНоменклатуры',
    'ЗначенияСвойствОбъектов', 'НастройкиПравПользователей',
    'Календари', 'ГрафикиРаботы', 'Задачи', 'Контроли',
]

ATTRIBUTE_NAMES = [
    'Наименование', 'ПолноеНаименование', 'Код', 'Артикул', 'ИНН',
    'КПП', 'ОГРН', 'Адрес', 'Телефон', 'Email', 'ДатаРождения',
    'ПаспортСерия', 'ПаспортНомер', 'СНИЛС', 'Должность', 'Оклад',
    'Ставка', 'Количество', 'Сумма', 'Цена', 'Валюта', 'Единица',
    'Склад', 'Организация', 'Контрагент', 'Договор', 'Статус',
    'Комментарий', 'Автор', 'ДатаСоздания', 'ДатаИзменения',
    'Ответственный', 'ПометкаУдаления', 'Проведен', 'Номер',
    'Дата', 'Ссылка', 'Родитель', 'ЭтоГруппа', 'КодБыстрогоПоиска',
    'ОсновнойБанковскийСчет', 'ВидЦены', 'ПроцентСкидки',
    # Атрибуты из ваших скриншотов
    'Проект', 'МощностьВыбросов', 'СрокОбновления', 'План',
    'ВидЗадачи', 'ТипПриложения', 'ТипПроекта', 'Направление',
    'ДатаНачала', 'ДатаОкончания', 'ФИО', 'ФИОСотрудника',
    'ПолноеФИО', 'Фиолетовый', 'ФИОСотрудникаПолное',
]

TABULAR_SECTIONS = [
    'Товары', 'Услуги', 'Контакты', 'Сотрудники', 'Реквизиты',
    'ДополнительныеРеквизиты', 'Стороны', 'Документы', 'Работы',
    'Материалы', 'Ингредиенты', 'Корреспонденты', 'Параметры',
    'Строки', 'Спецификации', 'Комплектующие', 'Приложения',
]

DIMENSIONS = ['Организация', 'Контрагент', 'Номенклатура', 'Склад',
              'Валюта', 'Пользователь', 'Договор', 'Проект',
              'Автор', 'Исполнитель', 'Задача', 'Ответственный']

RESOURCES = ['Количество', 'Сумма', 'Время', 'Стоимость', 'Ставка',
             'Мощность', 'Срок', 'Курс', 'План', 'Прогресс']

FORMS = ['ФормаЭлемента', 'ФормаСписка', 'ФормаВыбора',
         'ФормаЗаписи', 'ФормаГруппы', 'ФормаКарточки']

MODULES = ['ObjectModule', 'ManagerModule', 'RecordSetModule',
           'FormModule', 'CommandModule', 'ValueManagerModule']

COMMANDS = ['Открыть', 'Создать', 'Печать', 'Экспорт', 'Импорт',
            'СоздатьОбразецНаОсновании', 'СформироватьДокумент']

ENUM_VALUES = ['НеЗадан', 'ВПроцессе', 'Завершен', 'Отменен',
               'Черновик', 'Проведен', 'Удален', 'ВРаботе',
               'Приостановлен', 'Согласование']

# ============================================================================
# УТИЛИТЫ
# ============================================================================
def gen_guid():
    return str(uuid.uuid4())


def esc(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;')
             .replace('>', '&gt;').replace('"', '&quot;'))


class Writer:
    """Обёртка над файлом с автоматическим подсчётом записей."""
    def __init__(self, path):
        self.f = open(path, 'w', encoding='utf-8')
        self.count = 0
        self.limit = TARGET_COUNT

    def write_metadata(self, name, config_version=None):
        """Возвращает False, если лимит достигнут."""
        if self.count >= self.limit:
            return False
        guid = gen_guid()
        cv = config_version or gen_guid()
        self.f.write(
            f'\t\t<Metadata name="{esc(name)}" '
            f'id="{guid}" configVersion="{cv}"/>\n'
        )
        self.count += 1
        return True

    def close(self):
        self.f.close()


# ============================================================================
# ГЕНЕРАЦИЯ
# ============================================================================
def main():
    w = Writer(OUTPUT)

    # --- Заголовок ---
    w.f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    w.f.write(
        '<ConfigDumpInfo '
        'xmlns="http://v8.1c.ru/8.3/xcf/dumpinfo" '
        'xmlns:xen="http://v8.1c.ru/8.3/xcf/enums" '
        'xmlns:xs="http://www.w3.org/2001/XMLSchema" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'format="Hierarchical" version="2.20">\n'
    )
    w.f.write('\t<ConfigVersions/>\n')

    obj_idx = 0
    while w.count < TARGET_COUNT:
        obj_type = OBJECT_TYPES[obj_idx % len(OBJECT_TYPES)]
        base_name_no_prefix = OBJECT_NAMES_BASE[
            (obj_idx * 7) % len(OBJECT_NAMES_BASE)]
        prefix = random.choice(PREFIXES)
        obj_name = f'{prefix}{base_name_no_prefix}'
        obj_idx += 1

        full = f'{obj_type}.{obj_name}'

        # 1) Сам объект
        if not w.write_metadata(full):
            break

        # 2) Реквизиты (3-8)
        n_attrs = random.randint(3, 8)
        for attr in random.sample(
                ATTRIBUTE_NAMES,
                min(n_attrs, len(ATTRIBUTE_NAMES))):
            if not w.write_metadata(f'{full}.Attribute.{attr}'):
                break
        if w.count >= TARGET_COUNT:
            break

        # 3) Табличные части (1-3) с реквизитами
        n_ts = random.randint(1, 3)
        for ts in random.sample(
                TABULAR_SECTIONS, min(n_ts, len(TABULAR_SECTIONS))):
            if not w.write_metadata(
                    f'{full}.TabularSection.{ts}'):
                break
            for attr in random.sample(
                    ATTRIBUTE_NAMES, random.randint(2, 5)):
                if not w.write_metadata(
                        f'{full}.TabularSection.{ts}'
                        f'.Attribute.{attr}'):
                    break
            if w.count >= TARGET_COUNT:
                break
        if w.count >= TARGET_COUNT:
            break

        # 4) Формы (1-2)
        for form in random.sample(FORMS, random.randint(1, 2)):
            if not w.write_metadata(f'{full}.Form.{form}'):
                break

        # 5) Команды (0-2)
        for cmd in random.sample(COMMANDS, random.randint(0, 2)):
            if not w.write_metadata(f'{full}.Command.{cmd}'):
                break

        # 6) Модули (1-2)
        for mod in random.sample(MODULES, random.randint(1, 2)):
            if not w.write_metadata(f'{full}.{mod}'):
                break

        # 7) Для регистров — измерения и ресурсы
        if 'Register' in obj_type:
            for dim in random.sample(DIMENSIONS,
                                     random.randint(1, 4)):
                if not w.write_metadata(
                        f'{full}.Dimension.{dim}'):
                    break
            for res in random.sample(RESOURCES,
                                     random.randint(1, 3)):
                if not w.write_metadata(
                        f'{full}.Resource.{res}'):
                    break

        # 8) Для перечислений — значения
        if obj_type == 'Enum':
            for val in random.sample(ENUM_VALUES,
                                     random.randint(2, 5)):
                if not w.write_metadata(
                        f'{full}.EnumValue.{val}'):
                    break

    # --- Закрытие ---
    w.f.write('\t</ConfigDumpInfo>\n')
    total = w.count
    w.close()

    print(f'Готово: {OUTPUT}')
    print(f'Записей <Metadata>: {total}')


if __name__ == '__main__':
    main()