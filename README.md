# tower_align
Расширение для Klipper, предназначенное для выполнения автокалибровки офсетов X и Y для двухголовых принтеров (Dual).

## Установка
### Шаг 1. SSH
```bash
cd ~ && git clone https://github.com/Transistor427/tower_aling -b dev | cd ~/tower_aling && sudo service klipper stop && ln -s ~/tower_aling/tower_aling.py ~/klipper/klippy/extras && ln -s ~/tower_aling/tower_aling.cfg ~/printer_dara/config/klipper-config | sudo service klipper start
```
### Шаг 2. Веб-интерфейс
Открываем файл printer.cfg и добавляем в начало строчку:
```
[include klipper-config/tower_aling.cfg]
```
Сохраняем изменения нажав кнопку "Сохранить и перезапустить" в верхнем правом углу

## Настройка
`t0_x_tower_position: 49.5,34.95` - точка начала для оси X T0 (координаты по X и Y)
`t0_y_tower_position: 34.95,49.5` - точка начала для оси Y T0 (координаты по X и Y)
`t1_x_tower_position: 49.5,65.05` - точка начала для оси X T1 (координаты по X и Y)
`t1_y_tower_position: 65.05,49.5`- точка начала для оси Y T1 (координаты по X и Y)
`coarse_step: 0.5` - грубый шаг измерения 
`fine_step: 0.1` - точный шаг измерения
`coarse_backoff: 0.65` - грубый отскок назад
`lift_distance: 0.6` - подъем 
`trigger_diff: 0.1` - целевая разница между измерениями
`tolerance: 0.05` - максимальная разница между измерениями для осей X и Y
`probe_height: 4` - начальная высота измерения
`lift_speed: 100` - скорость перемещения
`probe_speed: 80` - скорость для касания
`travel_speed: 150` - скорость перемещения
`variable_t1x: t1_x_offset` - название переменной офсета X в конфигурационном файле (на случай, если изменится)
`variable_t1y: t1_y_offset` - название переменной офсета Y в конфигурационном файле (на случай, если изменится)



