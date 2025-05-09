========================
Time averaging frequency
========================

The tool relies on `approx_interval` parameter from the CMIP tables to
determine the time frequency to average the data.

`approx_interval` is the interval in days expressed as a floating
point number. The value of this parameter can range from seconds to
decades depending on the table selected matching the required
variable.

In the processing step, this inverval is converted to a pandas
frequency string so that time averaging can be carried out.

  .. code:: python

     >>> from pymorize.std_lib import timeaverage
     >>> timeaverage._frequency_from_approx_interval(31)  # 31 days
     '1MS'
     >>> timeaverage._frequency_from_approx_interval(30)  # 30 days
     '1MS'
     >>> timeaverage._frequency_from_approx_interval(59)  # 31 + 28 days
     '2MS'
     >>> timeaverage._frequency_from_approx_interval(60)  # 31 + 29 days (leap-year)
     '2MS'
     >>> timeaverage._frequency_from_approx_interval(90)  # 31 + 28 + 31 days
     '3MS'
     >>> timeaverage._frequency_from_approx_interval(91)  # 31 + 29 + 31 days
     '3MS1D'
     >>> timeaverage._frequency_from_approx_interval(120) # 31 + 28 + 31 + 30
     '4MS'
     >>> timeaverage._frequency_from_approx_interval(151) # 32 + 28 + 31 + 30 + 31
     '5MS'


`approx_interval` is a bit loosely defined in the sence it has no
notion of leap or non-leap year. In the tables, monthly frequencies
for a single month is found (i.e., 30 days) and not multiple months.
If the notion of 30 days per month is considered, then it imples 360
days per year calendar is considered but in the tables 365 days is
used to indicate the yearly frequency and 3560 days is used to
indicate the decadal frequency.
