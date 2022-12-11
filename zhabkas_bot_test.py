from zhabkas_bot import calc_days_to_wait_until_wednesday, calc_day_string


def test_calc_before_wednesday():
    monday = 0
    days_to_wait = calc_days_to_wait_until_wednesday(current_day=monday)
    assert days_to_wait == 2


def test_calc_after_wednesday():
    friday = 4
    days_to_wait = calc_days_to_wait_until_wednesday(current_day=friday)
    assert days_to_wait == 5


def test_calc_on_wednesday():
    wednesday = 2
    days_to_wait = calc_days_to_wait_until_wednesday(current_day=wednesday)
    assert days_to_wait == 0


def test_calc_wait_more_than_one_day():
    days_to_wait = 2
    day_string = calc_day_string(days_to_wait)
    assert day_string == 'days'


def test_calc_wait_one_day():
    days_to_wait = 1
    day_string = calc_day_string(days_to_wait)
    assert day_string == 'day'


def test_calc_wait_zero_days():
    days_to_wait = 0
    day_string = calc_day_string(days_to_wait)
    assert day_string == 'days'
