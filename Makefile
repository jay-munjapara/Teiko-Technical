.PHONY: setup pipeline dashboard

setup:
	python3 -m pip install -r requirements.txt

pipeline:
	python3 load_data.py
	python3 analysis.py

dashboard:
	streamlit run dashboard.py