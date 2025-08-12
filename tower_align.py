import logging
import re
import os
from math import fabs

class TowerAlign:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object('gcode')
        self.config = config
        self.probe_result_regex = re.compile(
            r"// Result is z=([\d\.\-]+)")
        self.last_probe_result = None
        # Получаем доступ к модулю сохранения переменных
        self.save_variables = self.printer.lookup_object('save_variables', None)
        if self.save_variables is None:
            raise config.error("save_variables module must be loaded")
        # Получаем путь к файлу переменных
        self.variables_file = self.save_variables.filename
        # Загрузка параметров конфигурации
        self.load_config(config)
        # Регистрация обработчика сообщений
        self.gcode.register_output_handler(self._handle_output)
        # Регистрация команды G-Code
        self.gcode.register_command(
            "TOWER_ALIGN",
            self.cmd_TOWER_ALIGN,
            desc=self.cmd_TOWER_ALIGN_help)
        self.gcode.respond_info("TowerAlign extension initialized")

    cmd_TOWER_ALIGN_help = "Perform XY offset alignment for dual extruder"

    def _handle_output(self, msg):
        # Перехватываем и анализируем вывод команд
        match = self.probe_result_regex.search(msg)
        if match:
            self.last_probe_result = float(match.group(1))

    def load_config(self, config):
        # Параметры башен T0
        t0_x_pos = config.get("t0_x_tower_position").split(',')
        self.t0_x_tower = (float(t0_x_pos[0]), float(t0_x_pos[1]))
        t0_y_pos = config.get("t0_y_tower_position").split(',')
        self.t0_y_tower = (float(t0_y_pos[0]), float(t0_y_pos[1]))
        # Параметры башен T1
        t1_x_pos = config.get("t1_x_tower_position").split(',')
        self.t1_x_tower = (float(t1_x_pos[0]), float(t1_x_pos[1]))
        t1_y_pos = config.get("t1_y_tower_position").split(',')
        self.t1_y_tower = (float(t1_y_pos[0]), float(t1_y_pos[1]))
        # Параметры измерения
        self.coarse_step = config.getfloat("coarse_step", 0.1)
        self.fine_step = config.getfloat("fine_step", 0.05)
        self.coarse_backoff = config.getfloat("coarse_backoff", 0.5)
        self.lift_distance = config.getfloat("lift_distance", 0.4)
        self.trigger_diff = config.getfloat("trigger_diff", 0.2)
        self.tolerance = config.getfloat("tolerance", 0.05)
        self.probe_height = config.getfloat("probe_height", 10.0)
        # Скорости
        self.lift_speed = config.getfloat("lift_speed", 10.0)
        self.probe_speed = config.getfloat("probe_speed", 5.0)
        self.travel_speed = config.getfloat("travel_speed", 100.0)
        # Имена переменных
        self.var_t1x = config.get("variable_t1x", "t1_x_offset")
        self.var_t1y = config.get("variable_t1y", "t1_y_offset")

    def cmd_TOWER_ALIGN(self, gcmd):
        # Охлаждение экструдера перед измерениями
        gcmd.respond_info("Preparing for measurements...")
        gcmd.respond_info("Cooling down extruders to safe temperature")
        self.gcode.run_script_from_command("G1 X0 Y0 F6000")
        self.gcode.run_script_from_command("G1 Z0 F6000")
        # Выключение нагревателей
        self.gcode.run_script_from_command("TURN_OFF_HEATERS")
        self.gcode.run_script_from_command("M106 S255")
        # Ожидание охлаждения экструдеров до 60°C
        self.gcode.run_script_from_command(
            "TEMPERATURE_WAIT SENSOR=extruder MAXIMUM=60")
