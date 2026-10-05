.PHONY: install notebooks run clean

install:
	pip install -r requirements.txt

run:
	jupyter lab notebooks/

clean:
	rm -f notebooks/*.ipynb
