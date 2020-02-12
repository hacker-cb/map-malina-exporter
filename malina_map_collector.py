import logging
from json import JSONDecodeError

import requests
from prometheus_client import Info
from prometheus_client.metrics_core import (CounterMetricFamily,
                                            GaugeMetricFamily,
                                            InfoMetricFamily)

_logger = logging.getLogger(__name__)


class Malina:
    def __init__(self, name, host, login, password, timeout):
        self.name = name
        self.host = host
        self.login = login
        self.password = password
        self.timeout = timeout


class MapMetricFactory:
    def __init__(self, m: Malina):
        self._labels = ['name', 'hostname']
        self._labels_values = [m.name, m.host]

    def gauge(self, name, value, help):
        c = GaugeMetricFamily(name, help, labels=self._labels)
        c.add_metric(self._labels_values, value)
        return c

    def counter(self, name, value, help):
        c = CounterMetricFamily(name, help, labels=self._labels)
        c.add_metric(self._labels_values, value)
        return c        

class MapMalinaCollector:
    def __init__(self, sources):
        self._sources = sources

    def collect(self):
        for m in self._sources:
                    
            url = 'http://' + m.host + '/read_json.php?device=map'

            if m.login and m.password:
                auth = (m.login, m.password)
            else:
                auth = None

            try:
                r = requests.get(url=url, auth=auth, timeout=m.timeout)            
            except requests.RequestException:
                _logger.error("Connect to MAP error: " + m.host)
                continue
            try:
                j = r.json()
            except JSONDecodeError:
                _logger.error("JSON decode error (possible no MAP connected): " + m.host)
                continue

            _logger.debug('Got response from ' + m.host + ' Firmware: ' + j['fw'])
            i = InfoMetricFamily('map', 'MAP information for.', value={'name': m.name, 'hostname': m.host, 'firmware': j['fw']})
            yield i

            f = MapMetricFactory(m)

            yield f.gauge('map_mode',                                    j['_MODE'],                      'Режим работы МАП')
            yield f.gauge('map_status_charge',                           j['_Status_Char'],               'Cтатус заряда (по протоколу МикроАрт)')
            yield f.gauge('map_battery_voltage',                         j['_Uacc'],                      'Напряжение АКБ, Вольт')
            yield f.gauge('map_battery_charge_end_voltage_with_temp',    j['_Uch_T'],                     'Напряжение окончания заряда АКБ с коррекцией по текущей температуре')
            yield f.gauge('map_battery_charge_buffer_voltage_with_temp', j['_Ubuf_T'],                    'Напряжение окончания заряда АКБ для буферного напряжения АКБ')
            yield f.gauge('map_battery_current_coarse',                  j['_Iacc'],                      'Ток АКБ, А (грубое значение)')
            yield f.gauge('map_battery_current_fine',                    j['_IAcc_med_A_u16'],            'Ток АКБ, А (точное значение, до 0.1)')
            yield f.gauge('map_battery_current_average',                 j['_I_acc_avg'],                 'Cредний ток по АКБ')
            yield f.gauge('map_battery_power',                           j['_PLoad'],                     'Мощность по АКБ, Вт. Из ячейки МАП')
            yield f.gauge('map_battery_power_calculated',                j['_PLoad_calc'],                'Расчетная мощность по АКБ. P(t)=I(t)*U(t). (Знак минус – ток из АКБ. Знак + ток на АКБ (заряд))')
            yield f.gauge('map_battery_power_overload',                  j['_F_Acc_Over'],                'Состояние перегрузки по АКБ (см. Протокол)')
            yield f.gauge('map_network_power_overload',                  j['_F_Net_Over'],                'Состояние перегрузки по сети 220 (см. Протокол)')
            yield f.gauge('map_network_voltage',                         j['_UNET'],                      'Напряжение сети (вход МАП), Вольт')
            yield f.gauge('map_network_current_coarse',                  j['_INET'],                      'Ток по входу МАП, А (грубое значение)')
            yield f.gauge('map_network_current_fine',                    j['_INET_16_4'],                 'Ток по входу МАП, А (точное значение, до 0.1)')
            yield f.counter('map_network_current_direction',             float(j['_E_NET_SIGN'])/100.0,   'Счетчик, учитывающий знак направления тока энергии по входу МАП кВтч')
            yield f.gauge('map_network_power',                           j['_PNET'],                      'Мощность по входу МАП, ВА')
            yield f.gauge('map_network_power_calculated',                j['_PNET_calc'],                 'Мощность по входу МАП, ВА (расчетное значение)')
            yield f.gauge('map_network_frequency',                       j['_TFNET'],                     'Частота сети по входу МАП, Гц')
            yield f.gauge('map_output_frequency',                        j['_ThFMAP'],                    'Частота по выходу МАП, Гц')
            yield f.gauge('map_output_voltage_average',                  j['_UOUTmed'],                   'Усредненное значение напряжения на выходе МАП, Вольт')
            yield f.gauge('map_temperature_external',                    j['_Temp_Grad0'],                'Температура от внешнего датчика температуры (который наклеен на АКБ)')
            yield f.gauge('map_temperature_tor',                         j['_Temp_Grad1'],                'Температура датчика тора (в модели DOMINATOR)')
            yield f.gauge('map_temperature_transistors',                 j['_Temp_Grad2'],                'Температура от датчика температуры транзисторов')
            yield f.counter('map_power_from_network',                    float(j['_E_NET'])/100.0,        'Потребленная энергия от сети кВтч')
            yield f.counter('map_power_from_battery',                    float(j['_E_ACC'])/100.0,        'Потребленная энергия от АКБ на генерацию МАП кВтч')
            yield f.counter('map_power_to_battery',                      float(j['_E_ACC_CHARGE'])/100.0, 'Энергия на заряд АКБ от сети кВтч')
            yield f.gauge('map_cooler_speed',                            j['_CoolerSpeed'],               'Скорость вращения охлаждающего вентилятора')
            yield f.gauge('map__I_acc_3ph',                              j['_I_acc_3ph'],                 'Общий ток потребления/заряда по АКБ для 3-ф системы, А')
            yield f.gauge('map_battery_current_phase1',                  j['_I_ph1'],                     'Ток потребления/заряда по АКБ для 3-ф системы: Фаза 1')
            yield f.gauge('map_battery_current_phase2',                  j['_I_ph2'],                     'Ток потребления/заряда по АКБ для 3-ф системы: Фаза 2')
            yield f.gauge('map_battery_current_phase3',                  j['_I_ph3'],                     'Ток потребления/заряда по АКБ для 3-ф системы: Фаза 3')
            yield f.gauge('map__P_mppt_avg',                             j['_P_mppt_avg'],                'Общая мощность от MPPT контроллеров, Вт')
            yield f.gauge('map__P_acc_3ph',                              j['_P_acc_3ph'],                 'Мощность от АКБ: Все фазы (Знак минус – ток из АКБ. Знак + ток на АКБ (заряд))')
            yield f.gauge('map_battery_power_phase1',                    j['_P_ph1'],                     'Мощность от АКБ: Фаза 1 (Знак минус – ток из АКБ. Знак + ток на АКБ (заряд))')
            yield f.gauge('map_battery_power_phase2',                    j['_P_ph2'],                     'Мощность от АКБ: Фаза 2 (Знак минус – ток из АКБ. Знак + ток на АКБ (заряд))')
            yield f.gauge('map_battery_power_phase3',                    j['_P_ph3'],                     'Мощность от АКБ: Фаза 3 (Знак минус – ток из АКБ. Знак + ток на АКБ (заряд))')
            yield f.counter('map_E_NET_B',                               j['_E_NET_B'],                   'XXXXXXXXXX')
            yield f.counter('map_E_ACC_B',                               j['_E_ACC_B'],                   'XXXXXXXXXX')
            yield f.counter('map_E_ACC_CHARGE_B',                        j['_E_ACC_CHARGE_B'],            'XXXXXXXXXX')
            yield f.counter('map_E_NET_SIGN_B',                          j['_E_NET_SIGN_B'],              'XXXXXXXXX')
            # yield f.gauge('map_XXXXXXXX',                                j['Temp_off'],                   'Наличие датчиков температуры МАП (см. протокол)')
            # yield f.gauge('map_XXXXXXXX',                                j['_TFNET_Limit'],               'XXXXXXXXXX')
            # yield f.gauge('map_XXXXXXXX',                                j['_UNET_Limit'],                'XXXXXXXXXX')
            # yield f.gauge('map_XXXXXXXX',                                j['_RSErrSis'],                  'XXXXXXXXXX')
            # yield f.gauge('map_XXXXXXXX',                                j['_RSErrJobM'],                 'XXXXXXXXXX')
            # yield f.gauge('map_XXXXXXXX',                                j['_RSErrJob'],                  'XXXXXXXXXX')
            # yield f.gauge('map_XXXXXXXX',                                j['_RSWarning'],                 'XXXXXXXXXX')
            # yield f.gauge('map_XXXXXXXX',                                j['_RSErrDop'],                  'XXXXXXXXXX')
            # yield f.gauge('map_XXXXXXXX'                                 j['_Inet_flag'],                 'XXXXXXXXXX')
            # yield f.gauge('map_XXXXXXXX',                                j['_I_mppt_avg'],                'XXXXXXXXXX')
            # yield f.gauge('map_XXXXXXXX',                                j['_I2C_Err'],                   'XXXXXXXXXX')
            # yield f.gauge('map_XXXXXXXX',                                j['_Relay1'],                    'XXXXXXXXXX')
            # yield f.gauge('map_XXXXXXXX',                                j['_Relay2'],                    'XXXXXXXXXX')
            # yield f.gauge('map_XXXXXXXX',                                j['_Flag_ECO'],                  'XXXXXXXXXX')
            # yield f.gauge('map_XXXXXXXX',                                j['_flagUnet2'],                 'XXXXXXXXXX')
            # yield f.gauge('map_XXXXXXXX',                                j['_MPPTs_mode'],                'XXXXXXXXXX')
            # yield f.gauge('map_XXXXXXXX',                                j['_I_MPPT_WIND'],               'XXXXXXXXXX')
            # yield f.gauge('map_XXXXXXXX',                                j['_P_MPPT_WIND'],               'XXXXXXXXXX')
            # yield f.gauge('map_XXXXXXXX',                                j['_fl_UAccChBF_24h'],          'XXXXXXXXXX')
