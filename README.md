# tower_align
Расширение для Klipper, предназначенное для выполнения автокалибровки офсетов X и Y для двухголовых принтеров (Dual).

## Установка
### Шаг 1. SSH
```bash
cd ~ && git clone https://github.com/Transistor427/tower_align -b dev | cd ~/tower_align && sudo service klipper stop && ln -s ~/tower_align/tower_align.py ~/klipper/klippy/extras/tower_align.py && ln -s ~/tower_align/tower_align.cfg ~/printer_data/config/klipper-config/tower_align.cfg | sudo service klipper start
```
### Шаг 2. Веб-интерфейс
Открываем файл printer.cfg и добавляем в начало строчку:
```
[include klipper-config/tower_align.cfg]
```
Сохраняем изменения нажав кнопку "Сохранить и перезапустить" в верхнем правом углу

## Настройка
- `t0_x_tower_position: 49.5,34.95` - точка начала для оси X T0 (координаты по X и Y)
- `t0_y_tower_position: 34.95,49.5` - точка начала для оси Y T0 (координаты по X и Y)
- `t1_x_tower_position: 49.5,65.05` - точка начала для оси X T1 (координаты по X и Y)
- `t1_y_tower_position: 65.05,49.5`- точка начала для оси Y T1 (координаты по X и Y)
- `coarse_step: 0.5` - грубый шаг измерения 
- `fine_step: 0.1` - точный шаг измерения
- `coarse_backoff: 0.65` - грубый отскок назад
- `lift_distance: 0.6` - подъем 
- `trigger_diff: 0.1` - целевая разница между измерениями
- `tolerance: 0.05` - максимальная разница между измерениями для осей X и Y
- `probe_height: 4` - начальная высота измерения
- `lift_speed: 100` - скорость перемещения
- `probe_speed: 80` - скорость для касания
- `travel_speed: 150` - скорость перемещения
- `variable_t1x: t1_x_offset` - название переменной офсета X в конфигурационном файле (на случай, если изменится)
- `variable_t1y: t1_y_offset` - название переменной офсета Y в конфигурационном файле (на случай, если изменится)

## Подготовка тестового файла
### Шаг 1. Скачиваем STL
Из данного репозитория необходимо скачать 2 тестовых файла `calibrate_autooffset-part1.STL` и `calibrate_autooffset-part2.STL`. Сохраните два этих файла на компьютер.

### Шаг 2. Подготавливаем G-код
Откройте OrcaSlicer, выберите тестируемую модель принтера из списка (например S600 Dual), далее выделите оба тестовых файла и перетяните их из проводника в область слайсера.
<img width="1225" height="268" alt="изображение" src="https://github.com/user-attachments/assets/a7e7b723-6ef7-41e6-9f0a-3862e3a2d89e" />

На предложение загрузить файлы как единую модель соглашаемся.
Далее в разлеле "Профиль процесса" открываем вкладку "Модели", находим в списке `calibrate_autooffset-part2.STL`, нажимаем правой кнопкой мыши на название и в списке находим пункт "Сменить пруток", далее выбираем пруток №2.
<img width="1642" height="1029" alt="изображение" src="https://github.com/user-attachments/assets/177e9c60-55e3-49e4-9983-5487ab740685" />

Далее перемещаем тестовый файл в координаты 50 по оси X и 50 по оси Y. Черновую башню размещаем недалеко от теста
<img width="1758" height="1366" alt="изображение" src="https://github.com/user-attachments/assets/c992bda2-a894-4573-81d4-8ebb55b18f4d" />

Выбираем материалы печати, которыми будет печататься тест.

Настраиваем печать:

Устанавливаем шаблон заполнения верхней поверхности "Прямолинейный":
<img width="1019" height="224" alt="изображение" src="https://github.com/user-attachments/assets/6140f6c3-8067-42c0-83fc-3f56c90bf8a0" />

Устанавливаем параметры "Угол разреженного заполнения" и "Угол сплошного заполнения" в 0:
<img width="1002" height="811" alt="изображение" src="https://github.com/user-attachments/assets/90ccaf66-e608-469b-b3a5-cb44e7629e30" />


Нарезаем файл и сохраняем его на принтер
<img width="1211" height="1371" alt="изображение" src="https://github.com/user-attachments/assets/4e803e28-1bfc-4838-83be-956ef10773da" />

На принтере нажимаем по нему правой кнопкой мыши и в открывшемся контекстном меню выбираем "Редактировать".
Листаем в самый низ и находим строчку с конечным g-кодом "END_PRINT ..."
Комментируем строчку и добавляем перед ней или после нее команду "TOWER_ALIGN". Должно получится примерно как на фото:
<img width="1219" height="406" alt="изображение" src="https://github.com/user-attachments/assets/b8435ca6-f2a3-4849-9484-f6d8a4373c7e" />

## Обновление
```
cd ~/tower_align/ && git reset --hard | git pull && sudo service klipper stop && rm ~/klipper/klippy/extras/tower_align.py && ln -s ~/tower_align/tower_align.py ~/klipper/klippy/extras/tower_align.py && cp ~/tower_align/tower_align.cfg ~/printer_data/config/klipper-config/tower_align.cfg | sudo service klipper start
```




