name: Local Odds Test

on:
  workflow_dispatch: {}   # run it manually from the Actions tab

jobs:
  run:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

      - name: Run DK events test
        run: |
          if [ -f src/run_local_events_test.py ]; then
            python src/run_local_events_test.py
          elif [ -f run_local_events_test.py ]; then
            python run_local_events_test.py
          else
            echo "❌ Missing run_local_events_test.py (looked in ./ and ./src/)"
            exit 1
          fi
