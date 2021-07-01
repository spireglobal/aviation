# Calculate distance flown during a flight using Tracking History endpoint in Java

This code sample shows how to call the Spire Aviation Tracking History endpoint, extract a single flight and calculate the distance flown during the said flight, as well as the countries flown over.

## Setup

This code sample assumes that you have a Java environment ready (JDK installed, Maven installed).

### Install the Atlas dependency

For this project to work, you will need the [Atlas]() package, which is not available in the Maven repository. For the sake of simplicity, we will install it locally:
```
git clone https://github.com/bkiers/atlas.git
cd altas
mvn clean install
```
