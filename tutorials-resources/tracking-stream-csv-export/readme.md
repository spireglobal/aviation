# Listen to the Tracking Stream endpoint and generate CSVs

This code sample shows how to listen to Spire Aviation Tracking Stream endpoint, and generate CSVs in 60 minute data buckets.

## Setup

### Install the necessary dependencies

```py
pip install -r requirements.txt
```

### Update your environment configuration

In the `env.yaml` file, update the `AVIATION_TOKEN` variable with your own API token.

### Run the code

```
python main.py
```