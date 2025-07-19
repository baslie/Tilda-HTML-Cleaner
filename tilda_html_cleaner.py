import os
import re
import glob
from pathlib import Path

def clean_html(content):
    """
    Очищает HTML контент согласно заданным правилам
    """
    # Основные правила замены
    rules = [
        # 1. Удаляем data-* атрибуты
        (r'\s*data-[^=\s]*(?:="[^"]*")?(?:=\'[^\']*\')?', ''),
        
        # 2. Удаляем <style> блоки
        (r'<style\b[^>]*>[\s\S]*?</style>', ''),
        
        # 3. Удаляем <script> блоки
        (r'<script\b[^>]*>[\s\S]*?</script>', ''),
        
        # 4. Удаляем style атрибуты
        (r'\s*style\s*=\s*(?:"[^"]*"|\'[^\']*\')', ''),
        
        # 5. Удаляем bis_skin_checked атрибуты
        (r'\s*bis_skin_checked\s*=\s*(?:"[^"]*"|\'[^\']*\')', ''),
        
        # 6. Удаляем HTML комментарии
        (r'<!--[\s\S]*?-->', ''),
        
        # 7. Удаляем SVG элементы
        (r'<svg(?:\s[^>]*)?>(?:[\s\S]*?</svg>)?', ''),
        
        # 8. Удаляем class атрибуты
        (r'\s*class\s*=\s*(?:"[^"]*"|\'[^\']*\')', ''),
        
        # 9. Удаляем field атрибуты
        (r'\s*field\s*=\s*(?:"[^"]*"|\'[^\']*\')', ''),
    ]
    
    # Правила для итеративной очистки пустых элементов
    empty_elements_rules = [
        # 10. Пустые div элементы
        (r'<div[^>]*>\s*</div>', ''),
        
        # 11. Пустые li элементы
        (r'<li[^>]*>\s*</li>', ''),
        
        # 12. Пустые svg элементы
        (r'<svg[^>]*>\s*</svg>', ''),
        
        # Дополнительные правила для других потенциально пустых элементов
        (r'<span[^>]*>\s*</span>', ''),
        (r'<p[^>]*>\s*</p>', ''),
        (r'<a[^>]*>\s*</a>', ''),
        (r'<h[1-6][^>]*>\s*</h[1-6]>', ''),
        (r'<ul[^>]*>\s*</ul>', ''),
        (r'<ol[^>]*>\s*</ol>', ''),
        (r'<table[^>]*>\s*</table>', ''),
        (r'<tr[^>]*>\s*</tr>', ''),
        (r'<td[^>]*>\s*</td>', ''),
        (r'<th[^>]*>\s*</th>', ''),
    ]
    
    # Применяем основные правила
    for pattern, replacement in rules:
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE | re.MULTILINE)
    
    # Итеративно применяем правила для пустых элементов
    max_iterations = 10  # Защита от бесконечного цикла
    iteration = 0
    
    while iteration < max_iterations:
        old_content = content
        
        # Применяем правила для пустых элементов
        for pattern, replacement in empty_elements_rules:
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE | re.MULTILINE)
        
        # Если контент не изменился, прекращаем итерации
        if content == old_content:
            break
            
        iteration += 1
    
    return content

def detect_encoding(filepath):
    """
    Определяет кодировку файла
    """
    encodings_to_try = ['utf-8', 'cp1251', 'utf-8-sig', 'latin-1']
    
    for encoding in encodings_to_try:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                f.read()
            return encoding
        except UnicodeDecodeError:
            continue
    
    # Если ничего не подошло, используем utf-8 с игнорированием ошибок
    return 'utf-8'

def create_backup_filename(original_path):
    """
    Создает имя файла для резервной копии
    """
    path = Path(original_path)
    # Добавляем "_copy" перед расширением
    new_name = f"{path.stem}_copy{path.suffix}"
    return path.parent / new_name

def process_html_files():
    """
    Обрабатывает все HTML файлы в текущей директории
    """
    # Получаем путь к директории скрипта
    script_dir = Path(__file__).parent
    
    # Ищем все HTML файлы в директории (не рекурсивно)
    # Исключаем файлы с суффиксом "_copy", чтобы не обрабатывать уже обработанные файлы
    all_html_files = list(script_dir.glob('*.html')) + list(script_dir.glob('*.htm'))
    html_files = [f for f in all_html_files if '_copy' not in f.stem]
    
    if not html_files:
        print("HTML файлы не найдены в текущей директории.")
        print("(файлы с суффиксом '_copy' игнорируются)")
        return
    
    processed_count = 0
    
    for html_file in html_files:
        try:
            print(f"Обрабатывается файл: {html_file.name}")
            
            # Создаем имя для очищенного файла
            cleaned_file = create_backup_filename(html_file)
            
            # Определяем кодировку
            encoding = detect_encoding(html_file)
            print(f"  Обнаружена кодировка: {encoding}")
            
            # Читаем файл
            with open(html_file, 'r', encoding=encoding, errors='replace') as f:
                content = f.read()
            
            # Сохраняем оригинальный размер для статистики
            original_size = len(content)
            
            # Очищаем контент
            cleaned_content = clean_html(content)
            
            # Сохраняем очищенный файл с суффиксом "_copy"
            with open(cleaned_file, 'w', encoding='utf-8', errors='replace') as f:
                f.write(cleaned_content)
            
            # Статистика
            new_size = len(cleaned_content)
            reduction = original_size - new_size
            reduction_percent = (reduction / original_size * 100) if original_size > 0 else 0
            
            print(f"  ✓ Создан очищенный файл: {cleaned_file.name}")
            print(f"  ✓ Размер уменьшился на {reduction} символов ({reduction_percent:.1f}%)")
            processed_count += 1
            
        except Exception as e:
            print(f"  ✗ Ошибка при обработке {html_file.name}: {str(e)}")
    
    print(f"\nОбработано файлов: {processed_count} из {len(html_files)}")
    if processed_count > 0:
        print(f"Оригинальные файлы сохранены без изменений.")
        print(f"Очищенные версии сохранены с суффиксом '_copy'.")

if __name__ == "__main__":
    print("Скрипт очистки HTML файлов")
    print("=" * 40)
    
    try:
        process_html_files()
        print("\nОбработка завершена!")
    except KeyboardInterrupt:
        print("\nОбработка прервана пользователем.")
    except Exception as e:
        print(f"\nКритическая ошибка: {str(e)}")
    
    input("\nНажмите Enter для выхода...")
