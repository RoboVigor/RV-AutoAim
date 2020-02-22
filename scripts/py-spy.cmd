activate cv
set PYTHONPATH=%cd%
echo PYTHONPATH=%cd%
py-spy top --subprocesses -- python app/aim_process.py
:: py-spy top --output profile.svg -- python app/aim_process.py --subprocesses
