"""Потоковый парсер ConfigDumpInfo.xml."""

import xml.etree.ElementTree as ET
from typing import Callable, Dict, List, Optional, Tuple

from ..constants import (
    BASE_COLUMNS,
    CUSTOM_TAG,
    KIND_TRANSLATIONS,
    NONE_TAG,
    STD_TAG,
    TYPE_TRANSLATIONS,
)
from .row import MetadataRow


class XmlParser:
    """Читает ConfigDumpInfo.xml потоково, без загрузки всего в память.

    Прогон состоит из двух проходов: подсчёт Metadata (для прогресса),
    затем собственно парсинг. На каждом проходе iterparse очищает
    отработанные элементы, поэтому память не растёт.
    """

    def __init__(
        self,
        path: str,
        on_count: Optional[Callable[[int], None]] = None,
        on_progress: Optional[Callable[[int, int], None]] = None,
    ) -> None:
        """on_count(n) - вызывается редко, по мере подсчёта;
        on_progress(done, total) - вызывается при парсинге."""
        self.path = path
        self.on_count = on_count
        self.on_progress = on_progress
        self._ns_uri = ''
        self._total = 0
        self._tag_metadata = 'Metadata'

    # --- публичный интерфейс ---

    def run(self, markers) -> Tuple[List[MetadataRow], List[str]]:
        """Полный цикл: обнаружение ns, подсчёт, парсинг.

        Возвращает (строки, список колонок). `markers` - любой объект
        с методом is_custom_name(name) -> bool.
        """
        self._detect_namespace()
        self._count()
        return self._parse(markers)

    # --- этапы ---

    def _detect_namespace(self) -> None:
        """Определяет URI пространства имён XML (если есть)."""
        ns = ''
        try:
            for _, elem in ET.iterparse(self.path, events=('start',)):
                t = elem.tag
                if t.startswith('{'):
                    ns = t[1:t.index('}')]
                break
        except Exception:
            ns = ''
        self._ns_uri = ns
        self._tag_metadata = f'{{{ns}}}Metadata' if ns else 'Metadata'

    def _count(self) -> None:
        """Считает общее число элементов Metadata."""
        total = 0
        with open(self.path, 'rb') as fh:
            for _, elem in ET.iterparse(fh, events=('end',)):
                if elem.tag == self._tag_metadata:
                    total += 1
                    elem.clear()
                    if self.on_count and total % 100_000 == 0:
                        self.on_count(total)
        self._total = total

    def _parse(self, markers) -> Tuple[List[MetadataRow], List[str]]:
        """Читает файл ещё раз, извлекая строки и колонки."""
        rows: List[MetadataRow] = []
        extra_cols: set = set()
        done = 0

        with open(self.path, 'rb') as fh:
            for _, elem in ET.iterparse(fh, events=('end',)):
                if elem.tag != self._tag_metadata:
                    continue

                rows.append(self._build_row(elem, markers))
                extra_cols.update(elem.attrib)

                elem.clear()
                done += 1
                if self.on_progress and done % 500 == 0:
                    self.on_progress(done, self._total)

        if self.on_progress:
            self.on_progress(done, self._total)

        columns = BASE_COLUMNS + sorted(
            c for c in extra_cols if c not in BASE_COLUMNS)
        return rows, columns

    @staticmethod
    def _build_row(elem: ET.Element, markers) -> MetadataRow:
        """Строит MetadataRow из XML-элемента."""
        name = elem.get('name', '')
        parsed = XmlParser._split_name(name)
        parsed.update(elem.attrib)

        parsed['ПризнакОбъекта'] = (
            CUSTOM_TAG
            if markers.is_custom_name(parsed.get('ИмяОбъекта', ''))
            else STD_TAG
        )
        return MetadataRow(data=parsed)

    @staticmethod
    def _split_name(name: str) -> Dict[str, str]:
        """Разбирает строку name из XML в набор русских полей."""
        parts = name.split('.') if name else []
        parts += [''] * (6 - len(parts))

        type_ru = TYPE_TRANSLATIONS.get(parts[0], parts[0])
        kind1_ru = KIND_TRANSLATIONS.get(parts[2], parts[2])
        kind2_ru = KIND_TRANSLATIONS.get(parts[4], parts[4])

        path_parts = [type_ru, parts[1], kind1_ru, parts[3], kind2_ru, parts[5]]
        if len(parts) > 6:
            path_parts.extend(parts[6:])
        path = '.'.join(p for p in path_parts if p)

        return {
            'ТипОбъекта': type_ru,
            'ИмяОбъекта': parts[1],
            'ВидЭлемента': kind1_ru,
            'ИмяЭлемента': parts[3],
            'ВидВложенногоЭлемента': kind2_ru,
            'ИмяВложенногоЭлемента': parts[5],
            'ПутьЭлемента': path,
            'ПризнакОбъекта': NONE_TAG,
        }