#        self.gcode.run_script_from_command(
#            "TEMPERATURE_WAIT SENSOR=extruder1 MAXIMUM=60")
        gcmd.respond_info("Extruders cooled down to 60°C, starting alignment")
        self.gcode.run_script_from_command("M106 S0")
        self.gcode.run_script_from_command("G1 Z10 F3000")
        toolhead = self.printer.lookup_object('toolhead')
        # Измерение башен T0
        t0_x_edge = self.measure_tower(
            toolhead, self.t0_x_tower, True, gcmd)
        t0_y_edge = self.measure_tower(
            toolhead, self.t0_y_tower, False, gcmd)
        # Измерение башен T1
        t1_x_edge = self.measure_tower(
            toolhead, self.t1_x_tower, True, gcmd)
        t1_y_edge = self.measure_tower(
            toolhead, self.t1_y_tower, False, gcmd)
        # Расчет разницы офсетов
        diff_x = t0_x_edge - t1_x_edge
        diff_y = t0_y_edge - t1_y_edge
        # Обновление переменных
        updated = False
        new_x_offset = None
        new_y_offset = None
        # Получаем текущие значения переменных
        current_x = self.get_variable(self.var_t1x, default=0.0)
        current_y = self.get_variable(self.var_t1y, default=0.0)
        if fabs(diff_x) > self.tolerance:
            new_x_offset = current_x + diff_x
            self.set_variable(self.var_t1x, new_x_offset)
            gcmd.respond_info(
                "Updated X offset: %.3f (diff: %.3f)" % (new_x_offset, diff_x))
            updated = True
        else:
            gcmd.respond_info(
                "X offset within tolerance (%.3f), no update needed. Current value: %.3f"
                % (self.tolerance, current_x))
        if fabs(diff_y) > self.tolerance:
            new_y_offset = current_y + diff_y
            self.set_variable(self.var_t1y, new_y_offset)
            gcmd.respond_info(
                "Updated Y offset: %.3f (diff: %.3f)" % (new_y_offset, diff_y))
            updated = True
        else:
            gcmd.respond_info(
                "Y offset within tolerance (%.3f), no update needed. Current value: %.3f"
                % (self.tolerance, current_y))
        # Сохранение конфигурации
        if updated:
            self.save_config(gcmd)
        # Итоговый отчет
        gcmd.respond_info("="*40)
        gcmd.respond_info("TOWER ALIGNMENT COMPLETED")
        if new_x_offset is not None:
            gcmd.respond_info("New X offset: %.3f mm" % new_x_offset)
        else:
            gcmd.respond_info("X offset: %.3f mm (no change)" % current_x)
        if new_y_offset is not None:
            gcmd.respond_info("New Y offset: %.3f mm" % new_y_offset)
        else:
            gcmd.respond_info("Y offset: %.3f mm (no change)" % current_y)
        gcmd.respond_info("="*40)

    def measure_tower(self, toolhead, position, is_x_axis, gcmd):
        x, y = position
        gcmd.respond_info(
            "Measuring %s tower at (%.2f, %.2f)"
            % ("X" if is_x_axis else "Y", x, y))
        # Перемещение в начальную позицию
        self.move(toolhead, x, y, self.probe_height, self.travel_speed)
        # Первоначальное касание
        base_z = self.probe_point(toolhead, x, y, gcmd)
        gcmd.respond_info("Base Z: %.3f" % base_z)
        # Грубое сканирование
        edge_found = False
        current_pos = [x, y, self.probe_height]
        step = self.coarse_step
        while not edge_found:
            # Смещение по оси
            if is_x_axis:
                current_pos[0] += self.coarse_step
            else:
                current_pos[1] += self.coarse_step
            self.move(toolhead, *current_pos, self.probe_speed)
            z = self.probe_point(toolhead, current_pos[0], current_pos[1], gcmd)
            if fabs(z - base_z) >= self.trigger_diff:
                edge_found = True
                gcmd.respond_info(
                    "Edge detected at %s=%.3f (Z diff: %.3f)"
                    % ("X" if is_x_axis else "Y",
                       current_pos[0] if is_x_axis else current_pos[1],
                       fabs(z - base_z)))
        # Откат для точного сканирования
        if is_x_axis:
            current_pos[0] -= self.coarse_backoff
        else:
            current_pos[1] -= self.coarse_backoff
        self.move(toolhead, *current_pos, self.probe_speed)
        # Точное сканирование
        edge_pos = None
        step = self.fine_step
        while True:
            # Смещение по оси
            if is_x_axis:
                current_pos[0] += self.fine_step
            else:
                current_pos[1] += self.fine_step
            self.move(toolhead, *current_pos, self.probe_speed)
            z = self.probe_point(toolhead, current_pos[0], current_pos[1], gcmd)
            if fabs(z - base_z) >= self.trigger_diff:
                edge_pos = current_pos[0] if is_x_axis else current_pos[1]
                gcmd.respond_info(
                    "Precise edge at %s=%.3f"
                    % ("X" if is_x_axis else "Y", edge_pos))
                break
        # Подъем и возврат позиции края
        self.move(toolhead, current_pos[0], current_pos[1],
                 self.probe_height, self.lift_speed)
        return edge_pos

    def probe_point(self, toolhead, x, y, gcmd):
        # Сброс предыдущего результата
        self.last_probe_result = None
        # Перемещение в точку измерения
        self.move(toolhead, x, y, self.probe_height, self.probe_speed)
        # Выполнение команды PROBE
        self.gcode.run_script_from_command("PROBE")
        # Ожидание результата
        if self.last_probe_result is None:
            # Повторная попытка при необходимости
            self.gcode.run_script_from_command("PROBE")
            if self.last_probe_result is None:
                raise gcmd.error("Probe measurement failed")
        z_value = self.last_probe_result
        # Подъем после измерения
        self.move(toolhead, x, y, self.probe_height, self.lift_speed)
        return z_value

    def move(self, toolhead, x, y, z, speed):
        toolhead.manual_move([x, y, z], speed)

    def get_variable(self, name, default=0.0):
        """Получить значение переменной из файла конфигурации"""
        # Проверяем существование файла
        if not os.path.exists(self.variables_file):
            return default
        # Читаем файл
        with open(self.variables_file, 'r') as f:
            content = f.read()
        # Ищем переменную
        pattern = r"^\s*{}\s*=\s*([\d\.\-]+)".format(name)
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return default
        return default

    def set_variable(self, name, value):
        """Установить значение переменной через команду"""
        # Используем команду SET_VARIABLE
        self.gcode.run_script_from_command(
            "SAVE_VARIABLE VARIABLE={} VALUE={:.6f}".format(name, value))

    def save_config(self, gcmd):
        gcmd.respond_info("Saving configuration...")
        # Сохраняем переменные через команду SAVE_VARIABLE
        self.gcode.run_script_from_command(
            "SAVE_VARIABLE VARIABLE={} VALUE={:.6f}".format(
                self.var_t1x, self.get_variable(self.var_t1x)))
        self.gcode.run_script_from_command(
            "SAVE_VARIABLE VARIABLE={} VALUE={:.6f}".format(
                self.var_t1y, self.get_variable(self.var_t1y)))
        # Сохраняем конфиг
        #self.gcode.run_script_from_command("SAVE_CONFIG")
        self.gcode.run_script_from_command("M118 Configuration saved")
        #gcmd.respond_info("Configuration saved")

def load_config(config):
    return TowerAlign(config)