import logging
from math import fabs

class TowerAlign:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object('gcode')
        self.config = config
        # Загрузка параметров конфигурации
        self.load_config(config)
        # Регистрация команды G-Code
        self.gcode.register_command(
            "TOWER_ALIGN",
            self.cmd_TOWER_ALIGN,
            desc=self.cmd_TOWER_ALIGN_help)
        self.gcode.respond_info("TowerAlign extension initialized")
    cmd_TOWER_ALIGN_help = "Perform XY offset alignment for dual extruder"
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
        toolhead = self.printer.lookup_object('toolhead')
        probe = self.printer.lookup_object('probe', None)
        if probe is None:
            raise gcmd.error("Probe not configured")
        # Измерение башен T0
        t0_x_edge = self.measure_tower(
            toolhead, probe, self.t0_x_tower, True, gcmd)
        t0_y_edge = self.measure_tower(
            toolhead, probe, self.t0_y_tower, False, gcmd)
        # Измерение башен T1
        t1_x_edge = self.measure_tower(
            toolhead, probe, self.t1_x_tower, True, gcmd)
        t1_y_edge = self.measure_tower(
            toolhead, probe, self.t1_y_tower, False, gcmd)
        # Расчет разницы офсетов
        diff_x = t0_x_edge - t1_x_edge
        diff_y = t0_y_edge - t1_y_edge
        # Обновление переменных
        updated = False
        if fabs(diff_x) > self.tolerance:
            self.update_offset(self.var_t1x, diff_x)
            gcmd.respond_info(
                "Updated X offset: %.3f (diff: %.3f)" % (diff_x, diff_x))
            updated = True
        else:
            gcmd.respond_info(
                "X offset within tolerance (%.3f), no update needed" 
                % self.tolerance)
        if fabs(diff_y) > self.tolerance:
            self.update_offset(self.var_t1y, diff_y)
            gcmd.respond_info(
                "Updated Y offset: %.3f (diff: %.3f)" % (diff_y, diff_y))
            updated = True
        else:
            gcmd.respond_info(
                "Y offset within tolerance (%.3f), no update needed" 
                % self.tolerance)
        # Сохранение конфигурации
        if updated:
            self.save_config(gcmd)
        gcmd.respond_info("Tower alignment completed")
    def measure_tower(self, toolhead, probe, position, is_x_axis, gcmd):
        x, y = position
        gcmd.respond_info(
            "Measuring %s tower at (%.2f, %.2f)" 
            % ("X" if is_x_axis else "Y", x, y))
        # Перемещение в начальную позицию
        self.move(toolhead, x, y, self.probe_height, self.travel_speed)
        # Первоначальное касание
        base_z = self.probe_point(probe, x, y, self.probe_speed)
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
            z = self.probe_point(probe, current_pos[0], current_pos[1], 
                                self.probe_speed)
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
            z = self.probe_point(probe, current_pos[0], current_pos[1], 
                                self.probe_speed)
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
    def probe_point(self, probe, x, y, speed):
        toolhead = self.printer.lookup_object('toolhead')
        # Подготовка к измерению
        self.move(toolhead, x, y, self.probe_height, speed)
        # Выполнение измерения
        pos = probe.run_probe()
        # Подъем после измерения
        self.move(toolhead, x, y, self.probe_height, self.lift_speed)
        return pos[2]
    def move(self, toolhead, x, y, z, speed):
        toolhead.manual_move([x, y, z], speed)
    def update_offset(self, var_name, diff):
        # Получение текущего значения
        current_val = self.gcode.get_variable(var_name, default=0.0)
        # Обновление значения
        new_val = float(current_val) + diff
        # Установка новой переменной
        self.gcode.set_variable(var_name, new_val)
    def save_config(self, gcmd):
        configfile = self.printer.lookup_object('configfile')
        gcmd.respond_info("Saving configuration...")
        # Сохранение переменных
        self.gcode.run_script_from_command(
            "SAVE_VARIABLE VARIABLE=%s VALUE=%.6f" 
            % (self.var_t1x, float(self.gcode.get_variable(self.var_t1x))))
        self.gcode.run_script_from_command(
            "SAVE_VARIABLE VARIABLE=%s VALUE=%.6f" 
            % (self.var_t1y, float(self.gcode.get_variable(self.var_t1y))))
        # Сохранение конфига
        configfile.save_config(None)
        gcmd.respond_info("Configuration saved")
def load_config(config):
    return TowerAlign(config)