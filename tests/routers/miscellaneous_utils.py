def round_to_two_decimal_places_with_min(value: float) -> float:
    """
    This function is used to round decimal values
    up to 2 decimal places. However, there are instances
    where rounding to two decimal places still yields 0.00.
    This poses problems when forecasting results. Hence, 
    we'll set the minimum this function can possibly return to
    be 0.01

    ### Args:
    - `value`: A float

    ### Returns:
    A float rounded to 2 decimal places or 0.01 if
    the rounded value is smaller than 0.01.
    """

    rounded_value = round(value, 2)
    return max(rounded_value, 0.01)